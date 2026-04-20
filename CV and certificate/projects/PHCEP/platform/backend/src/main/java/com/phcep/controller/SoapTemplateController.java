package com.phcep.controller;

import com.phcep.model.SoapTemplate;
import com.phcep.service.SoapTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

/**
 * SOAP Template REST API.
 *
 * <pre>
 * GET    /api/soap-templates              — list all (or filtered by ?category=)
 * POST   /api/soap-templates              — create
 * PUT    /api/soap-templates/{id}         — update
 * DELETE /api/soap-templates/{id}         — delete (HCP/Admin only)
 * </pre>
 *
 * <p>The frontend ghost/autocomplete window requests all templates and filters
 * by category client-side so only templates in the current SOAP note's
 * category are shown — avoiding showing an encyclopedia of all templates.
 */
@RestController
@RequestMapping("/api/soap-templates")
@RequiredArgsConstructor
public class SoapTemplateController {

    private final SoapTemplateService soapTemplateService;

    @GetMapping
    public ResponseEntity<List<SoapTemplate>> list(
            @RequestParam(required = false) String category) {
        List<SoapTemplate> result = (category != null && !category.isBlank())
                ? soapTemplateService.listByCategory(category)
                : soapTemplateService.listAll();
        return ResponseEntity.ok(result);
    }

    @PostMapping
    public ResponseEntity<SoapTemplate> create(@RequestBody SoapTemplate template) {
        return ResponseEntity.ok(soapTemplateService.create(template));
    }

    @PutMapping("/{id}")
    public ResponseEntity<SoapTemplate> update(
            @PathVariable UUID id,
            @RequestBody SoapTemplate patch) {
        return ResponseEntity.ok(soapTemplateService.update(id, patch));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or hasRole('HCP')")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        soapTemplateService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
