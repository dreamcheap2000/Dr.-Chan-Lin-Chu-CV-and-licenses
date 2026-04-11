package com.phcep.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.HexFormat;

/**
 * Strips / pseudonymises Personally Identifiable Information (PII).
 *
 * Strategy:
 *  - Patient names / IDs → deterministic UUID via HMAC-SHA256
 *  - Dates → per-patient random offset (consistent for the same patient)
 *  - Direct identifiers → [REDACTED]
 */
@Service
@Slf4j
public class DeIdentificationService {

    @Value("${phcep.deidentification.date-shift-seed}")
    private String dateSeed;

    /**
     * Generates a stable pseudonymous token from a real identifier.
     * Uses SHA-256 so the mapping is deterministic but not reversible.
     */
    public String pseudonymise(String realId) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest((dateSeed + realId).getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash).substring(0, 32);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 not available", e);
        }
    }

    /**
     * Shifts a date by a patient-specific offset derived from their token.
     * The shift is in the range [-180, +180] days, consistent per patient.
     */
    public LocalDateTime shiftDate(String pseudonymousToken, LocalDateTime original) {
        if (original == null) return null;
        int shiftDays = computeShiftDays(pseudonymousToken);
        return original.plus(shiftDays, ChronoUnit.DAYS);
    }

    private int computeShiftDays(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest((dateSeed + token).getBytes(StandardCharsets.UTF_8));
            int raw = ((hash[0] & 0xFF) << 8) | (hash[1] & 0xFF);
            return (raw % 361) - 180;  // range [-180, +180]
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 not available", e);
        }
    }

    public String redact(String value) {
        return "[REDACTED]";
    }
}
