from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api.deps import get_db, get_current_user
from app.models import User
from app.services.ai.ai_service import AIService
from app.services.clinical.workflow_service import WorkflowService

router = APIRouter()
ai_service = AIService()

def get_workflow_service(db: Session = Depends(get_db)):
    return WorkflowService(db, ai_service)

# 1. TRAJECTORY
@router.post("/notes/{note_id}/analyze")
async def analyze_note_workflow(
    note_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    wf: WorkflowService = Depends(get_workflow_service)
):
    """
    Triggers full workflow analysis (Trajectory, Summary, Tasks).
    """
    background_tasks.add_task(wf.analyze_trajectory, note_id)
    background_tasks.add_task(wf.generate_patient_summary, note_id)
    background_tasks.add_task(wf.process_auto_tasks, note_id)
    return {"message": "Workflow analysis started."}

@router.post("/patients/{patient_id}/trajectory-check")
async def check_trajectory(
    patient_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    wf: WorkflowService = Depends(get_workflow_service)
):
    """
    Triggers trajectory analysis specifically for a patient's overall history.
    """
    background_tasks.add_task(wf.analyze_patient_trajectory, patient_id)
    return {"message": "Trajectory evaluation queued."}

# 2. DISCHARGE READINESS
@router.post("/patients/{patient_id}/discharge-check")
async def check_discharge(
    patient_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    wf: WorkflowService = Depends(get_workflow_service)
):
    background_tasks.add_task(wf.evaluate_discharge_readiness, patient_id)
    return {"message": "Discharge evaluation queued."}

# 3. DASHBOARD
@router.get("/patients/{patient_id}/workflow-dashboard")
async def get_dashboard(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    wf: WorkflowService = Depends(get_workflow_service)
):
    return await wf.get_patient_workflow_dashboard(patient_id)

@router.get("/shift-briefing")
async def get_shift_briefing(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Automated shift-end intelligence briefing system.
    Summarizes the day's encounters, highlights critical follow-ups, and flags pending medico-legal issues.
    """
    from datetime import datetime, timedelta
    from app.models import AIEncounter
    import groq
    from app.core.config import settings
    import json

    # 1. Fetch encounters from the last 12 hours
    cutoff = datetime.utcnow() - timedelta(hours=12)
    encounters = db.query(AIEncounter).filter(AIEncounter.created_at >= cutoff).all()

    if not encounters:
        return {"summary": "No encounters recorded in the last 12 hours.", "critical_actions": [], "stats": {"total": 0}}

    # 2. Extract key intel
    intel = []
    total_encounters = len(encounters)
    high_risk_count = 0
    unconfirmed = 0

    for e in encounters:
        if not e.is_confirmed:
            unconfirmed += 1
        if e.risk_score == "High":
            high_risk_count += 1
            
        intel.append({
            "encounter_id": e.id,
            "patient_id": e.patient_id,
            "chief_complaint": e.chief_complaint,
            "risk": e.risk_score,
            "confirmed": e.is_confirmed
        })

    # 3. Generate Briefing via LLM
    try:
        client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
        prompt = f"""
        You are an elite clinical assistant generating a Shift-End Intelligence Briefing for a physician.
        Current Shift Encounters: {json.dumps(intel)}
        
        Generate a concise, professional handover summary. Highlight any High risk cases that need attention or unconfirmed charts.
        Return ONLY a JSON object with this schema:
        {{
            "executive_summary": "A 2-3 sentence overview of the shift.",
            "critical_actions": ["Actionable items, e.g., 'Confirm charting for Patient X'", "Follow up on high-risk case Y"],
            "high_risk_cases_summarized": ["Brief 1-liners of high risk cases"]
        }}
        """
        
        completion = await client.chat.completions.create(
            model="llama-3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        ai_briefing = json.loads(completion.choices[0].message.content)
    except Exception as e:
        ai_briefing = {
            "executive_summary": "Failed to generate AI summary. Showing raw data.",
            "critical_actions": [f"Review {unconfirmed} unconfirmed charts"],
            "high_risk_cases_summarized": []
        }

    return {
        "stats": {
            "total_encounters": total_encounters,
            "high_risk": high_risk_count,
            "pending_charts": unconfirmed
        },
        "briefing": ai_briefing
    }
