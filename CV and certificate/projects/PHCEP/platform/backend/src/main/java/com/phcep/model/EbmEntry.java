package com.phcep.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * An Evidence-Based Medicine entry: a clinical statement with provenance.
 */
@Entity
@Table(name = "ebm_entries")
@Data
@NoArgsConstructor
public class EbmEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /** Free-text EBM clinical statement. */
    @Column(nullable = false, columnDefinition = "TEXT")
    private String statement;

    /** PubMed ID (numeric string), if available. */
    @Column(length = 20)
    private String pmid;

    /** Full article URL. */
    @Column(length = 1000)
    private String articleUrl;

    /** ICD-10 code(s) this statement relates to. */
    @Column(length = 50)
    private String icd10Codes;

    /** Medical speciality tag (e.g. Neurology, Cardiology). */
    @Column(length = 100)
    private String specialty;

    /** FastSR semantic embedding vector (JSON array, stored for retrieval). */
    @Column(columnDefinition = "TEXT")
    private String semanticEmbeddingJson;

    /** FastSR global-context embedding vector (JSON array). */
    @Column(columnDefinition = "TEXT")
    private String globalEmbeddingJson;

    /** FastSR fragment-attention embedding vector (JSON array). */
    @Column(columnDefinition = "TEXT")
    private String fragmentEmbeddingJson;

    /** HCP who entered or approved this entry. */
    private String enteredByHcp;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    private LocalDate publicationDate;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
