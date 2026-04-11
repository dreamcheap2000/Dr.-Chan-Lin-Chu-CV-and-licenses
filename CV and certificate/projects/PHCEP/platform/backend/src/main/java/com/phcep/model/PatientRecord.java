package com.phcep.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * De-identified patient record.
 * Direct PII is replaced by the DeIdentificationService before persistence.
 */
@Entity
@Table(name = "patient_records")
@Data
@NoArgsConstructor
public class PatientRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /** Pseudonymous patient token — never the real name or NHI ID. */
    @Column(nullable = false, unique = true)
    private String pseudonymousToken;

    /** Year of birth (not exact date, to reduce re-identification risk). */
    private Integer birthYear;

    /** Biological sex (M/F/Other). */
    @Column(length = 10)
    private String sex;

    /** FHIR Patient resource JSON (serialised, de-identified). */
    @Column(columnDefinition = "TEXT")
    private String fhirPatientJson;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = createdAt;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
