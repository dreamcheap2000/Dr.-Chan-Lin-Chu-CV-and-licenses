package com.phcep.service;

import com.phcep.model.MedicalQuery;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

/**
 * Sends LINE Messaging API push notifications to:
 *  - HCPs: new query requiring review
 *  - Patients: query has been answered
 *
 * Requires a valid LINE channel access token in application.yml.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class LineNotificationService {

    private final WebClient.Builder webClientBuilder;

    @Value("${phcep.line.channel-access-token}")
    private String channelAccessToken;

    private static final String LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push";

    /** Notify HCP group or admin LINE user about a new pending query. */
    @Async
    public void notifyHcpNewQuery(MedicalQuery query) {
        String message = String.format(
                "[PHCEP] New query awaiting HCP review\nID: %s\nQuery: %s",
                query.getId(), truncate(query.getQueryText(), 100));
        // In production: replace with actual HCP LINE user ID or group ID from config
        sendPush("HCP_LINE_USER_ID_PLACEHOLDER", message);
    }

    /** Notify patient via LINE that their query has been answered. */
    @Async
    public void notifyPatientAnswered(MedicalQuery query) {
        String lineUserId = resolvePatientLineId(query.getPseudonymousToken());
        if (lineUserId == null) return;
        String message = String.format(
                "[PHCEP] Your query has been answered.\nQuery: %s\nAnswer: %s",
                truncate(query.getQueryText(), 80),
                truncate(effectiveAnswer(query), 200));
        sendPush(lineUserId, message);
    }

    private void sendPush(String to, String text) {
        try {
            webClientBuilder.build()
                    .post()
                    .uri(LINE_PUSH_URL)
                    .header("Authorization", "Bearer " + channelAccessToken)
                    .bodyValue(Map.of(
                            "to", to,
                            "messages", new Object[]{Map.of("type", "text", "text", text)}
                    ))
                    .retrieve()
                    .toBodilessEntity()
                    .subscribe(
                            resp -> log.info("LINE push sent to {}", to),
                            err -> log.warn("LINE push failed: {}", err.getMessage())
                    );
        } catch (Exception e) {
            log.warn("LINE push error: {}", e.getMessage());
        }
    }

    private String resolvePatientLineId(String pseudonymousToken) {
        // LINE user IDs are stored separately; token starting with LINE_ was derived from LINE ID
        if (pseudonymousToken.startsWith("LINE_")) {
            // Cannot reverse, but in a full implementation the LINE user ID would be looked up
            // from a secure mapping table (not stored in the de-identified record).
            return null;
        }
        return null;
    }

    private String effectiveAnswer(MedicalQuery q) {
        return q.getHcpAnswer() != null ? q.getHcpAnswer() : q.getAiAnswer();
    }

    private String truncate(String s, int max) {
        if (s == null) return "";
        return s.length() <= max ? s : s.substring(0, max) + "...";
    }
}
