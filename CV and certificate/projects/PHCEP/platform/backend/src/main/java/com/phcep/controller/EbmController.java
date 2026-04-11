package com.phcep.controller;

import com.phcep.model.EbmEntry;
import com.phcep.service.EbmService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

/**
 * REST controller for EBM knowledge base entries.
 * HCP/Admin can create/update; all authenticated users can read/search.
 */
@RestController
@RequestMapping("/api/ebm")
@RequiredArgsConstructor
public class EbmController {

    private final EbmService ebmService;

    /** Add a new EBM entry (HCP or Admin). */
    @PostMapping
    @PreAuthorize("hasAnyRole('HCP','ADMIN')")
    public ResponseEntity<EbmEntry> create(@Valid @RequestBody EbmEntry entry) {
        return ResponseEntity.ok(ebmService.save(entry));
    }

    @GetMapping("/{id}")
    public ResponseEntity<EbmEntry> get(@PathVariable UUID id) {
        return ebmService.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /** Full-text search across statements, PMID, ICD-10, specialty. */
    @GetMapping("/search")
    public ResponseEntity<List<EbmEntry>> search(@RequestParam String q,
                                                  @RequestParam(defaultValue = "10") int limit) {
        return ResponseEntity.ok(ebmService.search(q, limit));
    }

    /** Semantic search via FastSR embeddings. */
    @GetMapping("/semantic-search")
    public ResponseEntity<List<EbmEntry>> semanticSearch(@RequestParam String q,
                                                          @RequestParam(defaultValue = "10") int topK) {
        return ResponseEntity.ok(ebmService.semanticSearch(q, topK));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        ebmService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
