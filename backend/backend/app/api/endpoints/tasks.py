from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...api.deps import get_current_user
from ...models import User
from ...schemas.clinical import TaskResponse
from ...services.clinical_service import ClinicalService

router = APIRouter()

@router.post("/approve", response_model=TaskResponse)
def approve_task(
    taskId: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.approve_task(db, taskId, user_id=current_user.id)
