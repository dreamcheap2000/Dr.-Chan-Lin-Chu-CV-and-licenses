package com.phcep.repository;

import com.phcep.model.ClinicalEntry;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ClinicalEntryRepository extends JpaRepository<ClinicalEntry, UUID> {

    /** Used by the ML query engine to retrieve all entries for a user. */
    List<ClinicalEntry> findByPseudonymousUserTokenOrderByInputTimestampDesc(String token);

    /** Paginated list with optional filters (all nullable). */
    @Query("""
            SELECT e FROM ClinicalEntry e
            WHERE e.pseudonymousUserToken = :token
              AND (:type IS NULL OR e.entryType = :type)
              AND (:icd10 IS NULL OR e.icd10Code = :icd10)
              AND (:category IS NULL OR e.geminiCategory = :category)
              AND (:from IS NULL OR e.examDate >= :from)
              AND (:to IS NULL OR e.examDate <= :to)
            ORDER BY e.inputTimestamp DESC
            """)
    Page<ClinicalEntry> filterByUser(
            @Param("token") String token,
            @Param("type") ClinicalEntry.EntryType type,
            @Param("icd10") String icd10,
            @Param("category") String category,
            @Param("from") LocalDate from,
            @Param("to") LocalDate to,
            Pageable pageable);

    /** Entries whose Gemini category has not been set yet (pending nightly job). */
    @Query("SELECT e FROM ClinicalEntry e WHERE e.geminiCategory IS NULL ORDER BY e.inputTimestamp ASC")
    List<ClinicalEntry> findUnclassified();

    /** Entries whose FastSR embedding has not been set yet. */
    @Query("SELECT e FROM ClinicalEntry e WHERE e.semanticEmbeddingJson IS NULL ORDER BY e.inputTimestamp ASC")
    List<ClinicalEntry> findUnembedded();

    /** For Google Sheets upsert. */
    Optional<ClinicalEntry> findByGsheetRowId(String gsheetRowId);

    /** Daily digest counts per category for a given date. */
    @Query(value = """
            SELECT gemini_category AS category, COUNT(*) AS cnt
            FROM clinical_entry
            WHERE DATE(input_timestamp AT TIME ZONE 'UTC') = :date
              AND gemini_category IS NOT NULL
            GROUP BY gemini_category
            ORDER BY cnt DESC
            """, nativeQuery = true)
    List<Object[]> dailySummaryByCategory(@Param("date") java.sql.Date date);

    /** All entries that have a non-null abbreviation_map (for sync). */
    @Query(value = "SELECT * FROM clinical_entry WHERE abbreviation_map IS NOT NULL", nativeQuery = true)
    List<ClinicalEntry> findWithAbbreviationMap();
}
