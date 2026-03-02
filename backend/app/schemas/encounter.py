"""
Pydantic schemas for the Clinical Intelligence Platform encounter system.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class EncounterRequest(BaseModel):
    patient_id: int = Field(..., description="ID of the patient")
    raw_note: str = Field(..., min_length=10, max_length=50_000, description="Raw clinical note text")
    encounter_date: Optional[datetime] = Field(None, description="ISO datetime of the encounter")

    @field_validator("raw_note")
    @classmethod
    def strip_note(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# Child output schemas (read-only — what comes back from AI)
# ---------------------------------------------------------------------------

class AIMedicationOut(BaseModel):
    id: int
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    duration: Optional[str] = None
    start_date_text: Optional[str] = None
    requires_confirmation: bool = False
    fields_required: List[str] = []   # Fields the doctor must fill in
    confidence: str = "medium"         # high / medium / low

    model_config = {"from_attributes": True}


class AIDiagnosisOut(BaseModel):
    id: int
    condition_name: str
    icd10_code: Optional[str] = None
    confidence_score: float = 0.5
    reasoning: Optional[str] = None
    is_primary: bool = False

    model_config = {"from_attributes": True}


class AIProcedureOut(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    notes: Optional[str] = None
    confidence: str = "medium"

    model_config = {"from_attributes": True}


class AIBillingOut(BaseModel):
    id: int
    cpt_code: Optional[str] = None
    description: str
    estimated_cost: Optional[float] = None
    complexity: str = "medium"
    confidence: float = 0.5
    requires_review: bool = True
    review_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class AITimelineEventOut(BaseModel):
    id: int
    event_type: str
    event_description: str
    event_date_text: Optional[str] = None
    severity: str = "info"

    model_config = {"from_attributes": True}


class AIFollowupOut(BaseModel):
    id: int
    recommendation: str
    follow_up_type: Optional[str] = None
    urgency: str = "routine"
    suggested_days: Optional[int] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Root encounter response
# ---------------------------------------------------------------------------

class EncounterResponse(BaseModel):
    encounter_id: int
    patient_id: int
    status: str                     # pending / ready / confirmed / rejected
    is_confirmed: bool = False
    encounter_date: datetime
    chief_complaint: str = ""

    # Structured AI outputs
    soap: Dict[str, Any] = {}
    medications: List[AIMedicationOut] = []
    diagnoses: List[AIDiagnosisOut] = []
    procedures: List[AIProcedureOut] = []
    billing: List[AIBillingOut] = []
    timeline_events: List[AITimelineEventOut] = []
    followups: List[AIFollowupOut] = []

    # Clinical intelligence
    risk_score: str = "Low"
    risk_flags: List[str] = []
    legal_flags: List[str] = []
    admission_required: bool = False
    icu_required: bool = False
    follow_up_days: Optional[int] = None
    case_status: str = "active"
    billing_complexity: str = "medium"

    # Mandatory watermark for AI-generated content
    ai_watermark: str = "AI-GENERATED DRAFT ⚠️ — Requires licensed clinician review."

    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Confirmation response
# ---------------------------------------------------------------------------

class EncounterConfirmResponse(BaseModel):
    encounter_id: int
    confirmed: bool
    confirmed_medications: List[str] = []
    confirmed_procedures: List[str] = []
    confirmed_diagnoses: List[str] = []
    confirmed_billing: List[str] = []
    confirmed_tasks: List[str] = []


# ---------------------------------------------------------------------------
# List / summary view
# ---------------------------------------------------------------------------

class EncounterSummary(BaseModel):
    encounter_id: int
    encounter_date: datetime
    chief_complaint: str = ""
    status: str
    is_confirmed: bool
    risk_score: str
    case_status: str
    medication_count: int = 0
    diagnosis_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
