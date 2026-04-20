package com.phcep.repository;

import com.phcep.model.SoapTemplate;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface SoapTemplateRepository extends JpaRepository<SoapTemplate, UUID> {

    /** Templates in a given category, ordered by creation time. */
    List<SoapTemplate> findByCategoryOrderByCreatedAtAsc(String category);

    /** All templates across categories, ordered by creation time. */
    List<SoapTemplate> findAllByOrderByCreatedAtAsc();
}
