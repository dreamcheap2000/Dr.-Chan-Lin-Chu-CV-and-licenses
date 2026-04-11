package com.phcep.service;

import com.phcep.model.HealthObservation;
import com.phcep.repository.HealthObservationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * Handles patient observation recording, de-identification, FHIR mapping, and embedding.
 */
@Service
@RequiredArgsConstructor
public class PatientService {

    private final HealthObservationRepository observationRepository;
    private final DeIdentificationService deIdentificationService;
    private final FhirService fhirService;
    private final FastSRService fastSRService;

    @Transactional
    public HealthObservation recordObservation(HealthObservation observation) {
        // 1. De-identify effective date
        if (observation.getEffectiveDateTime() != null) {
            observation.setEffectiveDateTime(
                    deIdentificationService.shiftDate(
                            observation.getPseudonymousToken(),
                            observation.getEffectiveDateTime()));
        }
        // 2. Generate FHIR Observation JSON
        String fhirJson = fhirService.toFhirObservationJson(observation);
        observation.setFhirObservationJson(fhirJson);
        // 3. Encode with FastSR for future retrieval
        if (observation.getObservationText() != null) {
            FastSRService.EmbeddingResult emb = fastSRService.encode(observation.getObservationText());
            if (emb != null) {
                observation.setSemanticEmbeddingJson(emb.semantic().toString());
            }
        }
        return observationRepository.save(observation);
    }

    public List<HealthObservation> listObservations(String token, LocalDate from, LocalDate to) {
        LocalDateTime start = (from != null) ? from.atStartOfDay() : LocalDateTime.MIN;
        LocalDateTime end = (to != null) ? to.atTime(23, 59, 59) : LocalDateTime.MAX;
        return observationRepository
                .findByPseudonymousTokenAndEffectiveDateTimeBetweenOrderByEffectiveDateTimeAsc(
                        token, start, end);
    }

    public List<HealthObservation> getTimeline(String token) {
        return observationRepository
                .findByPseudonymousTokenOrderByEffectiveDateTimeAsc(token);
    }
}
