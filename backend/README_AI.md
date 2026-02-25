# AI Clinical Copilot & Intelligence Layer

This module adds advanced AI capabilities to the Clinical Documentation System, powered by Groq.

## Features

### 1. Clinical Risk Detection Module (Async)
- **Trigger**: Automatically runs when a note is saved.
- **Analysis**:
  - Risk Score (High/Medium/Low)
  - Red Flags (Contraindications, harmful interactions)
  - Missing Documentation Suggestions
  - Clinical Recommendations
- **Storage**: Results are stored in `clinical_ai_insights` table.
- **Access**: Available in Note Response under `ai_insights`.

### 2. Differential Diagnosis Generator
- **Endpoint**: `POST /api/v1/ai/differential`
- **Input**: Symptoms, Vitals, Labs, Age, Gender
- **Output**: Top 5 differentials with reasoning, suggested tests, and confidence levels.
- **Storage**: Results are logged in `differential_diagnoses` table.

### 3. Medico-Legal Guard
- **Endpoint**: `POST /api/v1/ai/medico_legal` (Ad-hoc)
- **Analysis**: Checks for completeness, consent documentation, and legal defensibility.
- **Integration**: Also runs as part of the async risk detection on note save.

### 4. Real-Time Copilot Mode
- **Endpoint**: `WS /ws/copilot`
- **Function**: Streams real-time suggestions to the doctor while typing.
- **Protocol**: WebSocket (send partial text -> receive JSON suggestions).

## Setup

1. **Database Migration**:
   Run the following command to create the necessary tables:
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add ClinicalAIInsight and DifferentialDiagnosis tables"
   alembic upgrade head
   ```

2. **Environment Variables**:
   Ensure `GROQ_API_KEY` is set in your `.env` file.

## Usage

### Differential Diagnosis
```json
POST /api/v1/ai/differential
{
  "symptoms": ["chest pain", "shortness of breath"],
  "age": 55,
  "gender": "Male",
  "vitals": {"bp": "150/90", "hr": 110}
}
```

### Risk Analysis (Ad-hoc)
```json
POST /api/v1/ai/risk_analysis
{
  "note_content": "Patient reports severe headache...",
  "patient_history": "Hypertension"
}
```

### Copilot WebSocket
Connect to `ws://localhost:8000/ws/copilot`.
Send text: `"Patient reports severe ches"`
Receive JSON:
```json
{
  "suggestions": ["Consider ruling out ACS"],
  "warnings": [],
  "disclaimer": "AI-generated suggestion..."
}
```
