from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
from ...db.session import get_db
from ...api.deps import get_current_user
from ...models import User
from ...schemas.notes import NoteCreateRequest, NoteResponse, NoteUpdateRequest
from ...services.notes.note_service import NoteService
from ...core.config import settings
from fastapi import Request
import markupsafe

from ...core.ratelimit import limiter

router = APIRouter()

@router.post("/structure", response_model=NoteResponse)
@limiter.limit("5/minute")
async def structure_note(
    request: Request,

    note_in: NoteCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Basic Sanitization
    note_in.raw_content = markupsafe.escape(note_in.raw_content)
    
    # Business logic handled by service layer
    db_note = await NoteService.create_and_structure_note(db, current_user.id, note_in)
    
    # Trigger Async Risk Analysis
    background_tasks.add_task(NoteService.analyze_risks_task, db_note.id)
    
    # Transform for response (JSON string to dict)
    response_data = NoteResponse.from_orm(db_note)
    if db_note.structured_content:
        response_data.structured_content = json.loads(db_note.structured_content)
    # AI insights async, so likely None immediately, but just in case
    if db_note.ai_insights:
        response_data.ai_insights = {
            "risk_score": db_note.ai_insights.risk_score,
            "red_flags": json.loads(db_note.ai_insights.red_flags or "[]"),
            "suggestions": json.loads(db_note.ai_insights.suggestions or "[]"),
            "missing_info": json.loads(db_note.ai_insights.missing_info or "[]")
        }
    return response_data

@router.get("/", response_model=List[NoteResponse])
@limiter.limit("20/minute")
def get_notes(
    request: Request,
    search: str = None,
    mode: str = "keyword", 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ...core.logging import logger
    logger.info(f"Fetching notes for user {current_user.id} (search: {search}, mode: {mode})")
    if search and mode == "semantic":
        notes = NoteService.semantic_search(db, current_user.id, search)
    else:
        notes = NoteService.get_user_notes(db, current_user.id, search)

    # Transform list
    result = []
    for note in notes:
        nr = NoteResponse.from_orm(note)
        if note.structured_content:
            nr.structured_content = json.loads(note.structured_content)
        if note.ai_insights:
            nr.ai_insights = {
                "risk_score": note.ai_insights.risk_score,
                "red_flags": json.loads(note.ai_insights.red_flags or "[]"),
                "suggestions": json.loads(note.ai_insights.suggestions or "[]"),
                "missing_info": json.loads(note.ai_insights.missing_info or "[]")
            }
        result.append(nr)
    return result

@router.get("/{id}", response_model=NoteResponse)
@limiter.limit("60/minute")
def get_note(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = NoteService.get_note_by_id(db, id, current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    nr = NoteResponse.from_orm(note)
    if note.structured_content:
        nr.structured_content = json.loads(note.structured_content)
    if note.ai_insights:
        nr.ai_insights = {
            "risk_score": note.ai_insights.risk_score,
            "red_flags": json.loads(note.ai_insights.red_flags or "[]"),
            "suggestions": json.loads(note.ai_insights.suggestions or "[]"),
            "missing_info": json.loads(note.ai_insights.missing_info or "[]")
        }
    return nr

@router.put("/{id}", response_model=NoteResponse)
@limiter.limit("10/minute")
def update_note(
    request: Request,
    id: int,
    note_in: NoteUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = NoteService.update_note(db, id, current_user.id, note_in)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    nr = NoteResponse.from_orm(note)
    if note.structured_content:
        nr.structured_content = json.loads(note.structured_content)
    if note.ai_insights:
        nr.ai_insights = {
            "risk_score": note.ai_insights.risk_score,
            "red_flags": json.loads(note.ai_insights.red_flags or "[]"),
            "suggestions": json.loads(note.ai_insights.suggestions or "[]"),
            "missing_info": json.loads(note.ai_insights.missing_info or "[]")
        }
    return nr

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_note(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = NoteService.soft_delete_note(db, id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return None

@router.get("/{id}/history")
@limiter.limit("20/minute")
def get_note_history(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = NoteService.get_note_history(db, id, current_user.id)
    return history
