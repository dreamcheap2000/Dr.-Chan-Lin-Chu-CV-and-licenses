package com.phcep.controller;

import com.phcep.model.MedicalQuery;
import com.phcep.service.QueryService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

/**
 * REST controller for medical query submission and retrieval.
 * POST /api/queries        — patient submits a query
 * GET  /api/queries/{id}   — get query details + AI/HCP answer
 * GET  /api/queries/my     — list current user's queries
 */
@RestController
@RequestMapping("/api/queries")
@RequiredArgsConstructor
public class QueryController {

    private final QueryService queryService;

    @PostMapping
    public ResponseEntity<MedicalQuery> submitQuery(@Valid @RequestBody QueryRequest request,
                                                     @RequestAttribute("pseudonymousToken") String token) {
        MedicalQuery query = queryService.submitQuery(token, request.queryText(), request.icd10Code());
        return ResponseEntity.accepted().body(query);
    }

    @GetMapping("/{id}")
    public ResponseEntity<MedicalQuery> getQuery(@PathVariable UUID id,
                                                  @RequestAttribute("pseudonymousToken") String token) {
        return queryService.findByIdForUser(id, token)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/my")
    public ResponseEntity<List<MedicalQuery>> myQueries(@RequestAttribute("pseudonymousToken") String token) {
        return ResponseEntity.ok(queryService.listQueriesForUser(token));
    }

    /** HCP endpoint: list all queries in pending/HCP_NOTIFIED state. */
    @GetMapping("/hcp/pending")
    @PreAuthorize("hasRole('HCP')")
    public ResponseEntity<List<MedicalQuery>> pendingQueries() {
        return ResponseEntity.ok(queryService.listPendingForHcp());
    }

    /** HCP endpoint: submit an answer to a query. */
    @PatchMapping("/hcp/{id}/answer")
    @PreAuthorize("hasRole('HCP')")
    public ResponseEntity<MedicalQuery> hcpAnswer(@PathVariable UUID id,
                                                   @RequestBody HcpAnswerRequest req) {
        return ResponseEntity.ok(queryService.hcpAnswer(id, req.answer(), req.citations()));
    }

    public record QueryRequest(String queryText, String icd10Code) {}
    public record HcpAnswerRequest(String answer, String citations) {}
}
