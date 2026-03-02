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
