# PHCEP — Personal Health Care Evidence-Based Medicine Platform

> **Author:** Dr. Chan-Lin Chu  
> **License:** MIT  
> **Status:** Framework / Prototype

---

## Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [System Architecture](#system-architecture)
4. [Module Breakdown](#module-breakdown)
5. [Technology Stack](#technology-stack)
6. [FastSR Integration](#fastsr-integration)
7. [FHIR / TW Core IG Compliance](#fhir--tw-core-ig-compliance)
8. [Privacy & De-identification](#privacy--de-identification)
9. [Integration Points](#integration-points)
10. [Roadmap](#roadmap)
11. [Getting Started](#getting-started)
12. [Local macOS Deployment (M2)](#local-macos-deployment-m2)
13. [Folder Structure](#folder-structure)

---

## Overview

PHCEP is a dynamic, longitudinal **Personal Health Care Evidence-Based Medicine Platform** that allows:

- **Healthcare Professionals (HCP)** to input and review EBM statements, clinical guidelines, ICD-10 codes, imaging findings, and lab references.
- **Patients/Users** to record personal health data (lab values, imaging reports, exam results) and pose medical queries.
- **AI/ML** (powered by the co-located **FastSR** few-shot semantic retrieval engine) to encode all data using semantic, global, and fragment-attention representations, and to synthesise answers from an individual's accumulated longitudinal context.

With time, the platform broadens its clinical coverage to align with Taiwan MOHW policies including:
- **TW Core IG** (Taiwan FHIR Implementation Guide)
- **Telemedicine Act** compliance
- **ICD-10-CM/PCS** coding
- **Long-term / Home Care** programmes
- National Health Insurance (NHI) interoperability

---

## Core Features

| Feature | Description |
|---|---|
| Longitudinal health records | Time-stamped personal data with de-identification |
| EBM knowledge base | Articles, PMID links, clinical guidelines |
| Semantic query engine | FastSR semantic + global + fragment-attention encoding |
| HCP notification queue | Unanswered queries flagged to HCP or platform owner |
| FHIR R4 / TW Core IG | Resources: Patient, Observation, DiagnosticReport, MedicationRequest |
| ICD-10 mapping | Diagnosis coding for queries and records |
| LINE Messaging integration | Notifications and query submission via LINE account |
| Edge device connectivity | Spring Boot REST API + MQTT for IoT/wearable data |
| Payment-ready hook | TON/Cocoon integration point (optional, skip at first launch) |
| GitHub-linked CI/CD | Automated build, test, and deploy via GitHub Actions |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PHCEP Platform                           │
│                                                                 │
│  ┌────────────┐   REST/FHIR    ┌─────────────────────────────┐ │
│  │  Frontend  │◄──────────────►│    Spring Boot Backend      │ │
│  │ (React/    │                │  ┌─────────┐ ┌──────────┐   │ │
│  │  Line Bot) │                │  │ FHIR R4 │ │  Query   │   │ │
│  └────────────┘                │  │ Service │ │ Service  │   │ │
│                                │  └────────-┘ └──────────┘   │ │
│  ┌────────────┐   gRPC/REST    │  ┌──────────────────────┐   │ │
│  │ Edge Devs  │◄──────────────►│  │  FastSR ML Bridge    │   │ │
│  │(IoT/Wear.) │                │  │ (Python microservice)│   │ │
│  └────────────┘                │  └──────────────────────┘   │ │
│                                │  ┌──────────────────────┐   │ │
│  ┌────────────┐                │  │   PostgreSQL + Redis  │   │ │
│  │ LINE Bot   │◄──────────────►│  │  (records + cache)   │   │ │
│  └────────────┘                │  └──────────────────────┘   │ │
│                                └─────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               FastSR (co-located module)                │   │
│  │  Semantic Encoder │ Global Context │ Fragment Attention  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Breakdown

### 1. `platform/backend/` — Spring Boot Application
- **QueryController** — accepts medical queries, routes to FastSR and/or HCP queue
- **PatientController** — manages de-identified patient records (FHIR Patient)
- **EbmController** — CRUD for EBM entries (article URL / PMID, ICD-10, statements)
- **NotificationController** — manages HCP notification queue
- **FhirService** — validates and translates records to/from FHIR R4 (TW Core IG)
- **FastSRService** — HTTP/gRPC bridge to Python ML microservice
- **DeIdentificationService** — strips / pseudonymises PII before persistence
- **LineNotificationService** — push notifications via LINE Messaging API

### 2. `platform/ml/` — Python ML Microservice
- **encoder.py** — wraps FastSR semantic / global / fragment encoders
- **query_engine.py** — retrieval pipeline; ranks candidate answers against user's longitudinal context
- **api.py** — FastAPI endpoint exposing `/encode` and `/query` routes

### 3. `platform/frontend/` — React Web App
- Patient health diary (input: lab, imaging, symptoms)
- EBM query form (with PMID / URL citation)
- HCP dashboard (notification queue, answer composer)
- Longitudinal timeline view

### 4. `docs/` — Documentation
- `architecture.md` — detailed system design
- `api-reference.md` — OpenAPI / REST endpoint catalogue
- `tw-core-ig-compliance.md` — FHIR mapping table to TW Core IG profiles
- `data-flow.md` — end-to-end data lifecycle
- `deployment.md` — Docker Compose, Kubernetes, cloud options
- `deployment-local-macos.md` — step-by-step guide for running PHCEP on macOS Apple Silicon (M2)

### 5. `docker/` — Container Configuration
- `docker-compose.yml` — full local stack
- `Dockerfile.backend` — Spring Boot image
- `Dockerfile.ml` — Python ML microservice image

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Spring Boot 3.x (Java 17) |
| ML microservice | Python 3.10+, FastAPI, PyTorch, HuggingFace |
| Frontend | React 18, Vite, Ant Design |
| Database | PostgreSQL 15 (records), Redis 7 (cache/session) |
| FHIR | HAPI FHIR R4, TW Core IG 0.2+ |
| Messaging | LINE Messaging API, MQTT (edge) |
| Containerisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Payment (optional) | TON / Cocoon SDK |

---

## FastSR Integration

PHCEP reuses the **FastSR** few-shot semantic retrieval engine (see `../FastSR/`) as a core intelligence module.

Each piece of data (query, lab value, EBM statement, imaging finding) is encoded with three complementary representations:

| Representation | Source module | Purpose |
|---|---|---|
| **Semantic** | FastSR `model.py` BiLSTM/BERT | Surface meaning of text |
| **Global context** | FastSR `section_model` | Position in clinical document |
| **Fragment attention** | FastSR attention layer | Key sub-phrase salience |

At query time, the `query_engine.py` retrieves the top-k most relevant records from the user's longitudinal context and synthesises a ranked response list with provenance citations (PMID, article URL, or source record date).

---

## FHIR / TW Core IG Compliance

PHCEP targets conformance with the **TW Core Implementation Guide** published by the Taiwan MOHW.

Key FHIR resource mappings:

| Clinical data | FHIR Resource | TW Core IG Profile |
|---|---|---|
| Patient demographics | `Patient` | TWCorePatient |
| Lab results | `Observation` | TWCoreObservationLaboratoryResult |
| Imaging | `ImagingStudy`, `DiagnosticReport` | TWCoreDiagnosticReport |
| Medications | `MedicationRequest` | TWCoreMedicationRequest |
| ICD-10 diagnosis | `Condition` | TWCoreCondition |
| Encounters / Telemedicine | `Encounter` | TWCoreEncounter |

Reference: https://twcore.mohw.gov.tw/ig/twcore/

---

## Privacy & De-identification

All personally identifiable information (PII) is processed through `DeIdentificationService` before database persistence:

- **Pseudonymisation:** patient name → deterministic UUID token
- **Date shifting:** dates shifted by a per-patient random offset (consistent within individual)
- **Structured suppression:** direct identifiers (NHI card number, phone, address) replaced with `[REDACTED]`
- **FHIR resource:** de-identified records stored as FHIR `Patient` with `meta.security` = `PSEUDONYMOUS`

---

## Integration Points

### LINE Messaging API
- Users can submit queries and receive answers via LINE
- HCPs receive push notifications for unanswered queue items
- Webhook endpoint: `POST /api/line/webhook`

### Edge Devices / IoT
- MQTT broker (Eclipse Mosquitto) accepts telemetry from wearables
- `EdgeDataIngestionService` normalises and maps readings to FHIR `Observation`

### GitHub Actions CI/CD
- On push to `main`: build backend → run tests → build ML image → deploy to staging
- See `.github/workflows/` for pipeline definitions

### TON / Cocoon (Payment — optional)
- `PaymentService` stub with TON SDK hook
- Skip at initial launch; enable by setting `payment.enabled=true` in `application.yml`

---

## Roadmap

### Phase 1 — MVP (months 1-3)
- [ ] Spring Boot REST API with patient record CRUD
- [ ] FastSR ML bridge (encode + query endpoints)
- [ ] Basic React frontend (query form + result list)
- [ ] PostgreSQL schema + liquibase migrations
- [ ] De-identification service
- [ ] Docker Compose local stack

### Phase 2 — FHIR & Integrations (months 4-6)
- [ ] HAPI FHIR R4 server integration
- [ ] TW Core IG profile validation
- [ ] LINE Messaging Bot
- [ ] ICD-10 code autocomplete
- [ ] HCP notification queue with email + LINE push

### Phase 3 — Compliance & Scale (months 7-12)
- [ ] Taiwan NHI API connector
- [ ] Telemedicine encounter workflow
- [ ] Long-term / home care care-plan module
- [ ] MQTT edge device ingestion
- [ ] Kubernetes deployment manifests
- [ ] TON/Cocoon payment module (optional)

---

## Getting Started

### Prerequisites
- Java 17+, Maven 3.9+
- Python 3.10+
- Docker & Docker Compose
- Node.js 18+

### Quick start (Docker Compose)
```bash
cd PHCEP/docker
cp ../platform/backend/src/main/resources/application.yml.example \
   ../platform/backend/src/main/resources/application.yml
# edit application.yml with your secrets
docker compose up --build
```

### Backend only (Spring Boot)
```bash
cd PHCEP/platform/backend
mvn spring-boot:run
# API available at http://localhost:8080
```

### ML microservice
```bash
cd PHCEP/platform/ml
pip install -r requirements.txt
uvicorn api:app --reload --port 8081
```

---

## Local macOS Deployment (M2)

Running PHCEP on a **MacBook Air/Pro with Apple Silicon (M2)** is the recommended zero-cost path for development and demos.  
A dedicated step-by-step guide covers both Docker Compose and non-Docker local dev, including:

- Docker Desktop settings for Apple Silicon (arm64 vs amd64 images, memory allocation)
- How to build and start the full stack with `docker compose up --build`
- Non-Docker path: backend (Java/Maven), ML service (Python venv + PyTorch on arm64), and frontend (Node/Vite)
- Required prerequisites and `.env` secrets setup (also handled by `scripts/setup.sh`)
- Where to access the UI, REST API, and health endpoints
- Common troubleshooting tips (port conflicts, PyTorch wheel issues, LINE webhook, etc.)

👉 **[docs/deployment-local-macos.md](docs/deployment-local-macos.md)**

---

## Folder Structure

```
PHCEP/
├── FastSR/                    # Few-shot semantic retrieval engine
├── platform/
│   ├── backend/               # Spring Boot application
│   │   ├── src/
│   │   │   ├── main/java/com/phcep/
│   │   │   │   ├── PhcepApplication.java
│   │   │   │   ├── config/
│   │   │   │   ├── controller/
│   │   │   │   ├── model/
│   │   │   │   ├── service/
│   │   │   │   └── repository/
│   │   │   └── main/resources/
│   │   └── pom.xml
│   ├── ml/                    # Python FastAPI + FastSR bridge
│   │   ├── encoder.py
│   │   ├── query_engine.py
│   │   ├── api.py
│   │   └── requirements.txt
│   └── frontend/              # React web app
│       ├── src/
│       └── package.json
├── docs/
│   ├── architecture.md
│   ├── api-reference.md
│   ├── tw-core-ig-compliance.md
│   ├── data-flow.md
│   ├── deployment.md
│   └── deployment-local-macos.md
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.ml
└── scripts/
    ├── setup.sh
    └── seed_data.py
```
