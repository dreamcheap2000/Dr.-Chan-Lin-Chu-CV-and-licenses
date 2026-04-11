# Data Flow

## End-to-End Pipeline

### 1. Data Ingestion

```
Source                 Channel           Service            Store
─────────────────────────────────────────────────────────────────────
Patient (web)    →  POST /api/patient/observations  →  health_observations
Patient (LINE)   →  LINE webhook → QueryService     →  medical_queries
HCP (web)        →  POST /api/ebm                  →  ebm_entries
IoT / wearable   →  MQTT → EdgeDataIngestionService →  health_observations
```

### 2. Encoding Pipeline

Every piece of ingested text is encoded asynchronously:

```
Text (observation / EBM statement / query)
  → FastSRService.encode()
    → POST http://ml:8081/encode
      → PhcepEncoder.encode()
        → BioBERT tokenise
        → semantic  = CLS token embedding (768-dim)
        → global    = CLS token embedding (768-dim)  [Phase 2: section classifier]
        → fragment  = mean-pooled token embeddings (768-dim)
  ← EmbeddingResult { semantic, global, fragment }
→ stored as JSON columns in DB
```

### 3. Query Processing

```
User query text
  → POST /api/queries (QueryController)
    → QueryService.submitQuery()
      → persist MedicalQuery (PENDING)
      → async: processQueryAsync()
        → FastSRService.query()
          → POST http://ml:8081/query
            → PhcepEncoder.encode(queryText)
            → QueryEngine.answer()
              → fetch patient observations from backend
              → cosine_similarity(queryVec, recordVec) for each record
              → sort by score, take top-k
              → synthesise answer string
            ← QueryResult { answer, citations, confidence }
        if confidence ≥ 0.75:
          → MedicalQuery.status = AI_ANSWERED
        else:
          → MedicalQuery.status = HCP_NOTIFIED
          → LineNotificationService.notifyHcpNewQuery()
    ← 202 Accepted
```

### 4. HCP Answer Flow

```
HCP receives LINE push notification
  → visits HCP dashboard (/api/queries/hcp/pending)
  → PATCH /api/queries/hcp/{id}/answer
    → QueryService.hcpAnswer()
      → MedicalQuery.status = HCP_ANSWERED
      → LineNotificationService.notifyPatientAnswered()
```

### 5. FHIR Serialisation

```
HealthObservation (JPA entity)
  → FhirService.toFhirObservationJson()
    → HAPI FHIR R4 Observation resource
    → TW Core IG profile URL added to meta
    → Security tag: Confidentiality=R
    → Effective date (date-shifted)
  ← FHIR JSON stored in fhir_observation_json column
```

---

## Privacy Boundary

```
Real patient data (name, NHI ID, exact dates)
  → DeIdentificationService
    → pseudonymise (SHA-256 + secret seed)
    → shiftDate (±180 days, patient-specific)
    → redact direct identifiers
  → de-identified record stored in PostgreSQL
  → real identifier is NEVER persisted
```

---

## Longitudinal Context Accumulation

With each new observation, the patient's context vector space grows.
At query time, the QueryEngine searches the full history:

```
t=0   Lab: HbA1c 7.2%  → embedding stored
t=1   Lab: HbA1c 6.9%  → embedding stored
t=2   Symptom: fatigue → embedding stored
...
Query: "Is my diabetes improving?"
  → cosine search over all stored embeddings
  → top-k: HbA1c series  → synthesise trend answer
```
