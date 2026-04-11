package com.phcep.controller;

import com.phcep.model.AiAuditLog;
import com.phcep.repository.AiAuditLogRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

/**
 * REST controller for platform-manager / admin functions.
 *
 * All endpoints require ADMIN role.
 *
 * GET /api/admin/audit-log           — paginated list of all AI messages sent to users
 * GET /api/admin/audit-log/{id}      — detail for a single audit entry
 * GET /api/admin/audit-log/query/{queryId} — all audit entries for a query
 * GET /api/admin/audit-log/stats     — summary counts by message type
 */
@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ADMIN')")
public class AdminController {

    private final AiAuditLogRepository auditLogRepository;

    /**
     * Paginated audit log — most recent first.
     *
     * @param page     zero-based page index (default 0)
     * @param size     page size (default 50, max 200)
     * @param type     optional filter by MessageType
     * @param from     optional start datetime (ISO-8601)
     * @param to       optional end datetime (ISO-8601)
     */
    @GetMapping("/audit-log")
    public ResponseEntity<Page<AiAuditLog>> auditLog(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size,
            @RequestParam(required = false) AiAuditLog.MessageType type,
            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime from,
            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime to) {

        int safeSize = Math.min(size, 200);
        Pageable pageable = PageRequest.of(page, safeSize);

        Page<AiAuditLog> result;
        if (type != null) {
            result = auditLogRepository.findByMessageType(type, pageable);
        } else if (from != null && to != null) {
            result = auditLogRepository.findByDateRange(from, to, pageable);
        } else {
            result = auditLogRepository.findAllByOrderBySentAtDesc(pageable);
        }
        return ResponseEntity.ok(result);
    }

    /** Get a single audit log entry by its UUID. */
    @GetMapping("/audit-log/{id}")
    public ResponseEntity<AiAuditLog> getAuditEntry(@PathVariable UUID id) {
        return auditLogRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /** All audit entries for a specific query (useful for drill-down). */
    @GetMapping("/audit-log/query/{queryId}")
    public ResponseEntity<?> auditForQuery(@PathVariable UUID queryId) {
        return ResponseEntity.ok(auditLogRepository.findByQueryIdOrderBySentAtDesc(queryId));
    }

    /**
     * Summary statistics for the platform manager dashboard.
     * Returns total counts by message type.
     */
    @GetMapping("/audit-log/stats")
    public ResponseEntity<Map<String, Long>> stats() {
        Map<String, Long> stats = Map.of(
                "totalMessages", auditLogRepository.count(),
                "aiAnswers", auditLogRepository.countByMessageType(AiAuditLog.MessageType.AI_ANSWER),
                "hcpEscalations", auditLogRepository.countByMessageType(AiAuditLog.MessageType.HCP_ESCALATION),
                "hcpAnswerRelays", auditLogRepository.countByMessageType(AiAuditLog.MessageType.HCP_ANSWER_RELAY)
        );
        return ResponseEntity.ok(stats);
    }
}
