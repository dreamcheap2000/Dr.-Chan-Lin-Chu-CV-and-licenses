package com.phcep.service;

import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.parser.IParser;
import com.phcep.model.HealthObservation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.hl7.fhir.r4.model.*;
import org.springframework.stereotype.Service;

import java.util.Date;

/**
 * Translates internal PHCEP models to/from FHIR R4 resources.
 * Targets conformance with TW Core IG profiles.
 *
 * Key profiles used:
 *   TWCoreObservationLaboratoryResult → Lab observations
 *   TWCorePatient                     → Patient records
 *   TWCoreDiagnosticReport            → Imaging / reports
 *
 * TW Core IG: https://twcore.mohw.gov.tw/ig/twcore/
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class FhirService {

    private final FhirContext fhirContext;
    private final IParser fhirJsonParser;

    private static final String TW_CORE_PATIENT_PROFILE =
            "https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/Patient-twcore";
    private static final String TW_CORE_OBS_LAB_PROFILE =
            "https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition/Observation-laboratoryResult-twcore";

    /**
     * Converts a HealthObservation to a FHIR R4 Observation JSON string
     * conformant with TW Core IG lab result profile.
     */
    public String toFhirObservationJson(HealthObservation obs) {
        try {
            Observation fhirObs = new Observation();

            // Profile
            fhirObs.getMeta().addProfile(TW_CORE_OBS_LAB_PROFILE);
            fhirObs.getMeta().addSecurity()
                    .setSystem("http://terminology.hl7.org/CodeSystem/v3-Confidentiality")
                    .setCode("R")
                    .setDisplay("Restricted");

            fhirObs.setStatus(Observation.ObservationStatus.FINAL);

            // Subject (pseudonymous reference)
            fhirObs.setSubject(new Reference().setDisplay(obs.getPseudonymousToken()));

            // LOINC code
            if (obs.getLoincCode() != null) {
                fhirObs.setCode(new CodeableConcept()
                        .addCoding(new Coding()
                                .setSystem("http://loinc.org")
                                .setCode(obs.getLoincCode())));
            }

            // Effective date
            if (obs.getEffectiveDateTime() != null) {
                fhirObs.setEffective(new DateTimeType(
                        java.util.Date.from(obs.getEffectiveDateTime()
                                .atZone(java.time.ZoneId.systemDefault()).toInstant())));
            }

            // Numeric value + unit
            if (obs.getNumericValue() != null) {
                Quantity qty = new Quantity()
                        .setValue(obs.getNumericValue());
                if (obs.getUnit() != null) qty.setUnit(obs.getUnit());
                if (obs.getReferenceRangeLow() != null || obs.getReferenceRangeHigh() != null) {
                    Observation.ObservationReferenceRangeComponent range =
                            new Observation.ObservationReferenceRangeComponent();
                    if (obs.getReferenceRangeLow() != null)
                        range.setLow(new Quantity().setValue(obs.getReferenceRangeLow()));
                    if (obs.getReferenceRangeHigh() != null)
                        range.setHigh(new Quantity().setValue(obs.getReferenceRangeHigh()));
                    fhirObs.addReferenceRange(range);
                }
                fhirObs.setValue(qty);
            } else if (obs.getObservationText() != null) {
                fhirObs.setValue(new StringType(obs.getObservationText()));
            }

            return fhirJsonParser.encodeResourceToString(fhirObs);
        } catch (Exception e) {
            log.warn("FHIR serialisation failed for observation {}: {}", obs.getId(), e.getMessage());
            return null;
        }
    }
}
