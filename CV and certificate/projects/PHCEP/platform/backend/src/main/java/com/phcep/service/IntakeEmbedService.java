package com.phcep.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.phcep.model.ClinicalEntry;
import com.phcep.repository.ClinicalEntryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * Bridges Spring Boot to the Python {@code intake_worker.py} microservice.
 *
 * <p>Calls {@code POST /intake/embed} with the entry's raw text and writes
 * the resulting FastSR semantic vector back to
 * {@code clinical_entry.semantic_embedding_json}.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class IntakeEmbedService {

    private final ClinicalEntryRepository clinicalEntryRepository;
    private final WebClient.Builder webClientBuilder;
    private final ObjectMapper objectMapper;

    @Value("${phcep.intake-worker.base-url:${phcep.ml.base-url}}")
    private String mlBaseUrl;

    @Value("${phcep.ml.timeout-seconds}")
    private int timeoutSeconds;

    /**
     * Asynchronously embed a clinical entry via the Python ML microservice.
     * Called immediately after a new entry is persisted.
     */
    @Async
    @Transactional
    public void embedAsync(ClinicalEntry entry) {
        try {
            String embedding = embed(entry.getRawText());
            if (embedding != null) {
                entry.setSemanticEmbeddingJson(embedding);
                clinicalEntryRepository.save(entry);
                log.debug("Embedded clinical entry {} (len={})", entry.getId(), embedding.length());
            }
        } catch (Exception e) {
            log.warn("Async embedding failed for entry {}: {}", entry.getId(), e.getMessage());
        }
    }

    /**
     * Synchronously embed a text string and return the JSON vector string.
     * Exposed for batch re-embedding if needed.
     */
    @SuppressWarnings("unchecked")
    public String embed(String text) {
        try {
            Map<String, Object> resp = webClientBuilder.build()
                    .post()
                    .uri(mlBaseUrl + "/intake/embed")
                    .bodyValue(Map.of("text", text))
                    .retrieve()
                    .bodyToMono(Map.class)
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .block();
            if (resp != null && resp.containsKey("semantic")) {
                List<?> vec = (List<?>) resp.get("semantic");
                try {
                    return objectMapper.writeValueAsString(vec);
                } catch (JsonProcessingException e) {
                    log.warn("IntakeEmbedService: failed to serialize embedding vector: {}", e.getMessage());
                }
            }
        } catch (Exception e) {
            log.warn("IntakeEmbedService.embed failed: {}", e.getMessage());
        }
        return null;
    }
}
