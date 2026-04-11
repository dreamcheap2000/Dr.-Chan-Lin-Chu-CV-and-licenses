package com.phcep.service;

import com.phcep.model.MedicalQuery;
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
 * 2. Request FastSR encoding + retrieval
 * 3. If confidence threshold met → return AI answer
 * 4. Else → notify HCP queue + LINE push
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class QueryService {

    private final MedicalQueryRepository queryRepository;
    private final FastSRService fastSRService;
    private final LineNotificationService lineNotificationService;

    private static final double CONFIDENCE_THRESHOLD = 0.75;

    @Transactional
    public MedicalQuery submitQuery(String pseudonymousToken, String queryText, String icd10Code) {
        MedicalQuery query = new MedicalQuery();
        query.setPseudonymousToken(pseudonymousToken);
        query.setQueryText(queryText);
        query.setIcd10Code(icd10Code);
        query.setStatus(MedicalQuery.QueryStatus.PENDING);
        MedicalQuery saved = queryRepository.save(query);
        processQueryAsync(saved.getId());
        return saved;
    }

    @Async
    public void processQueryAsync(UUID queryId) {
        MedicalQuery query = queryRepository.findById(queryId)
                .orElseThrow(() -> new IllegalArgumentException("Query not found: " + queryId));
        try {
            FastSRService.QueryResult result = fastSRService.query(
                    query.getPseudonymousToken(), query.getQueryText());

            if (result.confidence() >= CONFIDENCE_THRESHOLD) {
                query.setAiAnswer(result.answer());
                query.setCitations(result.citations());
                query.setStatus(MedicalQuery.QueryStatus.AI_ANSWERED);
                query.setAnsweredAt(LocalDateTime.now());
                log.info("Query {} answered by FastSR (confidence={})", queryId, result.confidence());
            } else {
                query.setStatus(MedicalQuery.QueryStatus.HCP_NOTIFIED);
                lineNotificationService.notifyHcpNewQuery(query);
                log.info("Query {} forwarded to HCP queue", queryId);
            }
            queryRepository.save(query);
        } catch (Exception e) {
            log.error("Error processing query {}: {}", queryId, e.getMessage(), e);
            query.setStatus(MedicalQuery.QueryStatus.HCP_NOTIFIED);
            queryRepository.save(query);
        }
    }

    public void submitQueryFromLine(String lineUserId, String messageText) {
        // Map LINE user ID to pseudonymous token (deterministic hash)
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
        return saved;
    }
}
