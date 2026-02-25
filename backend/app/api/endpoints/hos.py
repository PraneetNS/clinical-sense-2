from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api.deps import get_db, get_current_user
from app.models import User
from app.services.ai.ai_service import AIService
from app.services.hos.hos_service import HOSService

router = APIRouter()
ai_service = AIService()

def get_hos_service(db: Session = Depends(get_db)):
    return HOSService(db, ai_service)

# 1. COMMAND CENTER
@router.get("/command-center/overview", response_model=Dict[str, Any])
async def get_command_center(
    current_user: User = Depends(get_current_user),
    hos: HOSService = Depends(get_hos_service)
):
    """
    Returns real-time HOS metrics: Critical count, ICU %, Staff Burnout.
    """
    return await hos.get_command_center_overview()

# 2. DETERIORATION (Manual Trigger for Demo)
@router.post("/deterioration/scan")
async def trigger_deterioration_scan(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    hos: HOSService = Depends(get_hos_service)
):
    """
    Manually triggers the deterioration scan background task.
    """
    background_tasks.add_task(hos.run_deterioration_scan)
    return {"message": "Deterioration scan initiated."}

# 3. BED FLOW
@router.get("/flow/optimize")
async def optimize_flow(
    current_user: User = Depends(get_current_user),
    hos: HOSService = Depends(get_hos_service)
):
    """
    Returns AI-suggested bed movements and bottleneck predictions.
    """
    return await hos.optimize_bed_flow()

# 4. STAFF METRICS
@router.get("/staff/metrics")
async def staff_metrics(
    current_user: User = Depends(get_current_user), # Admin only in prod
    hos: HOSService = Depends(get_hos_service)
):
    """
    Triggers staff workload analysis.
    """
    await hos.update_staff_metrics()
    return {"message": "Staff metrics updated."}

# 6. EXECUTIVE ANALYTICS
@router.get("/executive/analytics", response_model=Dict[str, Any])
async def executive_analytics(
    current_user: User = Depends(get_current_user), # Executive only in prod
    hos: HOSService = Depends(get_hos_service)
):
    """
    Returns high-level AI executive summary.
    """
    return await hos.get_executive_analytics()
