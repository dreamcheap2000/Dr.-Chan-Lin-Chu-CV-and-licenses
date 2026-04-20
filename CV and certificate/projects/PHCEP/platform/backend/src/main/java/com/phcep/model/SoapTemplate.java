package com.phcep.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * A named SOAP-note snippet template saved by a clinician.
 *
 * <p>Template names follow the convention {@code "label: description"}.
 * The UI inserts only the part <em>before</em> the first colon as the note
 * text, using the full string only as an informational label in the ghost
 * autocomplete window.
 *
 * <p>Templates are scoped to a {@code category} so the ghost autocomplete
 * window shows only templates relevant to the current SOAP note's category.
 */
@Entity
@Table(name = "soap_template")
@Data
@NoArgsConstructor
public class SoapTemplate {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /**
     * Template name, e.g. {@code "急性腦中風: 標準處置流程"}.
     * The UI inserts only the part before ":" into the SOAP section.
     */
    @Column(nullable = false, length = 255)
    private String name;

    /**
     * Clinical category, e.g. {@code "腦血管科 Cerebrovascular"}.
     * Ghost autocomplete shows only templates whose category matches the
     * active SOAP note's selected category.
     */
    @Column(nullable = false, length = 100)
    private String category;

    /** Full template body inserted into the SOAP section on selection. */
    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(nullable = false, updatable = false,
            columnDefinition = "TIMESTAMPTZ DEFAULT now()")
    private OffsetDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
        }
    }
}
