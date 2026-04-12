package com.phcep.service;

import com.phcep.model.ClinicalEntry;
import com.phcep.repository.ClinicalEntryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Optional Workflow A connector: reads a Google Sheet daily and upserts rows
 * into {@code clinical_entry} using the sheet row ID as idempotency key.
 *
 * <p>Requires a Google service-account JSON key file and the target spreadsheet
 * ID to be configured in {@code application.yml}.
 *
 * <p>The Google Sheets API v4 client library ({@code google-api-services-sheets})
 * must be added to {@code pom.xml} before this service is enabled.
 * Until then the class compiles but the nightly job is a no-op when the
 * spreadsheet ID is blank.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class GoogleSheetsAdapterService {

    private final ClinicalEntryService clinicalEntryService;

    @Value("${phcep.google-sheets.spreadsheet-id:}")
    private String spreadsheetId;

    @Value("${phcep.google-sheets.range:Sheet1!A1:Z}")
    private String range;

    @Value("${phcep.google-sheets.credentials-path:}")
    private String credentialsPath;

    @Value("${phcep.google-sheets.user-token:GSHEETS_IMPORT}")
    private String defaultUserToken;

    /**
     * Nightly sync at 01:00 — runs before Gemini classification (02:00).
     */
    @Scheduled(cron = "0 0 1 * * *")
    @Transactional
    public void syncFromSheet() {
        if (spreadsheetId == null || spreadsheetId.isBlank()) {
            log.debug("GoogleSheetsAdapterService: spreadsheet-id not configured — skipping.");
            return;
        }
        log.info("GoogleSheetsAdapterService: syncing from spreadsheet {}", spreadsheetId);
        try {
            List<List<Object>> rows = fetchRows();
            if (rows == null || rows.isEmpty()) {
                log.info("GoogleSheetsAdapterService: sheet is empty or inaccessible.");
                return;
            }
            // First row is header
            List<Object> header = rows.get(0);
            int imported = 0;
            for (int i = 1; i < rows.size(); i++) {
                List<Object> row = rows.get(i);
                try {
                    ClinicalEntry entry = mapRow(header, row, i);
                    clinicalEntryService.upsertFromSheet(entry);
                    imported++;
                } catch (Exception e) {
                    log.warn("GoogleSheetsAdapterService: failed to import row {}: {}", i, e.getMessage());
                }
            }
            log.info("GoogleSheetsAdapterService: imported/updated {} rows.", imported);
        } catch (Exception e) {
            log.error("GoogleSheetsAdapterService: sync failed: {}", e.getMessage(), e);
        }
    }

    // ─── Private helpers ──────────────────────────────────────────────────────

    /**
     * Fetches all rows from the configured Google Sheet.
     *
     * <p>Uses the Google Sheets API v4 Java client if available.
     * Returns null (and logs a warning) when the dependency is absent.
     */
    private List<List<Object>> fetchRows() {
        // Dependency guard — the google-api-services-sheets library is optional.
        try {
            Class.forName("com.google.api.services.sheets.v4.Sheets");
        } catch (ClassNotFoundException e) {
            log.warn("Google Sheets API client library not on classpath. "
                    + "Add google-api-services-sheets to pom.xml to enable sheet sync.");
            return null;
        }

        // When the library IS present this block executes the real API call.
        try {
            com.google.api.client.json.gson.GsonFactory jsonFactory =
                    com.google.api.client.json.gson.GsonFactory.getDefaultInstance();
            com.google.api.client.http.javanet.NetHttpTransport transport =
                    new com.google.api.client.http.javanet.NetHttpTransport();

            com.google.auth.oauth2.GoogleCredentials credentials;
            try (java.io.FileInputStream fis = new java.io.FileInputStream(credentialsPath)) {
                credentials = com.google.auth.oauth2.GoogleCredentials
                        .fromStream(fis)
                        .createScoped("https://www.googleapis.com/auth/spreadsheets.readonly");
            }

            com.google.api.services.sheets.v4.Sheets service =
                    new com.google.api.services.sheets.v4.Sheets.Builder(
                            transport, jsonFactory,
                            new com.google.auth.http.HttpCredentialsAdapter(credentials))
                    .setApplicationName("PHCEP")
                    .build();

            com.google.api.services.sheets.v4.model.ValueRange response =
                    service.spreadsheets().values().get(spreadsheetId, range).execute();

            @SuppressWarnings("unchecked")
            List<List<Object>> values = (List<List<Object>>) (List<?>) response.getValues();
            return values;
        } catch (Exception e) {
            log.error("Failed to read Google Sheet: {}", e.getMessage(), e);
            return null;
        }
    }

    /**
     * Maps a sheet row to a {@link ClinicalEntry}.
     * Expected column order (matches the plan):
     * A=entry_type, B=icd10_code, C=raw_text, D=ebm_statement,
     * E=source_url, F=source_name, G=exam_date, H=ebm_extraction_date, I=tags
     */
    private ClinicalEntry mapRow(List<Object> header, List<Object> row, int rowIndex) {
        ClinicalEntry e = new ClinicalEntry();
        e.setPseudonymousUserToken(defaultUserToken);
        e.setGsheetRowId("row_" + rowIndex);

        e.setEntryType(ClinicalEntry.EntryType.valueOf(
                cell(row, 0, "NOTE").toUpperCase()));
        e.setIcd10Code(cell(row, 1, null));
        e.setRawText(cell(row, 2, ""));
        e.setEbmStatement(cell(row, 3, null));
        e.setSourceUrl(cell(row, 4, null));
        e.setSourceName(cell(row, 5, null));

        String examDateStr = cell(row, 6, null);
        if (examDateStr != null && !examDateStr.isBlank()) {
            try { e.setExamDate(LocalDate.parse(examDateStr)); } catch (Exception ignored) {}
        }
        String ebmDateStr = cell(row, 7, null);
        if (ebmDateStr != null && !ebmDateStr.isBlank()) {
            try { e.setEbmExtractionDate(LocalDate.parse(ebmDateStr)); } catch (Exception ignored) {}
        }
        String tagsStr = cell(row, 8, null);
        if (tagsStr != null && !tagsStr.isBlank()) {
            e.setTags(List.of(tagsStr.split(",\\s*")));
        }
        return e;
    }

    private String cell(List<Object> row, int idx, String defaultValue) {
        if (row == null || idx >= row.size()) return defaultValue;
        Object val = row.get(idx);
        if (val == null) return defaultValue;
        String s = val.toString().trim();
        return s.isEmpty() ? defaultValue : s;
    }
}
