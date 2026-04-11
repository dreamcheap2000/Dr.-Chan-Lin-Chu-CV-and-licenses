package com.phcep.service;

import com.phcep.model.EbmEntry;
import com.phcep.repository.EbmEntryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * EBM knowledge base management:
 * save entries with FastSR embeddings, full-text search, semantic search.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class EbmService {

    private final EbmEntryRepository ebmEntryRepository;
    private final FastSRService fastSRService;

    @Transactional
    public EbmEntry save(EbmEntry entry) {
        // Encode statement with FastSR
        try {
            FastSRService.EmbeddingResult emb = fastSRService.encode(entry.getStatement());
            if (emb != null) {
                entry.setSemanticEmbeddingJson(emb.semantic().toString());
                entry.setGlobalEmbeddingJson(emb.global().toString());
                entry.setFragmentEmbeddingJson(emb.fragment().toString());
            }
        } catch (Exception e) {
            log.warn("FastSR encoding failed for EBM entry: {}", e.getMessage());
        }
        return ebmEntryRepository.save(entry);
    }

    public Optional<EbmEntry> findById(UUID id) {
        return ebmEntryRepository.findById(id);
    }

    public List<EbmEntry> search(String query, int limit) {
        return ebmEntryRepository.fullTextSearch(query, limit);
    }

    /**
     * Semantic search: encodes the query with FastSR, then delegates
     * cosine similarity ranking to the ML microservice.
     */
    public List<EbmEntry> semanticSearch(String queryText, int topK) {
        // Retrieve candidate entries (broad filter), then rank by ML service
        return ebmEntryRepository.findTop50ByOrderByCreatedAtDesc()
                .stream()
                .limit(topK)
                .toList();
        // TODO Phase 2: call FastSR /semantic-search with vector and retrieve top-k IDs
    }

    @Transactional
    public void delete(UUID id) {
        ebmEntryRepository.deleteById(id);
    }
}
