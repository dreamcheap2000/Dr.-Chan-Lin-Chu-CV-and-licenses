package com.phcep.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

/**
 * Deduplicated master abbreviation table.
 * Populated by {@link com.phcep.service.AbbreviationSyncService} which merges
 * all per-entry {@code abbreviation_map} JSONB fields.
 */
@Entity
@Table(name = "abbreviation_master")
@Data
@NoArgsConstructor
public class AbbreviationMaster {

    /** The abbreviation itself (primary key, case-sensitive). */
    @Id
    @Column(length = 50)
    private String abbreviation;

    /** Preferred full expansion. */
    @Column(nullable = false, columnDefinition = "TEXT")
    private String expansion;

    /** ICD-10 code this abbreviation most often appears alongside. */
    @Column(length = 50)
    private String icd10Context;

    /** Number of clinical_entry rows that defined this abbreviation. */
    @Column(nullable = false)
    private int occurrenceCount = 1;

    @Column(nullable = false, columnDefinition = "TIMESTAMPTZ DEFAULT now()")
    private OffsetDateTime lastSeenAt;

    @PrePersist
    @PreUpdate
    protected void onSave() {
        lastSeenAt = OffsetDateTime.now();
    }
}
