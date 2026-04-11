package com.phcep.repository;

import com.phcep.model.MedicalQuery;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface MedicalQueryRepository extends JpaRepository<MedicalQuery, UUID> {

    List<MedicalQuery> findByPseudonymousTokenOrderByCreatedAtDesc(String pseudonymousToken);

    List<MedicalQuery> findByStatusIn(List<MedicalQuery.QueryStatus> statuses);

    @Query("SELECT q FROM MedicalQuery q WHERE q.icd10Code = :icd10Code ORDER BY q.createdAt DESC")
    List<MedicalQuery> findByIcd10Code(String icd10Code);
}
