"""
Clinical Intelligence Platform — API Router
============================================
POST /api/v1/ai/generate_full_encounter  — trigger full AI encounter
GET  /api/v1/ai/encounters/{patient_id}  — list encounters for patient
GET  /api/v1/ai/encounter/{encounter_id} — get a single encounter
POST /api/v1/ai/encounter/{encounter_id}/confirm — confirm and promote AI data
WS   /api/v1/ai/encounter/ws/{encounter_id}  — stream progress updates
"""

import asyncio
import json
import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...api.deps import get_current_user
from ...models import User, AIEncounter
from ...schemas.encounter import (
    EncounterRequest,
    EncounterResponse,
    EncounterConfirmResponse,
    EncounterSummary,
)
from ...services.clinical_intelligence import ClinicalIntelligenceOrchestrator
from ...services.ai.ai_service import AIService
from ...core.logging import logger
from ...core.ratelimit import limiter
from fastapi import Request


router = APIRouter()
_ai_service = AIService()


def get_orchestrator(db: Session = Depends(get_db)) -> ClinicalIntelligenceOrchestrator:
    return ClinicalIntelligenceOrchestrator(db, _ai_service)


# ---------------------------------------------------------------------------
# WebSocket connection manager (lightweight — single-encounter streaming)
# ---------------------------------------------------------------------------

class EncounterProgressManager:
    """Tracks active WebSocket connections for encounter progress streaming."""

    def __init__(self):
        # encounter_id -> WebSocket
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, encounter_id: int, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(encounter_id, []).append(ws)

    def disconnect(self, encounter_id: int, ws: WebSocket):
        conns = self._connections.get(encounter_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, encounter_id: int, event: dict):
        conns = self._connections.get(encounter_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(encounter_id, ws)


progress_manager = EncounterProgressManager()


# ---------------------------------------------------------------------------
# Endpoint: Generate Full Encounter
# ---------------------------------------------------------------------------

@router.post(
    "/generate_full_encounter",
    response_model=EncounterResponse,
    summary="Generate a full AI clinical encounter from a raw note",
    status_code=201,
)
@limiter.limit("10/minute")
async def generate_full_encounter(
    request: Request,
    encounter_req: EncounterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator: ClinicalIntelligenceOrchestrator = Depends(get_orchestrator),
):
    """
    Accepts a raw clinical note and orchestrates 6 parallel AI pipelines:
    - SOAP structuring
    - Medication extraction + structuring
    - ICD-10 diagnosis coding
    - Billing intelligence
    - Case intelligence (risk, follow-up, case status)
    - Medico-legal audit

    Returns a unified encounter object. Doctor must call /confirm to promote data.

    Rate limited: 10 requests/minute per user.
    """
    logger.info(
        f"Generating full encounter for patient_id={encounter_req.patient_id}",
        extra={"metadata": {"user_id": current_user.id}},
    )

    encounter = await orchestrator.generate_encounter(
        request=encounter_req,
        user_id=current_user.id,
    )

    # Broadcast a "ready" event over WebSocket if listeners exist
    background_tasks.add_task(
        progress_manager.broadcast,
        encounter.encounter_id,
        {
            "event": "encounter_ready",
            "encounter_id": encounter.encounter_id,
            "status": "ready",
            "timestamp": datetime.datetime.utcnow().isoformat(),
        },
    )

    return encounter


# ---------------------------------------------------------------------------
# Endpoint: List encounters for a patient
# ---------------------------------------------------------------------------

@router.get(
    "/encounters/{patient_id}",
    response_model=List[EncounterSummary],
    summary="List all AI encounters for a patient",
)
async def list_encounters(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    encounters = (
        db.query(AIEncounter)
        .filter(
            AIEncounter.patient_id == patient_id,
            AIEncounter.created_by_id == current_user.id,
        )
        .order_by(AIEncounter.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        EncounterSummary(
            encounter_id=e.id,
            encounter_date=e.encounter_date,
            chief_complaint=e.chief_complaint or "",
            status=e.status,
            is_confirmed=e.is_confirmed,
            risk_score=e.risk_score or "Low",
            case_status=e.case_status,
            medication_count=len(e.medications),
            diagnosis_count=len(e.diagnoses),
            created_at=e.created_at,
        )
        for e in encounters
    ]


# ---------------------------------------------------------------------------
# Endpoint: Get single encounter
# ---------------------------------------------------------------------------

@router.get(
    "/encounter/{encounter_id}",
    response_model=EncounterResponse,
    summary="Get a specific AI encounter by ID",
)
async def get_encounter(
    encounter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator: ClinicalIntelligenceOrchestrator = Depends(get_orchestrator),
):
    encounter = (
        db.query(AIEncounter)
        .filter(
            AIEncounter.id == encounter_id,
            AIEncounter.created_by_id == current_user.id,
        )
        .first()
    )
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    # Re-build from DB (merged is reconstructed from DB fields)
    soap = {}
    try:
        soap = json.loads(encounter.soap_note or "{}")
    except Exception:
        pass

    from ...services.clinical_intelligence import _safe_json_loads

    return EncounterResponse(
        encounter_id=encounter.id,
        patient_id=encounter.patient_id,
        status=encounter.status,
        is_confirmed=encounter.is_confirmed,
        encounter_date=encounter.encounter_date,
        chief_complaint=encounter.chief_complaint or "",
        soap=soap,
        medications=[
            {
                "id": m.id, "name": m.name, "dosage": m.dosage,
                "frequency": m.frequency, "route": m.route,
                "duration": m.duration, "start_date_text": m.start_date_text,
                "requires_confirmation": m.requires_confirmation,
                "fields_required": _safe_json_loads(m.fields_required, []),
                "confidence": m.confidence or "medium",
            }
            for m in encounter.medications
        ],
        diagnoses=[
            {
                "id": d.id, "condition_name": d.condition_name,
                "icd10_code": d.icd10_code, "confidence_score": d.confidence_score or 0.5,
                "reasoning": d.reasoning, "is_primary": d.is_primary,
            }
            for d in encounter.diagnoses
        ],
        procedures=[
            {
                "id": p.id, "name": p.name, "code": p.code,
                "notes": p.notes, "confidence": p.confidence or "medium",
            }
            for p in encounter.procedures
        ],
        billing=[
            {
                "id": b.id, "cpt_code": b.cpt_code, "description": b.description,
                "estimated_cost": b.estimated_cost, "complexity": b.complexity or "medium",
                "confidence": b.confidence or 0.5,
                "requires_review": b.requires_review, "review_reason": b.review_reason,
            }
            for b in encounter.billing_items
        ],
        timeline_events=[
            {
                "id": t.id, "event_type": t.event_type,
                "event_description": t.event_description,
                "event_date_text": t.event_date_text, "severity": t.severity or "info",
            }
            for t in encounter.timeline_events
        ],
        followups=[
            {
                "id": f.id, "recommendation": f.recommendation,
                "follow_up_type": f.follow_up_type, "urgency": f.urgency,
                "suggested_days": f.suggested_days,
            }
            for f in encounter.followups
        ],
        risk_score=encounter.risk_score or "Low",
        risk_flags=_safe_json_loads(encounter.risk_flags, []),
        legal_flags=_safe_json_loads(encounter.legal_flags, []),
        admission_required=encounter.admission_required,
        icu_required=encounter.icu_required,
        follow_up_days=encounter.follow_up_days,
        case_status=encounter.case_status,
        billing_complexity=encounter.billing_complexity or "medium",
        created_at=encounter.created_at,
    )


# ---------------------------------------------------------------------------
# Endpoint: Confirm encounter
# ---------------------------------------------------------------------------

@router.post(
    "/encounter/{encounter_id}/confirm",
    response_model=EncounterConfirmResponse,
    summary="Confirm AI encounter and promote data to clinical tables",
)
async def confirm_encounter(
    encounter_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator: ClinicalIntelligenceOrchestrator = Depends(get_orchestrator),
):
    """
    Promotes AI-generated encounter data into the live clinical tables:
    - AIGeneratedMedication → medications
    - AIGeneratedBilling → billing_items
    - AIFollowupRecommendation → tasks

    Only confirmed records enter the permanent clinical record.
    """
    result = await orchestrator.confirm_encounter(
        encounter_id=encounter_id,
        user_id=current_user.id,
    )

    # Notify WS listeners
    background_tasks.add_task(
        progress_manager.broadcast,
        encounter_id,
        {
            "event": "encounter_confirmed",
            "encounter_id": encounter_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        },
    )

    return result


# ---------------------------------------------------------------------------
# WebSocket: Stream encounter progress
# ---------------------------------------------------------------------------

@router.websocket("/encounter/ws/{encounter_id}")
async def encounter_ws(
    encounter_id: int,
    websocket: WebSocket,
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time encounter progress streaming.
    Frontend connects here after calling generate_full_encounter.
    The server pushes 'encounter_ready' and 'encounter_confirmed' events.
    """
    await progress_manager.connect(encounter_id, websocket)
    logger.info(f"WebSocket connected for encounter {encounter_id}")
    try:
        # Send initial status
        encounter = db.query(AIEncounter).filter(AIEncounter.id == encounter_id).first()
        if encounter:
            await websocket.send_json({
                "event": "status",
                "status": encounter.status,
                "is_confirmed": encounter.is_confirmed,
            })
        # Keep alive until disconnect
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"event": "ping"})
    except WebSocketDisconnect:
        progress_manager.disconnect(encounter_id, websocket)
        logger.info(f"WebSocket disconnected for encounter {encounter_id}")
    except Exception as e:
        logger.error(f"WebSocket error for encounter {encounter_id}: {str(e)}")
        progress_manager.disconnect(encounter_id, websocket)
@router.get("/encounter/{encounter_id}/quality-report")
async def get_quality_report(
    encounter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches the AI quality and safety report for a specific encounter."""
    encounter = db.query(AIEncounter).filter(AIEncounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    
    # Ownership Check
    if encounter.created_by_id != current_user.id and current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Access denied")

    report = encounter.quality_report
    if not report:
        raise HTTPException(status_code=404, detail="Quality report not found for this encounter")
    
    return {
        "encounter_id": encounter_id,
        "confidence_score": report.confidence_score,
        "compliance_score": report.compliance_score,
        "billing_accuracy_score": report.billing_accuracy_score,
        "hallucination_flags": report.hallucination_flags or [],
        "missing_critical_fields": report.missing_critical_fields or [],
        "clinical_safety_flags": report.clinical_safety_flags or {},
        "risk_level": report.risk_level,
        "model_version": report.model_version,
        "created_at": report.created_at,
        
        # Clinical Sense v2: Deterministic + Explainable Extensions
        "evidence_mode_enabled": report.evidence_mode_enabled,
        "rationale_json": report.rationale_json or {},
        "drug_safety_flags": report.drug_safety_flags or {},
        "structured_risk_metrics": report.structured_risk_metrics or {},
        "guideline_flags": report.guideline_flags or {},
        "differential_output": report.differential_output or {},
        "lab_interpretation": report.lab_interpretation or {},
        "handoff_sbar": report.handoff_sbar or {},
    }
