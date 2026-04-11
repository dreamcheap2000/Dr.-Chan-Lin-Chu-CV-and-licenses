# PHCEP API Reference

Base URL: `http://localhost:8080`

## Authentication

All endpoints (except `/api/auth/**`, `/api/line/webhook`, `/actuator/health`) require:
```
Authorization: Bearer <JWT>
```

---

## Auth

### POST /api/auth/login
Request: `{ "username": "string", "password": "string" }`
Response: `{ "token": "string", "role": "string" }`

---

## Queries

### POST /api/queries
Submit a medical query.

Request:
```json
{
  "queryText": "What does an HbA1c of 7.2% indicate?",
  "icd10Code": "E11"
}
```
Response: `MedicalQuery` (status 202)

### GET /api/queries/{id}
Get query + answer for the current user.

### GET /api/queries/my
List all queries for the current authenticated user.

### GET /api/queries/hcp/pending  _(HCP role required)_
List pending queries awaiting HCP review.

### PATCH /api/queries/hcp/{id}/answer  _(HCP role required)_
```json
{
  "answer": "HbA1c 7.2% indicates ...",
  "citations": "PMID:12345678; https://..."
}
```

---

## Patient Records

### POST /api/patient/observations
Record a health observation.
```json
{
  "observationType": "LAB",
  "loincCode": "4548-4",
  "observationText": "HbA1c result",
  "numericValue": 7.2,
  "unit": "%",
  "referenceRangeLow": 4.0,
  "referenceRangeHigh": 5.6,
  "effectiveDateTime": "2024-06-01T08:00:00"
}
```

### GET /api/patient/observations
List observations. Optional query params: `from` (ISO date), `to` (ISO date).

### GET /api/patient/observations/timeline
All observations ordered chronologically.

---

## EBM Knowledge Base

### POST /api/ebm  _(HCP or Admin required)_
Add a new EBM entry.
```json
{
  "statement": "Metformin is first-line therapy for type 2 diabetes.",
  "pmid": "28214667",
  "articleUrl": "https://pubmed.ncbi.nlm.nih.gov/28214667/",
  "icd10Codes": "E11",
  "specialty": "Endocrinology"
}
```

### GET /api/ebm/{id}
Get EBM entry by ID.

### GET /api/ebm/search?q=&limit=
Full-text search (PostgreSQL `tsvector`).

### GET /api/ebm/semantic-search?q=&topK=
Semantic search via FastSR embedding similarity.

### DELETE /api/ebm/{id}  _(Admin required)_

---

## LINE Webhook

### POST /api/line/webhook
Receives LINE message events. Signature validated by LINE SDK.
Body: LINE Messaging API event payload.

---

## ML Microservice (port 8081)

### POST /encode
```json
{ "text": "string" }
```
Response: `{ "semantic": [...], "global_ctx": [...], "fragment": [...] }`

### POST /query
```json
{
  "pseudonymous_token": "string",
  "query_text": "string",
  "top_k": 5
}
```
Response: `{ "answer": "string", "citations": "string", "confidence": 0.85 }`

### GET /health
Response: `{ "status": "ok" }`
