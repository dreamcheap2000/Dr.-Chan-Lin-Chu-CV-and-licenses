package com.phcep.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

/**
 * Workflow A — Smart Data-Intake Pipeline entry.
 *
 * Each row represents one piece of clinical information entered by a doctor,
 * optionally imported from Google Sheets, and enriched nightly by Gemini.
 */
@Entity
@Table(name = "clinical_entry")
@Data
@NoArgsConstructor
public class ClinicalEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /** De-identified user reference (via DeIdentificationService). */
    @Column(nullable = false)
    private String pseudonymousUserToken;

    /** Entry category. */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private EntryType entryType;

    /** ICD-10 code (nullable). */
    @Column(length = 10)
    private String icd10Code;

    /** Free-form clinical note / snippet — may contain abbreviations. */
    @Column(nullable = false, columnDefinition = "TEXT")
    private String rawText;

    /** Extracted EBM statement — filled inline by user or by Gemini. */
    @Column(columnDefinition = "TEXT")
    private String ebmStatement;

    /** Source URL (PubMed / guideline). */
    @Column(columnDefinition = "TEXT")
    private String sourceUrl;

    /** Journal or database name. */
    @Column(length = 255)
    private String sourceName;

    /** Date of the clinical exam / procedure. */
    private LocalDate examDate;

    /** Date EBM text was extracted from the source. */
    private LocalDate ebmExtractionDate;

    /** Server-side creation timestamp (immutable). */
    @Column(nullable = false, updatable = false,
            columnDefinition = "TIMESTAMPTZ DEFAULT now()")
    private OffsetDateTime inputTimestamp;

    /** Gemini-inferred clinical category (e.g. "Neurology / Stroke"). */
    @Column(length = 100)
    private String geminiCategory;

    /** Gemini classification confidence (0–1). */
    private Double geminiConfidence;

    /**
     * Per-entry abbreviation map {"abbr": "expansion", …}.
     * Stored as JSONB; populated by GeminiClassificationService.
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "JSONB")
    private String abbreviationMap;

    /** FastSR semantic embedding JSON (filled async after creation). */
    @Column(columnDefinition = "TEXT")
    private String semanticEmbeddingJson;

    /** User-applied tags (stored as PostgreSQL text array). */
    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(columnDefinition = "TEXT[]")
    private List<String> tags;

    /** Idempotency key for Google Sheets row upsert. */
    @Column(length = 100, unique = true)
    private String gsheetRowId;

    @PrePersist
    protected void onCreate() {
        if (inputTimestamp == null) {
            inputTimestamp = OffsetDateTime.now();
        }
    }

    public enum EntryType {
        ICD10, SYMPTOM, EBM, LAB, IMAGING, NOTE
    }
}
