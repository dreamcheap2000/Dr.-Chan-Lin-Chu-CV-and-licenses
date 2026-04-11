package com.phcep.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.phcep.model.AiAuditLog;
import com.phcep.model.MedicalQuery;
import com.phcep.repository.AiAuditLogRepository;
import com.phcep.repository.MedicalQueryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Orchestrates the full query lifecycle:
 * 1. Persist incoming query
 * 2. Request FastSR encoding + retrieval (top-K ranked matches)
 * 3. If confidence threshold met → return AI answer + log to audit trail
 * 4. Else → notify HCP queue + LINE push + log escalation to audit trail
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class QueryService {

    private final MedicalQueryRepository queryRepository;
    private final AiAuditLogRepository auditLogRepository;
    private final FastSRService fastSRService;
    private final LineNotificationService lineNotificationService;
    private final ObjectMapper objectMapper;

    private static final double CONFIDENCE_THRESHOLD = 0.75;
    private static final int DEFAULT_TOP_K = 3;

    @Transactional
    public MedicalQuery submitQuery(String pseudonymousToken, String queryText, String icd10Code) {
        return submitQuery(pseudonymousToken, queryText, icd10Code, DEFAULT_TOP_K);
    }

    @Transactional
    public MedicalQuery submitQuery(String pseudonymousToken, String queryText,
                                    String icd10Code, int topK) {
        MedicalQuery query = new MedicalQuery();
        query.setPseudonymousToken(pseudonymousToken);
        query.setQueryText(queryText);
        query.setIcd10Code(icd10Code);
        query.setStatus(MedicalQuery.QueryStatus.PENDING);
        MedicalQuery saved = queryRepository.save(query);
        processQueryAsync(saved.getId(), topK);
        return saved;
    }

    @Async
    public void processQueryAsync(UUID queryId, int topK) {
        MedicalQuery query = queryRepository.findById(queryId)
                .orElseThrow(() -> new IllegalArgumentException("Query not found: " + queryId));
        try {
            FastSRService.QueryResult result = fastSRService.query(
                    query.getPseudonymousToken(), query.getQueryText(), topK);

            // Persist top-K ranked matches and confidence
            query.setConfidence(result.confidence());
            query.setTopKMatchesJson(toJson(result.matches()));

            if (!result.escalated() && result.confidence() >= CONFIDENCE_THRESHOLD) {
                query.setAiAnswer(result.answer());
                query.setCitations(result.citations());
                query.setStatus(MedicalQuery.QueryStatus.AI_ANSWERED);
                query.setAnsweredAt(LocalDateTime.now());
                log.info("Query {} answered by FastSR (confidence={})", queryId, result.confidence());

                writeAuditLog(query, AiAuditLog.MessageType.AI_ANSWER,
                        result.answer(), result.confidence(), query.getTopKMatchesJson());
            } else {
                query.setStatus(MedicalQuery.QueryStatus.HCP_NOTIFIED);
                lineNotificationService.notifyHcpNewQuery(query);
                log.info("Query {} forwarded to HCP queue (confidence={})", queryId, result.confidence());

                writeAuditLog(query, AiAuditLog.MessageType.HCP_ESCALATION,
                        "Query escalated to HCP — confidence below threshold ("
                                + String.format("%.2f", result.confidence()) + ")",
                        result.confidence(), query.getTopKMatchesJson());
            }
            queryRepository.save(query);
        } catch (Exception e) {
            log.error("Error processing query {}: {}", queryId, e.getMessage(), e);
            query.setStatus(MedicalQuery.QueryStatus.HCP_NOTIFIED);
            queryRepository.save(query);
        }
    }

    public void submitQueryFromLine(String lineUserId, String messageText) {
        String token = "LINE_" + UUID.nameUUIDFromBytes(lineUserId.getBytes()).toString();
        submitQuery(token, messageText, null);
    }

    public Optional<MedicalQuery> findByIdForUser(UUID id, String pseudonymousToken) {
        return queryRepository.findById(id)
                .filter(q -> q.getPseudonymousToken().equals(pseudonymousToken));
    }

    public List<MedicalQuery> listQueriesForUser(String pseudonymousToken) {
        return queryRepository.findByPseudonymousTokenOrderByCreatedAtDesc(pseudonymousToken);
    }

    public List<MedicalQuery> listPendingForHcp() {
        return queryRepository.findByStatusIn(List.of(
                MedicalQuery.QueryStatus.PENDING,
                MedicalQuery.QueryStatus.HCP_NOTIFIED));
    }

    @Transactional
    public MedicalQuery hcpAnswer(UUID queryId, String answer, String citations) {
        MedicalQuery query = queryRepository.findById(queryId)
                .orElseThrow(() -> new IllegalArgumentException("Query not found: " + queryId));
        query.setHcpAnswer(answer);
        query.setCitations(citations);
        query.setStatus(MedicalQuery.QueryStatus.HCP_ANSWERED);
        query.setAnsweredAt(LocalDateTime.now());
        MedicalQuery saved = queryRepository.save(query);
        lineNotificationService.notifyPatientAnswered(saved);

        writeAuditLog(saved, AiAuditLog.MessageType.HCP_ANSWER_RELAY,
                answer, saved.getConfidence(), saved.getTopKMatchesJson());
        return saved;
    }

    // ─── Private helpers ──────────────────────────────────────────────────────

    private void writeAuditLog(MedicalQuery query, AiAuditLog.MessageType type,
                                String content, Double confidence, String matchesJson) {
        try {
            AiAuditLog entry = AiAuditLog.builder()
                    .queryId(query.getId())
                    .recipientToken(query.getPseudonymousToken())
                    .messageType(type)
                    .messageContent(content)
                    .confidence(confidence)
                    .topKMatchesJson(matchesJson)
                    .queryText(query.getQueryText())
                    .build();
            auditLogRepository.save(entry);
        } catch (Exception e) {
            log.warn("Failed to write audit log for query {}: {}", query.getId(), e.getMessage());
        }
    }

    private String toJson(Object obj) {
        if (obj == null) return null;
        try {
            return objectMapper.writeValueAsString(obj);
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialise object to JSON: {}", e.getMessage());
            return null;
        }
    }
}
