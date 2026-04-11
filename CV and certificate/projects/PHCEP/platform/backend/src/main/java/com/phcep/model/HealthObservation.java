package com.phcep.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * A health observation recorded by a patient or device (maps to FHIR Observation).
 * Examples: lab value, vital sign, imaging finding summary, symptom.
 */
@Entity
@Table(name = "health_observations")
@Data
@NoArgsConstructor
public class HealthObservation {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /** De-identified patient reference. */
    @Column(nullable = false)
    private String pseudonymousToken;

    /** LOINC code or ICD-10 code identifying the observation type. */
    @Column(length = 50)
    private String loincCode;

    @Column(length = 50)
    private String icd10Code;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String observationText;

    /** Numeric value (if applicable). */
    private Double numericValue;

    /** Unit of measure. */
    @Column(length = 50)
    private String unit;

    /** Reference range low. */
    private Double referenceRangeLow;

    /** Reference range high. */
    private Double referenceRangeHigh;

    @Enumerated(EnumType.STRING)
    private ObservationType observationType;

    /** Effective date/time (date-shifted for de-identification). */
    private LocalDateTime effectiveDateTime;

    /** FHIR Observation resource JSON (de-identified). */
    @Column(columnDefinition = "TEXT")
    private String fhirObservationJson;

    /** FastSR semantic embedding of observationText. */
    @Column(columnDefinition = "TEXT")
    private String semanticEmbeddingJson;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    public enum ObservationType {
        LAB, VITAL_SIGN, IMAGING_FINDING, SYMPTOM, MEDICATION, PROCEDURE, OTHER
    }
}
