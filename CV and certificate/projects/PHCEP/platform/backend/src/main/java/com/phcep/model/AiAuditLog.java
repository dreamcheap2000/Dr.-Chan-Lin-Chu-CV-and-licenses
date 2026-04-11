package com.phcep.model;

import jakarta.persistence.*;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Immutable audit record for every AI-generated message sent to a user.
 * Allows platform managers to review what the system communicated on their behalf.
 *
 * Message types:
 *   AI_ANSWER          — AI answered with sufficient confidence
 *   HCP_ESCALATION     — query forwarded to HCP (low confidence)
 *   HCP_ANSWER_RELAY   — HCP answer relayed back to patient
 */
@Entity
@Table(name = "ai_audit_log",
        indexes = {
                @Index(name = "idx_audit_query", columnList = "queryId"),
                @Index(name = "idx_audit_token", columnList = "recipientToken"),
                @Index(name = "idx_audit_sent", columnList = "sentAt"),
        })
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AiAuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /** Foreign key to the originating MedicalQuery. */
    @Column(nullable = false)
    private UUID queryId;

    /** Pseudonymous token identifying the message recipient (patient). */
    @Column(nullable = false)
    private String recipientToken;

    /** Classification of the automated message. */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private MessageType messageType;

    /** Full text of the AI-generated answer or escalation notice shown to the user. */
    @Column(columnDefinition = "TEXT")
    private String messageContent;

    /** ML confidence score at the time the message was generated (0–1). */
    private Double confidence;

    /** JSON snapshot of the top-K ranked matches that drove this message. */
    @Column(columnDefinition = "TEXT")
    private String topKMatchesJson;

    /** Original query text (denormalised for fast admin lookups). */
    @Column(columnDefinition = "TEXT")
    private String queryText;

    /** Timestamp when the message was created and dispatched. */
    @Column(nullable = false, updatable = false)
    private LocalDateTime sentAt;

    @PrePersist
    protected void onCreate() {
        sentAt = LocalDateTime.now();
    }

    public enum MessageType {
        AI_ANSWER,
        HCP_ESCALATION,
        HCP_ANSWER_RELAY,
    }
}
