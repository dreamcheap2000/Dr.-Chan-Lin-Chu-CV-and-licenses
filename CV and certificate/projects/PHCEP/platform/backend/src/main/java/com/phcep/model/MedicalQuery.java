package com.phcep.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * A medical query submitted by a patient or HCP.
 * Linked to a pseudonymous patient token and resolved via FastSR or HCP answer.
 */
@Entity
@Table(name = "medical_queries")
@Data
@NoArgsConstructor
public class MedicalQuery {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /** FK pseudonymousToken from PatientRecord. */
    @Column(nullable = false)
    private String pseudonymousToken;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String queryText;

    /** ICD-10 code hint (optional, provided by user or auto-suggested). */
    @Column(length = 20)
    private String icd10Code;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private QueryStatus status = QueryStatus.PENDING;

    /** FastSR synthesised answer (may be null if awaiting HCP). */
    @Column(columnDefinition = "TEXT")
    private String aiAnswer;

    /** HCP written answer (overrides or supplements AI answer). */
    @Column(columnDefinition = "TEXT")
    private String hcpAnswer;

    /** PMID or article URL citations (comma-separated). */
    @Column(columnDefinition = "TEXT")
    private String citations;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime answeredAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    public enum QueryStatus {
        PENDING, AI_ANSWERED, HCP_NOTIFIED, HCP_ANSWERED, CLOSED
    }
}
