package com.phcep.service;

import com.phcep.model.AbbreviationMaster;
import com.phcep.model.ClinicalEntry;
import com.phcep.repository.AbbreviationMasterRepository;
import com.phcep.repository.ClinicalEntryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * Business logic for Workflow A — Smart Data-Intake Pipeline.
 *
 * <p>On entry creation:
 * <ol>
 *   <li>Persist the entry.</li>
 *   <li>Trigger async FastSR embedding via {@link IntakeEmbedService}.</li>
 *   <li>Trigger async Gemini classification via {@link GeminiClassificationService}.</li>
 * </ol>
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ClinicalEntryService {

    private final ClinicalEntryRepository clinicalEntryRepository;
    private final AbbreviationMasterRepository abbreviationMasterRepository;
    private final GeminiClassificationService geminiService;
    private final IntakeEmbedService intakeEmbedService;

    // ─── CRUD ─────────────────────────────────────────────────────────────────

    @Transactional
    public ClinicalEntry create(ClinicalEntry entry) {
        ClinicalEntry saved = clinicalEntryRepository.save(entry);
        // Kick off async FastSR embedding + Gemini classification (non-blocking)
        intakeEmbedService.embedAsync(saved);
        geminiService.classifyAsync(saved);
        return saved;
    }

    public Optional<ClinicalEntry> findById(UUID id) {
        return clinicalEntryRepository.findById(id);
    }

    @Transactional
    public ClinicalEntry update(UUID id, ClinicalEntry patch) {
        ClinicalEntry existing = clinicalEntryRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("ClinicalEntry not found: " + id));
        // Selective field update (null = no-change)
        if (patch.getEntryType() != null) existing.setEntryType(patch.getEntryType());
        if (patch.getIcd10Code() != null) existing.setIcd10Code(patch.getIcd10Code());
        if (patch.getRawText() != null) existing.setRawText(patch.getRawText());
        if (patch.getEbmStatement() != null) existing.setEbmStatement(patch.getEbmStatement());
        if (patch.getSourceUrl() != null) existing.setSourceUrl(patch.getSourceUrl());
        if (patch.getSourceName() != null) existing.setSourceName(patch.getSourceName());
        if (patch.getExamDate() != null) existing.setExamDate(patch.getExamDate());
        if (patch.getEbmExtractionDate() != null) existing.setEbmExtractionDate(patch.getEbmExtractionDate());
        if (patch.getTags() != null) existing.setTags(patch.getTags());
        return clinicalEntryRepository.save(existing);
    }

    @Transactional
    public void delete(UUID id) {
        clinicalEntryRepository.deleteById(id);
    }

    // ─── Query / filter ───────────────────────────────────────────────────────

    public Page<ClinicalEntry> filter(
            String token,
            ClinicalEntry.EntryType type,
            String icd10,
            String category,
            LocalDate from,
            LocalDate to,
            Pageable pageable) {
        return clinicalEntryRepository.filterByUser(token, type, icd10, category, from, to, pageable);
    }

    /** All entries for a user — used by the ML query engine. */
    public List<ClinicalEntry> listForUser(String token) {
        return clinicalEntryRepository.findByPseudonymousUserTokenOrderByInputTimestampDesc(token);
    }

    // ─── Abbreviation glossary ────────────────────────────────────────────────

    /** Returns the full merged abbreviation master list ordered by frequency. */
    public List<AbbreviationMaster> listAbbreviations() {
        return abbreviationMasterRepository.findAllByOrderByOccurrenceCountDesc();
    }

    public List<AbbreviationMaster> searchAbbreviations(String q) {
        return abbreviationMasterRepository.search(q, 50);
    }

    // ─── Daily summary ────────────────────────────────────────────────────────

    /**
     * Returns a daily digest: { category → count } plus total EBM entry count.
     * Shown on the HCP dashboard without invoking the ML engine.
     */
    public Map<String, Object> dailySummary(LocalDate date) {
        java.sql.Date sqlDate = java.sql.Date.valueOf(date);
        List<Object[]> rows = clinicalEntryRepository.dailySummaryByCategory(sqlDate);

        Map<String, Long> byCategory = new LinkedHashMap<>();
        for (Object[] row : rows) {
            String cat = (String) row[0];
            long cnt = ((Number) row[1]).longValue();
            byCategory.put(cat, cnt);
        }

        long totalEbm = clinicalEntryRepository.countEbmByDate(sqlDate);

        return Map.of(
                "date", date.toString(),
                "byCategory", byCategory,
                "totalEbm", totalEbm
        );
    }

    // ─── Google Sheets upsert ─────────────────────────────────────────────────

    @Transactional
    public ClinicalEntry upsertFromSheet(ClinicalEntry entry) {
        if (entry.getGsheetRowId() != null) {
            Optional<ClinicalEntry> existing = clinicalEntryRepository.findByGsheetRowId(entry.getGsheetRowId());
            if (existing.isPresent()) {
                ClinicalEntry e = existing.get();
                e.setRawText(entry.getRawText());
                e.setIcd10Code(entry.getIcd10Code());
                e.setEntryType(entry.getEntryType());
                e.setSourceUrl(entry.getSourceUrl());
                e.setExamDate(entry.getExamDate());
                return clinicalEntryRepository.save(e);
            }
        }
        return create(entry);
    }
}
