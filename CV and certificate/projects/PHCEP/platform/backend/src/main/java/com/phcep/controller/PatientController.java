package com.phcep.controller;

import com.phcep.model.HealthObservation;
import com.phcep.service.PatientService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

/**
 * REST controller for patient health observations (labs, vitals, imaging, symptoms).
 * POST /api/patient/observations          — record a new observation
 * GET  /api/patient/observations          — list own observations (with date filter)
 * GET  /api/patient/observations/timeline — longitudinal timeline
 */
@RestController
@RequestMapping("/api/patient")
@RequiredArgsConstructor
public class PatientController {

    private final PatientService patientService;

    @PostMapping("/observations")
    public ResponseEntity<HealthObservation> addObservation(
            @Valid @RequestBody HealthObservation observation,
            @RequestAttribute("pseudonymousToken") String token) {
        observation.setPseudonymousToken(token);
        HealthObservation saved = patientService.recordObservation(observation);
        return ResponseEntity.accepted().body(saved);
    }

    @GetMapping("/observations")
    public ResponseEntity<List<HealthObservation>> listObservations(
            @RequestAttribute("pseudonymousToken") String token,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to) {
        return ResponseEntity.ok(patientService.listObservations(token, from, to));
    }

    @GetMapping("/observations/timeline")
    public ResponseEntity<List<HealthObservation>> timeline(
            @RequestAttribute("pseudonymousToken") String token) {
        return ResponseEntity.ok(patientService.getTimeline(token));
    }
}
