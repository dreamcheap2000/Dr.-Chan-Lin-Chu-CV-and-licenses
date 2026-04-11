package com.phcep.repository;

import com.phcep.model.PatientRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface PatientRepository extends JpaRepository<PatientRecord, UUID> {

    Optional<PatientRecord> findByPseudonymousToken(String pseudonymousToken);

    boolean existsByPseudonymousToken(String pseudonymousToken);
}
