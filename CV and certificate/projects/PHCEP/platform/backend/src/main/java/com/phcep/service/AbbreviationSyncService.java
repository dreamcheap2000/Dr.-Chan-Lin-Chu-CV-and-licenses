package com.phcep.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.phcep.model.AbbreviationMaster;
import com.phcep.model.ClinicalEntry;
import com.phcep.repository.AbbreviationMasterRepository;
import com.phcep.repository.ClinicalEntryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;

/**
 * Merges per-entry {@code abbreviation_map} JSONB objects into the
 * deduplicated {@code abbreviation_master} table.
 *
 * <p>Runs nightly at 02:30, after {@link GeminiClassificationService} has
 * populated abbreviation maps (which runs at 02:00).
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AbbreviationSyncService {

    private final ClinicalEntryRepository clinicalEntryRepository;
    private final AbbreviationMasterRepository abbreviationMasterRepository;
    private final ObjectMapper objectMapper;

    /**
     * Nightly sync: merge all abbreviation maps from clinical_entry into
     * abbreviation_master, incrementing occurrence counts on conflicts.
     */
    @Scheduled(cron = "0 30 2 * * *")
    @Transactional
    public void syncAllAbbreviations() {
        log.info("AbbreviationSyncService: starting nightly merge…");
        List<ClinicalEntry> entries = clinicalEntryRepository.findWithAbbreviationMap();
        int merged = 0;
        for (ClinicalEntry entry : entries) {
            merged += mergeEntry(entry);
        }
        log.info("AbbreviationSyncService: merged {} abbreviation records.", merged);
    }

    /**
     * Merge a single entry's abbreviation map immediately (called after
     * inline Gemini classification of a new entry).
     */
    @Transactional
    public void syncEntry(ClinicalEntry entry) {
        mergeEntry(entry);
    }

    // ─── Private helpers ──────────────────────────────────────────────────────

    private int mergeEntry(ClinicalEntry entry) {
        if (entry.getAbbreviationMap() == null) return 0;
        Map<String, String> map = parseMap(entry.getAbbreviationMap());
        if (map == null || map.isEmpty()) return 0;

        int count = 0;
        for (Map.Entry<String, String> kv : map.entrySet()) {
            String abbr = kv.getKey().trim();
            String expansion = kv.getValue().trim();
            if (abbr.isBlank() || expansion.isBlank()) continue;

            AbbreviationMaster master = abbreviationMasterRepository.findById(abbr)
                    .orElse(new AbbreviationMaster());
            master.setAbbreviation(abbr);
            // Keep expansion with highest occurrence count (prefer newer context)
            master.setExpansion(expansion);
            if (entry.getIcd10Code() != null && master.getIcd10Context() == null) {
                master.setIcd10Context(entry.getIcd10Code());
            }
            master.setOccurrenceCount(master.getOccurrenceCount() + 1);
            abbreviationMasterRepository.save(master);
            count++;
        }
        return count;
    }

    private Map<String, String> parseMap(String json) {
        try {
            return objectMapper.readValue(json, new TypeReference<>() {});
        } catch (JsonProcessingException e) {
            log.warn("Failed to parse abbreviation_map JSON: {}", e.getMessage());
            return null;
        }
    }
}
