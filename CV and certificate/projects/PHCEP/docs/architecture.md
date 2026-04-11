# PHCEP Architecture

## Overview

PHCEP is a multi-tier, microservice-oriented platform. The core tiers are:

```
Browser / LINE Bot / Edge Device
       │
       ▼  HTTPS / REST
Spring Boot Backend (port 8080)
       │                    │
       ▼  HTTP/JSON          ▼  JDBC
Python ML Service       PostgreSQL + Redis
  (FastAPI, port 8081)
       │
       ▼  PyTorch
  FastSR Encoder
```

---

## Component Detail

### Spring Boot Backend

Package: `com.phcep`

| Package | Responsibility |
|---|---|
| `controller` | REST endpoints (QueryController, PatientController, EbmController, LineWebhookController) |
| `service` | Business logic (QueryService, PatientService, EbmService, FhirService, DeIdentificationService, FastSRService, LineNotificationService) |
| `model` | JPA entities (PatientRecord, MedicalQuery, EbmEntry, HealthObservation) |
| `repository` | Spring Data JPA repositories |
| `config` | Security (JWT), FHIR context, MQTT |

### Python ML Microservice

Files: `platform/ml/`

| File | Responsibility |
|---|---|
| `api.py` | FastAPI app with `/encode` and `/query` endpoints |
| `encoder.py` | PhcepEncoder — wraps FastSR tri-encoder (semantic, global, fragment) |
| `query_engine.py` | QueryEngine — cosine similarity retrieval + answer synthesis |

### Database Schema

```
patient_records         — pseudonymous patient profiles
medical_queries         — query lifecycle (PENDING → AI_ANSWERED / HCP_ANSWERED)
ebm_entries             — EBM knowledge base with embedding columns
health_observations     — longitudinal patient data (labs, vitals, imaging)
```

### Embeddings Storage

Three JSON columns per EbmEntry and HealthObservation:
- `semantic_embedding_json`
- `global_embedding_json`
- `fragment_embedding_json`

Phase 2 migration: replace JSON columns with `pgvector` `vector(768)` for native ANN search.

---

## Security Model

- JWT Bearer tokens for all authenticated endpoints
- Role-based: `PATIENT`, `HCP`, `ADMIN`
- De-identification pipeline runs on all patient data before persistence
- `meta.security = R (Restricted)` on all FHIR resources

---

## Data Flow: Query Submission

```
User types query (web / LINE)
  → POST /api/queries
    → QueryService.submitQuery()
      → save MedicalQuery (status=PENDING)
      → async: FastSRService.query() → ML /query endpoint
          → encoder.encode(queryText)
          → query_engine.answer() → cosine similarity on patient context
        if confidence ≥ 0.75:
          → status = AI_ANSWERED, aiAnswer = synthesised text
        else:
          → status = HCP_NOTIFIED
          → LineNotificationService.notifyHcpNewQuery()
  ← return MedicalQuery (accepted/202)
```
