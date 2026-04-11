package com.phcep.repository;

import com.phcep.model.EbmEntry;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface EbmEntryRepository extends JpaRepository<EbmEntry, UUID> {

    @Query(value = """
            SELECT * FROM ebm_entries
            WHERE to_tsvector('english', statement || ' ' || COALESCE(pmid,'') || ' ' || COALESCE(icd10_codes,'') || ' ' || COALESCE(specialty,''))
                  @@ plainto_tsquery('english', :query)
            LIMIT :limit
            """, nativeQuery = true)
    List<EbmEntry> fullTextSearch(String query, int limit);

    List<EbmEntry> findTop50ByOrderByCreatedAtDesc();

    List<EbmEntry> findBySpecialtyOrderByCreatedAtDesc(String specialty);

    List<EbmEntry> findByIcd10CodesContainingOrderByCreatedAtDesc(String icd10Code);
}
