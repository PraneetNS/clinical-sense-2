# Clinical Sense — AI Clinical Intelligence Platform

> **A production-ready, AI-powered clinical documentation and patient management system** built for medical professionals. Combines parallel AI pipelines, deterministic safety engines, and a modern clinical workflow UI.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Data Isolation & Security](#data-isolation--security)
- [AI Intelligence Engine](#ai-intelligence-engine)
- [Clinical Expansion Layer](#clinical-expansion-layer)
- [Disclaimer](#disclaimer)

---

## Overview

Clinical Sense is a full-stack clinical documentation assistant that helps doctors and nurses:

- **Manage patients** — create, view, update, and delete patient records with per-account data isolation
- **Write and structure clinical notes** — AI converts raw dictation into structured SOAP notes
- **Generate full AI encounters** — 8 parallel AI pipelines produce medications, diagnoses, billing codes, risk assessments, legal flags, and follow-up recommendations from a single raw note
- **Confirm & commit AI data** — all AI output is staged first; clinicians review and confirm before it enters permanent records
- **Track clinical timelines** — every event (notes, meds, procedures, admissions, tasks) appears on a unified timeline
- **Generate PDF reports** — complete patient summaries with AI encounter history

---

## Key Features

### 🧠 AI Intelligence Engine
| Feature | Description |
|---|---|
| **Parallel AI Orchestrator** | 8 AI pipelines run simultaneously via `asyncio.gather` — SOAP, Medications, Diagnoses (ICD-10), Billing (CPT), Risk Analysis, Legal Flags, Case Intelligence, Quality Evaluator |
| **AI Encounter Generation** | One raw clinical note → full structured encounter in under 4 seconds |
| **Encounter Confirmation** | All AI content is staged; `confirm` promotes it to permanent records (Medications, Procedures, Billing, Tasks, Medical History) |
| **SOAP Note Structuring** | Converts free-text notes into Subjective / Objective / Assessment / Plan format |
| **AI Risk Analysis** | Scores risk level (Low/Medium/High), identifies red flags and missing clinical info |
| **Idempotency** | Duplicate note creation is blocked via `idempotency_key` |

### 🛡️ Clinical Expansion Layer (Deterministic — No Hallucinations)
| Module | Description |
|---|---|
| **Drug Safety Engine** | Evaluates DDIs, allergy contraindications, renal dosing (Metformin/eGFR), cardiac safety |
| **Lab Interpreter** | Parses SOAP text, identifies lab values, flags critical & abnormal results |
| **Risk Calculators** | Hard-coded BMI, polypharmacy (≥5 meds), readmission risk, fall risk scoring |
| **Guideline Validator** | Rule-based checks for hypertension, diabetes, preventive screening compliance |
| **Explainability Engine** | Generates evidence-grounded rationale for AI recommendations (Evidence Mode) |
| **Differential Assistant** | Suggests alternative diagnoses with confidence scores |
| **SBAR Handoff Generator** | Fully formatted Situation-Background-Assessment-Recommendation handoffs |
| **Workflow Automation Engine** | Stages follow-up tasks from encounter recommendations |
| **Bias Monitor** | Tracks AI output drift, acceptance rates, and demographic-level consistency |

### 🏥 Patient Management
- Full CRUD with **soft-delete** (records are never physically removed)
- **Per-account data isolation** — each clinician's patients/notes are private
- **Fast list endpoint** (`/patients/list`) — no relationship loading, returns in milliseconds
- Patient status (`Active` / `Closed`) with case locking
- Billing totals computed on-the-fly with outstanding amounts

### 📝 Clinical Records
- Medical History, Allergies, Medications, Procedures, Documents, Admissions
- Tasks with priority, category, due dates, auto-generation from AI
- Billing Items with CPT codes and payment status
- Semantic search across notes using vector embeddings

### 📊 Admin & Governance
- **AI Analytics Dashboard** — confidence scores, latency metrics, acceptance rates
- **Bias & Drift Report** — per-model fairness monitoring
- **Quality Reports** — per-encounter hallucination flags, compliance scores, risk levels
- **Audit Logs** — every create/update/delete action is logged with user ID and timestamp

### 🔒 Security
- **Firebase Authentication** — all requests require a valid Firebase JWT
- **Rate Limiting** — 5/min for AI creation, 20/min for reads, 60/min for single resource fetch
- **Security Headers** — `X-Content-Type-Options`, `X-Frame-Options`
- **Request ID tracing** — every request gets a UUID for log correlation
- **Payload size limit** — 10MB max on POST requests
- **HIPAA-conscious design** — PHI not logged, audit trails maintained

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  Login → Dashboard → Patients → Patient Detail → Encounter      │
│  Notes → Admin Governance → Landing Page                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS REST + WebSocket
┌──────────────────────────▼──────────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐│
│  │  Auth Layer  │  │  Rate Limiter│  │  Request ID Middleware  ││
│  │  (Firebase)  │  │  (SlowAPI)   │  │  + Security Headers     ││
│  └─────────────┘  └──────────────┘  └─────────────────────────┘│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                     API Routers (v1)                         ││
│  │  /auth  /patients  /notes  /clinical  /ai  /workflow        ││
│  │  /hospital  /communication  /hos  /admin  /copilot          ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │             Clinical Intelligence Orchestrator              ││
│  │                                                             ││
│  │  Raw Note ──▶ asyncio.gather([                              ││
│  │                 ENCOUNTER_EXTRACTOR,                        ││
│  │                 SOAP_GENERATOR,                             ││
│  │                 MEDICATION_STRUCTURING,                     ││
│  │                 DIAGNOSIS_CODING (ICD-10),                  ││
│  │                 BILLING_INTELLIGENCE (CPT),                 ││
│  │                 CASE_INTELLIGENCE,                          ││
│  │                 RISK_ANALYSIS,                              ││
│  │                 MEDICO_LEGAL                                ││
│  │               ]) ──▶ Merge ──▶ Quality Evaluator           ││
│  │                        │                                    ││
│  │                        ▼ (if Evidence Mode ON)              ││
│  │              Clinical Expansion Layer:                      ││
│  │              Drug Safety, Lab Interpreter,                  ││
│  │              Risk Calculators, Guidelines,                  ││
│  │              Explainability, Differentials, SBAR            ││
│  │                        │                                    ││
│  │                        ▼                                    ││
│  │              Persist → AIEncounter (staging table)          ││
│  │              Clinician confirms → Permanent records         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │   Patient Service    │  │       Note Service               │ │
│  │  - Per-user isolation│  │  - Per-user isolation            │ │
│  │  - Soft delete       │  │  - Semantic search (embeddings)  │ │
│  │  - Fast list endpoint│  │  - AI risk analysis (background) │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│           PostgreSQL (Supabase) + Firebase Auth                  │
│                                                                  │
│  Tables: users, patients, clinical_notes, ai_encounters,        │
│  ai_generated_medications, ai_generated_diagnoses,              │
│  ai_generated_billing, ai_quality_reports, ai_usage_metrics,    │
│  medications, procedures, medical_history, allergies,           │
│  admissions, documents, tasks, billing_items, audit_logs,       │
│  clinical_trajectories, discharge_readiness, note_versions,     │
│  secure_messages, patient_communications, shift_handovers,      │
│  readmission_risks, clinical_ai_insights                        │
└─────────────────────────────────────────────────────────────────┘
```

### Intelligence Data Flow

```
Raw Clinical Note
       │
       ▼
  [8 Parallel AI Pipelines] ──── Groq (LLaMA 3.3 70B)
       │
       ▼
  [Merge & Deduplicate]
       │
       ├──▶ [Deterministic Clinical Rules Engine] (fast, in-process)
       │
       ├──▶ [AI Quality Evaluator] (confidence score, compliance, risk level)
       │
       └──▶ [Clinical Expansion: Drug Safety, Labs, Risk, Guidelines]  (Evidence Mode)
                          │
                          ▼
              [AIEncounter Staging Table]  ← reviewable by clinician
                          │
              Clinician clicks "Confirm"
                          │
                          ▼
              Permanent Clinical Records:
              Medications, Procedures, Diagnoses,
              Billing Items, Tasks, Clinical Note
```

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | Async REST API framework |
| **SQLAlchemy** | ORM for PostgreSQL |
| **Alembic** | Database migrations |
| **PostgreSQL (Supabase)** | Primary database, hosted |
| **Firebase Admin SDK** | JWT token verification & auth |
| **Groq API (LLaMA 3.3 70B)** | AI inference for all pipelines |
| **SlowAPI** | Rate limiting middleware |
| **ReportLab** | PDF report generation |
| **Pydantic v2** | Data validation & settings management |
| **sentence-transformers** | Embedding generation for semantic search |
| **Uvicorn** | ASGI server |

### Frontend
| Technology | Purpose |
|---|---|
| **Next.js 14** (App Router) | React framework with SSR support |
| **TypeScript** | Type safety across components |
| **Tailwind CSS** | Utility-first styling |
| **Axios** | HTTP client with auth interceptors |
| **Lucide React** | Icon library |
| **Firebase JS SDK** | Client-side authentication |

---

## Project Structure

```
clinical-sense/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                    # Auth dependencies (Firebase token verify)
│   │   │   └── endpoints/
│   │   │       ├── auth.py                # Register / login / me
│   │   │       ├── patients.py            # Patient CRUD, fast list, delete
│   │   │       ├── notes.py               # Clinical note CRUD + SOAP structuring
│   │   │       ├── clinical.py            # Medications, allergies, admissions, procedures, docs, tasks, billing
│   │   │       ├── encounter.py           # AI encounter generate, list, get, confirm (WebSocket)
│   │   │       ├── ai.py                  # Differential, risk analysis, medico-legal endpoints
│   │   │       ├── workflow.py            # Trajectory, discharge, workflow dashboard
│   │   │       ├── hospital.py            # Secure messages, shift handovers, readmission risk
│   │   │       ├── communication.py       # Patient communication summaries
│   │   │       ├── admin.py               # AI analytics, bias report (admin only)
│   │   │       ├── hos.py                 # Hospital OS batch endpoints
│   │   │       ├── copilot.py             # Copilot assistant endpoint
│   │   │       └── tasks.py               # Task management
│   │   ├── core/
│   │   │   ├── config.py                  # Pydantic settings (env vars, prod validation)
│   │   │   ├── logging.py                 # Structured JSON logger + request context
│   │   │   ├── ratelimit.py               # SlowAPI rate limiter instance
│   │   │   ├── exceptions.py              # Custom AppError + handlers
│   │   │   └── pdf_gen.py                 # ReportLab PDF generation
│   │   ├── db/
│   │   │   └── session.py                 # SQLAlchemy engine, SessionLocal, get_db
│   │   ├── models.py                      # All SQLAlchemy ORM models (30+ tables)
│   │   ├── schemas/                       # Pydantic schemas (request/response)
│   │   │   ├── patient.py                 # PatientCreate/Response/Minimal/Delete
│   │   │   ├── notes.py                   # NoteCreate/Response/Update
│   │   │   ├── clinical.py                # All clinical sub-schemas
│   │   │   ├── encounter.py               # EncounterRequest/Response + AI sub-schemas
│   │   │   └── hospital.py                # SecureMessage, Handover, Risk schemas
│   │   ├── services/
│   │   │   ├── patient_service.py         # Patient CRUD, soft-delete, fast list, timeline
│   │   │   ├── clinical_service.py        # Clinical sub-record CRUD
│   │   │   ├── clinical_intelligence.py   # 8-pipeline AI orchestrator + confirm logic
│   │   │   ├── clinical_rules.py          # Deterministic safety rules engine
│   │   │   ├── embedding_service.py       # Sentence embed for semantic search
│   │   │   ├── safety_service.py          # Content safety / PII filter
│   │   │   ├── ai/
│   │   │   │   ├── ai_service.py          # Groq client + prompt dispatcher
│   │   │   │   └── prompts.py             # All 10+ prompt templates (SOAP, Meds, etc.)
│   │   │   ├── notes/
│   │   │   │   └── note_service.py        # Note CRUD, semantic search, risk analysis
│   │   │   ├── clinical/
│   │   │   │   └── workflow_service.py    # Trajectory, discharge, patient summary
│   │   │   └── clinical_expansion/
│   │   │       ├── drug_safety.py         # DDI + allergy + renal dosing checks
│   │   │       ├── lab_interpreter.py     # Lab value parsing + flagging
│   │   │       ├── risk_calculators.py    # BMI, polypharmacy, readmission, fall risk
│   │   │       ├── guideline_validator.py # Hypertension / diabetes / preventive rules
│   │   │       ├── explainability.py      # AI rationale generation (LLM-powered)
│   │   │       ├── differential_assistant.py # Alternative diagnoses with confidence
│   │   │       ├── handoff.py             # SBAR handoff generation
│   │   │       ├── workflow_engine.py     # Task staging from encounter recommendations
│   │   │       └── bias_monitor.py        # Model equity and drift tracking
│   │   └── main.py                        # FastAPI app, middleware stack, router mounting
│   ├── .env                               # Environment variables (not committed)
│   ├── requirements.txt
│   └── alembic/                           # Database migration history
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                   # Landing page (marketing)
│   │   │   ├── layout.tsx                 # Root layout + Toast provider
│   │   │   ├── login/page.tsx             # Firebase sign-in
│   │   │   ├── register/page.tsx          # Firebase sign-up
│   │   │   ├── dashboard/page.tsx         # Clinical overview dashboard
│   │   │   ├── patients/
│   │   │   │   ├── page.tsx               # Patient list (fast endpoint, delete, search)
│   │   │   │   ├── new/page.tsx           # Create patient form
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx           # Patient detail (10 tabs, timeline, delete)
│   │   │   │       └── encounter/page.tsx # AI encounter generation + confirmation UI
│   │   │   ├── notes/
│   │   │   │   ├── page.tsx               # Notes list
│   │   │   │   └── new/page.tsx           # New note + SOAP structuring
│   │   │   └── admin/page.tsx             # Governance dashboard (admin only)
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── Modal.tsx              # Reusable modal wrapper
│   │   │   │   └── Toast.tsx              # Toast notification system
│   │   │   ├── WorkflowDashboard.tsx      # Trajectory + discharge widget
│   │   │   ├── landing/                   # Landing page sections
│   │   │   └── forms/                     # Medication, Procedure, Task, Billing, etc.
│   │   ├── context/
│   │   │   └── AuthContext.tsx            # Firebase auth state + token refresh
│   │   └── lib/
│   │       └── api.ts                     # Axios instance + all API method groups
│   └── .env.local                         # Frontend env vars
│
├── seed_initial_user.py                   # Creates first admin user
├── create_all_tables.py                   # Manual table creation script
├── migrate_*.py                           # One-off migration scripts
└── README.md
```

---

## API Reference

All endpoints require `Authorization: Bearer <firebase_token>` header unless noted.

### Patients (`/api/v1/patients`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/patients/list` | **Fast list** — minimal fields, no relationships, filters by owner |
| `GET` | `/patients/` | Full list with relationships (slower) |
| `POST` | `/patients/` | Create a new patient |
| `GET` | `/patients/{id}` | Get patient with all clinical data |
| `PATCH` | `/patients/{id}` | Update patient fields |
| `DELETE` | `/patients/{id}` | Soft-delete patient (owner only) |
| `GET` | `/patients/{id}/timeline` | Unified chronological event timeline |
| `GET` | `/patients/{id}/notes` | All clinical notes for patient |
| `GET` | `/patients/{id}/report` | Full AI clinical report |
| `GET` | `/patients/{id}/report/pdf` | Download PDF report |

### Notes (`/api/v1/notes`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/notes/structure` | Create + AI-structure a clinical note |
| `GET` | `/notes/` | List user's notes (search supported) |
| `GET` | `/notes/{id}` | Get single note |
| `PUT` | `/notes/{id}` | Update note content |
| `DELETE` | `/notes/{id}` | Soft-delete note |
| `GET` | `/notes/{id}/history` | Version history of note edits |

### Clinical Data (`/api/v1/patients/{id}/...`)

| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/{id}/history` | Medical history conditions |
| `GET/POST` | `/{id}/medications` | Medications |
| `GET/POST` | `/{id}/allergies` | Allergies |
| `GET/POST` | `/{id}/admissions` | Hospital admissions |
| `GET/POST` | `/{id}/procedures` | Procedures |
| `GET/POST` | `/{id}/documents` | Documents / file uploads |
| `GET/POST` | `/{id}/tasks` | Clinical tasks |
| `GET/POST` | `/{id}/billing` | Billing items |

### AI Encounters (`/api/v1/ai`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/ai/generate_full_encounter` | Trigger 8-pipeline encounter generation |
| `GET` | `/ai/encounters/{patient_id}` | List encounters for patient |
| `GET` | `/ai/encounter/{id}` | Get specific encounter |
| `GET` | `/ai/encounter/{id}/quality-report` | Confidence + compliance report |
| `POST` | `/ai/encounter/{id}/confirm` | Promote AI data to permanent records |
| `WS` | `/ai/encounter/ws/{id}` | WebSocket for real-time encounter stream |

### Workflow (`/api/v1/workflow`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/workflow/notes/{id}/analyze` | Trigger trajectory + summary + task extraction |
| `POST` | `/workflow/patients/{id}/trajectory-check` | Patient-level trajectory analysis |
| `POST` | `/workflow/patients/{id}/discharge-check` | Discharge readiness evaluation |
| `GET` | `/workflow/patients/{id}/workflow-dashboard` | Aggregated workflow status |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | API status + version |
| `GET` | `/api/health/db` | Database connectivity check |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Supabase PostgreSQL database
- A Firebase project (for authentication)
- A Groq API key

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy and fill in values)
cp ../.env.example .env

# Run database migrations
python -m alembic upgrade head

# Create initial admin user
python ../seed_initial_user.py

# Start development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8091 --reload
```

Server runs at: `http://127.0.0.1:8091`  
Health check: `http://127.0.0.1:8091/api/health`  
API Docs (dev only): `http://127.0.0.1:8091/api/v1/docs`

### Frontend Setup

```bash
cd frontend
npm install

# Configure environment
# Set NEXT_PUBLIC_API_URL=http://localhost:8091/api/v1 in .env.local

npm run dev -- --port 3006
```

App runs at: `http://localhost:3006`

---

## Environment Variables

### Backend (`.env`)

```env
ENV=development
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require
SUPABASE_DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require
SUPABASE_SERVICE_ROLE_KEY=sb_publishable_...

FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-...@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service_account.json

GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

FRONTEND_URL=http://localhost:3006
BACKEND_CORS_ORIGINS=["http://localhost:3006","http://127.0.0.1:3006"]
```

### Frontend (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8091/api/v1

NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abc123
```

---

## Data Isolation & Security

Each user account has **fully isolated data**:

| Data Type | Isolation Rule |
|---|---|
| **Patients** | Only the creating clinician can list, view, update, or delete their patients |
| **Clinical Notes** | Only the note author can view or edit their notes |
| **Clinical Records** | All sub-records (meds, tasks, billing, etc.) are tied to their parent patient, which is user-scoped |
| **AI Encounters** | Scoped to the patient, which is user-scoped |
| **Delete** | Soft-delete only — `is_deleted = True`, `deleted_at` timestamp set; records never physically removed |
| **Authentication** | Every API request validates a Firebase JWT; no open endpoints except `/health` |

---

## AI Intelligence Engine

### Prompts & Pipelines

All AI prompts are defined in `backend/app/services/ai/prompts.py` and dispatched through `ai_service.run_hospital_agent(prompt_key, context)`:

| Prompt Key | Purpose | Output |
|---|---|---|
| `SOAP` | Structures note into SOAP format | `{subjective, objective, assessment, plan}` |
| `ENCOUNTER_EXTRACTOR` | Extracts encounter metadata | Chief complaint, procedures, timeline events |
| `MEDICATION_STRUCTURING` | Extracts and structures medications | Name, dosage, frequency, route, duration, flags |
| `DIAGNOSIS_CODING` | ICD-10 coding from symptoms | Diagnoses with codes, confidence, reasoning |
| `BILLING_INTELLIGENCE` | CPT code generation | Billing items with estimated costs, review flags |
| `CASE_INTELLIGENCE` | Case management analysis | Admission/ICU needs, follow-up days, risk score |
| `RISK_ANALYSIS` | Patient risk stratification | Risk level, red flags, missing info |
| `MEDICO_LEGAL` | Legal risk identification | Legal flags, liability concerns |
| `QUALITY_EVALUATOR` | AI output quality scoring | Confidence score, compliance, hallucination flags |
| `TRAJECTORY` | Clinical trajectory analysis | Trend, risk score, key changes |
| `PATIENT_SUMMARY` | Patient-friendly note summary | Plain language explanation |
| `AUTOMATION` | Task extraction | Clinical tasks with priority and category |

### AI Governance

Every encounter generates an `AIQualityReport` with:
- `confidence_score` — overall output confidence (0–1)
- `compliance_score` — documentation standard compliance (0–1)
- `risk_level` — LOW / MEDIUM / HIGH
- `hallucination_flags` — detected factual inconsistencies
- `missing_critical_fields` — incomplete documentation alerts
- `clinical_safety_flags` — from deterministic rule engine

---

## Clinical Expansion Layer

The expansion layer runs alongside AI pipelines and adds **deterministic validation** that cannot hallucinate:

### Drug Safety Engine
- Checks 20+ known drug-drug interactions (Warfarin+NSAIDs, ACE+Potassium, etc.)
- Validates allergy contraindications against current medication list
- Flags Metformin use when renal context suggests low eGFR
- Detects polypharmacy risk (≥5 concurrent medications)

### Lab Interpreter
- Parses numeric lab values from SOAP text via regex
- Compares against standard ranges (e.g. Hemoglobin < 7 = Critical)
- Flags CRITICAL / ABNORMAL / NORMAL with clinical context

### Risk Calculators
- **BMI** — underweight/overweight/obese classification
- **Polypharmacy** — counts active meds, flags if ≥5
- **Fall Risk** — age + anticoagulant + mobility scoring
- **Readmission Risk** — comorbidity + prior admission assessment

### Guideline Validator
- HTN: Flags BP readings ≥ 130/80, validates ACE/ARB/CCB use
- Diabetes: Checks HbA1c monitoring and Metformin documentation
- Preventive: Annual flu vaccine, lipid panel, colorectal screening reminders

---

## Sample Encounter Inputs

Try these in the **Generate Full Encounter** screen:

**Geriatric Diabetes + Hypertension:**
> "72-year-old male with HTN and T2D for follow-up. BP today 155/92. Reports occasional palpitations. Meds: Lisinopril 20mg daily, Metformin 1000mg BID. Plan: Increase Lisinopril to 40mg, check renal panel in 2 weeks. Follow up in 3 months."

**High-Risk Polypharmacy + Fall:**
> "Alice, 82F, 3 days post-CHF hospitalization. On 12 medications including Warfarin 5mg, Lorazepam 1mg, Furosemide 40mg. Reports dizziness on standing, unsteady gait. Lives alone. INR not checked since discharge."

**Pediatric Urgent:**
> "8-year-old male, well-child visit. Fever 38.9°C for 3 days. Throat erythematous, tonsils 2+, no exudate. Rapid strep negative. No antibiotics given. Plan: symptomatic and return if worsens. Vaccines up to date."

---

## Disclaimer

> **Clinical Sense is strictly an assistive tool.** It does NOT provide medical advice or diagnoses. All AI-generated content is staged for review and **must be confirmed by a licensed clinician** before inclusion in the permanent medical record. The system is designed to reduce documentation burden, not replace clinical judgment.

---

**License**: Proprietary — All rights reserved.  
**Version**: 2.0 (March 2026)
