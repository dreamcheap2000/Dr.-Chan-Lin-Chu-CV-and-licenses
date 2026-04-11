package com.phcep.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * HTTP bridge to the Python FastAPI ML microservice.
 *
 * Endpoints on the ML service:
 *   POST /encode  — returns semantic, global, and fragment embeddings
 *   POST /query   — retrieves top-k ranked answers for a query;
 *                   includes per-match list, confidence, and escalation flag
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class FastSRService {

    private final WebClient.Builder webClientBuilder;

    @Value("${phcep.ml.base-url}")
    private String mlBaseUrl;

    @Value("${phcep.ml.timeout-seconds}")
    private int timeoutSeconds;

    public EmbeddingResult encode(String text) {
        return webClientBuilder.build()
                .post()
                .uri(mlBaseUrl + "/encode")
                .bodyValue(Map.of("text", text))
                .retrieve()
                .bodyToMono(EmbeddingResult.class)
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .block();
    }

    public QueryResult query(String pseudonymousToken, String queryText, int topK) {
        Map<String, Object> body = Map.of(
                "pseudonymous_token", pseudonymousToken,
                "query_text", queryText,
                "top_k", topK
        );
        return webClientBuilder.build()
                .post()
                .uri(mlBaseUrl + "/query")
                .bodyValue(body)
                .retrieve()
                .bodyToMono(QueryResult.class)
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .onErrorResume(e -> {
                    log.warn("FastSR query failed: {}", e.getMessage());
                    return Mono.just(new QueryResult("", "", 0.0, List.of(), true));
                })
                .block();
    }

    /** Convenience overload with default top_k = 3. */
    public QueryResult query(String pseudonymousToken, String queryText) {
        return query(pseudonymousToken, queryText, 3);
    }

    public record EmbeddingResult(List<Double> semantic, List<Double> global, List<Double> fragment) {}

    /** A single ranked match returned by the ML service. */
    public record MatchItem(int rank, String text, double confidence, String citation, String source, String url) {}

    /**
     * Full query response from the ML service.
     *
     * @param answer       synthesised narrative answer
     * @param citations    semicolon-separated citations
     * @param confidence   top match confidence (0–1)
     * @param matches      per-match ranked list (up to top_k entries)
     * @param escalated    true when confidence is below the ML threshold
     */
    public record QueryResult(
            String answer,
            String citations,
            double confidence,
            List<MatchItem> matches,
            boolean escalated) {}
}

