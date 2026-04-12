package com.phcep.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.phcep.model.ClinicalEntry;
import com.phcep.repository.ClinicalEntryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * Calls the Google Gemini API to:
 * <ol>
 *   <li>Classify {@code raw_text} into a clinical category
 *       → {@code gemini_category}</li>
 *   <li>Extract abbreviations and their expansions
 *       → {@code abbreviation_map} (JSONB)</li>
 * </ol>
 *
 * <p>Runs nightly at 02:00 for all unclassified entries.
 * Also triggered inline (async) when a new entry is saved.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class GeminiClassificationService {

    private final ClinicalEntryRepository clinicalEntryRepository;
    private final AbbreviationSyncService abbreviationSyncService;
    private final WebClient.Builder webClientBuilder;
    private final ObjectMapper objectMapper;

    @Value("${phcep.gemini.api-key:}")
    private String geminiApiKey;

    @Value("${phcep.gemini.model:gemini-1.5-flash}")
    private String geminiModel;

    private static final String GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/";
    private static final int TIMEOUT_SECONDS = 30;

    // ─── Nightly batch ────────────────────────────────────────────────────────

    /**
     * Classifies all unclassified entries nightly at 02:00.
     */
    @Scheduled(cron = "0 0 2 * * *")
    @Transactional
    public void classifyAll() {
        if (geminiApiKey == null || geminiApiKey.isBlank()) {
            log.warn("GeminiClassificationService: api-key not configured — skipping batch.");
            return;
        }
        List<ClinicalEntry> unclassified = clinicalEntryRepository.findUnclassified();
        log.info("GeminiClassificationService: classifying {} unclassified entries.", unclassified.size());
        for (ClinicalEntry entry : unclassified) {
            classifySingle(entry);
        }
    }

    // ─── Inline async (called on POST /api/entries) ───────────────────────────

    @Async
    public void classifyAsync(ClinicalEntry entry) {
        if (geminiApiKey == null || geminiApiKey.isBlank()) return;
        try {
            classifySingle(entry);
        } catch (Exception e) {
            log.warn("Async Gemini classification failed for entry {}: {}", entry.getId(), e.getMessage());
        }
    }

    // ─── Core classification ──────────────────────────────────────────────────

    @Transactional
    public void classifySingle(ClinicalEntry entry) {
        String prompt = buildPrompt(entry);
        try {
            String responseText = callGemini(prompt);
            GeminiResult result = parseResult(responseText);
            entry.setGeminiCategory(result.category());
            entry.setGeminiConfidence(result.confidence());
            entry.setAbbreviationMap(objectMapper.writeValueAsString(result.abbreviations()));
            clinicalEntryRepository.save(entry);
            abbreviationSyncService.syncEntry(entry);
            log.debug("Classified entry {} → {} ({:.2f})", entry.getId(), result.category(), result.confidence());
        } catch (Exception e) {
            log.warn("Gemini classification failed for entry {}: {}", entry.getId(), e.getMessage());
        }
    }

    // ─── Private helpers ──────────────────────────────────────────────────────

    private String buildPrompt(ClinicalEntry entry) {
        return """
                You are a clinical informatics assistant. Given the following medical note, do two things:
                1. Classify the note into one short clinical category (e.g. "Neurology / Stroke", "Cardiology / Heart Failure", "Endocrinology / Diabetes").
                2. Extract ALL medical abbreviations used in the note and provide their full expansions.

                Return ONLY valid JSON in this exact format (no markdown, no extra text):
                {
                  "category": "<category string>",
                  "confidence": <float 0-1>,
                  "abbreviations": {"<ABBR>": "<expansion>", ...}
                }

                Entry type: %s
                ICD-10: %s
                Note:
                %s
                """.formatted(
                entry.getEntryType().name(),
                entry.getIcd10Code() != null ? entry.getIcd10Code() : "N/A",
                entry.getRawText()
        );
    }

    @SuppressWarnings("unchecked")
    private String callGemini(String prompt) {
        String url = GEMINI_BASE + geminiModel + ":generateContent?key=" + geminiApiKey;
        Map<String, Object> body = Map.of(
                "contents", List.of(Map.of(
                        "parts", List.of(Map.of("text", prompt))
                ))
        );
        Map<String, Object> response = webClientBuilder.build()
                .post()
                .uri(url)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(Map.class)
                .timeout(Duration.ofSeconds(TIMEOUT_SECONDS))
                .block();

        // Navigate: candidates[0].content.parts[0].text
        List<Map<String, Object>> candidates = (List<Map<String, Object>>) response.get("candidates");
        Map<String, Object> content = (Map<String, Object>) candidates.get(0).get("content");
        List<Map<String, Object>> parts = (List<Map<String, Object>>) content.get("parts");
        return (String) parts.get(0).get("text");
    }

    @SuppressWarnings("unchecked")
    private GeminiResult parseResult(String json) throws Exception {
        // Strip any accidental markdown fences
        String clean = json.strip();
        if (clean.startsWith("```")) {
            clean = clean.replaceAll("```[a-z]*", "").strip();
        }
        Map<String, Object> map = objectMapper.readValue(clean, Map.class);
        String category = (String) map.getOrDefault("category", "Uncategorised");
        double confidence = ((Number) map.getOrDefault("confidence", 0.5)).doubleValue();
        Map<String, String> abbreviations = (Map<String, String>) map.getOrDefault("abbreviations", Map.of());
        return new GeminiResult(category, confidence, abbreviations);
    }

    private record GeminiResult(String category, double confidence, Map<String, String> abbreviations) {}
}
