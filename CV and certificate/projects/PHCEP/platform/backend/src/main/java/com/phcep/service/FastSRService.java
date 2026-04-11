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
 *   POST /query   — retrieves top-k answers for a query from user's context
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

    public QueryResult query(String pseudonymousToken, String queryText) {
        Map<String, Object> body = Map.of(
                "pseudonymous_token", pseudonymousToken,
                "query_text", queryText
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
                    return Mono.just(new QueryResult("", "", 0.0));
                })
                .block();
    }

    public record EmbeddingResult(List<Double> semantic, List<Double> global, List<Double> fragment) {}

    public record QueryResult(String answer, String citations, double confidence) {}
}
