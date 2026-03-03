# Clinical Sense v2: Deterministic AI Clinical Intelligence Platform

A secure, production-ready AI-powered clinical documentation system built with FastAPI and Next.js. **Clinical Sense v2** is expanded with robust governance, deterministic safety guardrails, and explainable AI modules.

## 🚀 Key Features (v2)

### 🧠 Intelligence Engine
- **Parallel Intelligence Orchestrator**: Executes 6+ AI pipelines simultaneously (SOAP, Meds, Billing, Risk, Legal, Coding) for <4s encounter generation.
- **Evidence Mode & Explainability**: Justifies AI outputs using direct quote snippets and source evidence from the original clinical note.
- **Assistive Differential Diagnosis**: Suggests alternative diagnoses for clinician consideration with built-in confidence scoring.
- **SBAR Handoff Generation**: Automatically assembles Situation-Background-Assessment-Recommendation handoffs.

### 🛡️ Clinical Expansion Layer (Deterministic & Safe)
- **Deterministic Drug Safety Engine**: Evaluates drug-drug interactions, allergies, and contraindications (e.g. Metformin vs eGFR) without AI hallucination risk.
- **Lab Interpreter**: Automatically analyzes lab results against standard ranges and flags critical values.
- **Structured Risk Calculators**: Hard-coded logic for BMI, Polypharmacy risk, Readmission risk, and Fall risk.
- **Guideline Validator**: Rule-based screening for hypertension, diabetes, and preventive care guidelines.
- **Bias & Drift Monitor**: Tracks model performance and identifies potential bias in AI extractions across patient demographics.

### 📊 Governance & Admin
- **AI Governance Dashboard**: Real-time Super Admin monitoring of model performance, confidence drift, and operational safety metrics.
- **Patient Timeline**: Complete longitudinal tracking of all clinical events and interventions.
- **PDF Report Generation**: Securely generates patient activity and encounter reports.

---

## 🏗️ Architecture: The "Intelligence + Governance" Model

Clinical Sense v2 shifts from a pure generative architecture to an **Intelligence + Governance** model. AI agents extract and structure, while the **Clinical Expansion Layer** validates and calculates risks deterministically.

**Flow of Intelligence:**
1. **Raw Note** → 2. **Parallel Agentic Pipelines** → 3. **Clinical Expansion Layer** (Safety & Risks) → 4. **AI Quality Evaluator** → 5. **Staging Table** → 6. **Clinician Confirmation** → 7. **Permanent Record**.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python), PostgreSQL, SQLAlchemy ORM, Alembic, JWT & Firebase Auth, Groq AI (LLaMA inference).
- **Frontend**: Next.js 14 (App Router), React TypeScript, Tailwind CSS, Lucide Icons, Framer Motion.

---

## ⚡ Quick Start (Development)

### Prerequisites
- Python 3.9+ | Node.js 18+ | PostgreSQL

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Database setup
python -m alembic upgrade head
python ../seed_initial_user.py # Create a root user

# Start server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --reload
```
*Available at: `http://127.0.0.1:8090` (Health: `/health`)*

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Available at: `http://localhost:3005`*

---

## 🧪 Sample Encounter Inputs (Try these!)

Paste these into the "New Encounter" text area to see the intelligence engine in action:

**Sample A: Geriatric Follow-up**
> "72-year-old male for follow-up of Hypertension and Type 2 Diabetes. BP today 155/92. Patient reports skip-beats. Meds: Lisinopril 20mg, Metformin 1000mg BID. Plan: Increase Lisinopril to 40mg. Follow up 3 months."

**Sample B: High Risk (Fall/Polypharmacy)**
> "Alice (82F) post-hospitalization for CHF. Taking 12 meds including Warfarin, Lorazepam, and Furosemide. Reports dizziness on standing. Lives alone. History of gait instability."

---

## 📁 Project Structure

```text
clinical-sense-2/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/         # Encounter WS, Admin Governance, Patient API
│   │   ├── services/
│   │   │   ├── ai/                # Prompt Registry & Groq Service
│   │   │   ├── clinical_intelligence.py  # Parallel Orchestrator
│   │   │   └── clinical_expansion/# Deterministic engines (Safety, Lab, Risk)
│   │   └── models.py              # Staging table & AIQualityReport
├── frontend/
│   ├── src/app/
│   │   ├── admin/                 # Governance & Monitoring
│   │   ├── patients/[id]/         # Encounter & Timeline UI
│   │   └── dashboard/             # Clinical overview
└── README.md
```

---

## ⚖️ Disclaimer
*Clinical Sense v2 is strictly an assistive tool. It does NOT provide medical advice or diagnoses. All AI-generated content must be reviewed and confirmed by a licensed clinician before inclusion in the permanent medical record.*

---
**License**: Proprietary - All rights reserved.
