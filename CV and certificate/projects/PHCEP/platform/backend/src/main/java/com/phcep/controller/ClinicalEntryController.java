package com.phcep.controller;

import com.phcep.model.AbbreviationMaster;
import com.phcep.model.ClinicalEntry;
import com.phcep.service.ClinicalEntryService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Workflow A — Smart Data-Intake Pipeline REST API.
 *
 * <pre>
 * POST   /api/entries                       — create entry (triggers async embed + classify)
 * GET    /api/entries                       — paginated list (filters: type, icd10, category, date)
 * GET    /api/entries/{id}                  — single entry with full provenance
 * PUT    /api/entries/{id}                  — update mutable fields
 * DELETE /api/entries/{id}                  — delete (admin only)
 * GET    /api/entries/abbreviations         — merged abbreviation glossary
 * GET    /api/entries/abbreviations/search  — search abbreviations
 * GET    /api/entries/summary               — daily digest (no ML call)
 * </pre>
 */
@RestController
@RequestMapping("/api/entries")
@RequiredArgsConstructor
public class ClinicalEntryController {

    private final ClinicalEntryService clinicalEntryService;

    // ─── Create ───────────────────────────────────────────────────────────────

    /**
     * Create a new clinical entry.
     * Triggers async FastSR embedding and Gemini classification.
     */
    @PostMapping
    public ResponseEntity<ClinicalEntry> create(@Valid @RequestBody ClinicalEntry entry) {
        return ResponseEntity.ok(clinicalEntryService.create(entry));
    }

    // ─── Read (paginated + filtered) ──────────────────────────────────────────

    /**
     * Paginated list of entries for the authenticated user's token.
     * All filter parameters are optional.
     */
    @GetMapping
    public ResponseEntity<Page<ClinicalEntry>> list(
            @RequestParam String pseudonymousToken,
            @RequestParam(required = false) ClinicalEntry.EntryType entryType,
            @RequestParam(required = false) String icd10Code,
            @RequestParam(required = false) String geminiCategory,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {

        PageRequest pageable = PageRequest.of(page, Math.min(size, 100),
                Sort.by(Sort.Direction.DESC, "inputTimestamp"));
        Page<ClinicalEntry> result = clinicalEntryService.filter(
                pseudonymousToken, entryType, icd10Code, geminiCategory, from, to, pageable);
        return ResponseEntity.ok(result);
    }

    /** Single entry — includes full provenance. */
    @GetMapping("/{id}")
    public ResponseEntity<ClinicalEntry> get(@PathVariable UUID id) {
        return clinicalEntryService.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    // ─── Update ───────────────────────────────────────────────────────────────

    /** Partial update — only non-null fields in the request body are applied. */
    @PutMapping("/{id}")
    public ResponseEntity<ClinicalEntry> update(
            @PathVariable UUID id,
            @RequestBody ClinicalEntry patch) {
        return ResponseEntity.ok(clinicalEntryService.update(id, patch));
    }

    // ─── Delete ───────────────────────────────────────────────────────────────

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        clinicalEntryService.delete(id);
        return ResponseEntity.noContent().build();
    }

    // ─── Abbreviation Glossary ────────────────────────────────────────────────

    /**
     * Returns the merged abbreviation master list (most frequent first).
     * Usable by the "Abbreviation Glossary" UI without ML calls.
     */
    @GetMapping("/abbreviations")
    public ResponseEntity<List<AbbreviationMaster>> abbreviations() {
        return ResponseEntity.ok(clinicalEntryService.listAbbreviations());
    }

    /** Search abbreviation glossary by free text. */
    @GetMapping("/abbreviations/search")
    public ResponseEntity<List<AbbreviationMaster>> searchAbbreviations(@RequestParam String q) {
        return ResponseEntity.ok(clinicalEntryService.searchAbbreviations(q));
    }

    // ─── Daily Summary (HCP dashboard — no ML call) ───────────────────────────

    /**
     * Returns a daily digest:
     * <ul>
     *   <li>{@code date} — the requested date</li>
     *   <li>{@code byCategory} — { category → count }</li>
     *   <li>{@code totalEbm} — number of EBM entries that day</li>
     *   <li>{@code abbreviations} — all current abbreviation masters</li>
     * </ul>
     */
    @GetMapping("/summary")
    public ResponseEntity<Map<String, Object>> summary(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        LocalDate target = date != null ? date : LocalDate.now();
        return ResponseEntity.ok(clinicalEntryService.dailySummary(target));
    }
}
