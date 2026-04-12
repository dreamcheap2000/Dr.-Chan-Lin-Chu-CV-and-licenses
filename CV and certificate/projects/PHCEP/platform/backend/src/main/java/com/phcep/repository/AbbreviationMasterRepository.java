package com.phcep.repository;

import com.phcep.model.AbbreviationMaster;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AbbreviationMasterRepository extends JpaRepository<AbbreviationMaster, String> {

    /** Full-text search across abbreviation and expansion. */
    @Query(value = """
            SELECT * FROM abbreviation_master
            WHERE to_tsvector('english', abbreviation || ' ' || expansion)
                  @@ plainto_tsquery('english', :query)
            ORDER BY occurrence_count DESC
            LIMIT :limit
            """, nativeQuery = true)
    List<AbbreviationMaster> search(String query, int limit);

    /** All entries ordered by frequency (most-used first). */
    List<AbbreviationMaster> findAllByOrderByOccurrenceCountDesc();
}
