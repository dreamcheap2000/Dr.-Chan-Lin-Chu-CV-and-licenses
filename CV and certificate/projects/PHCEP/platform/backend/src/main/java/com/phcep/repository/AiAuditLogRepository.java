package com.phcep.repository;

import com.phcep.model.AiAuditLog;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface AiAuditLogRepository extends JpaRepository<AiAuditLog, UUID> {

    Page<AiAuditLog> findAllByOrderBySentAtDesc(Pageable pageable);

    List<AiAuditLog> findByQueryIdOrderBySentAtDesc(UUID queryId);

    @Query("SELECT a FROM AiAuditLog a WHERE a.sentAt >= :from AND a.sentAt <= :to ORDER BY a.sentAt DESC")
    Page<AiAuditLog> findByDateRange(LocalDateTime from, LocalDateTime to, Pageable pageable);

    @Query("SELECT a FROM AiAuditLog a WHERE a.messageType = :type ORDER BY a.sentAt DESC")
    Page<AiAuditLog> findByMessageType(AiAuditLog.MessageType type, Pageable pageable);

    long countByMessageType(AiAuditLog.MessageType type);
}
