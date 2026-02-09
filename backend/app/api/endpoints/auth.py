from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ... import models
from ...schemas import auth as auth_schemas
from ..deps import get_current_user

router = APIRouter()

@router.post("/register")
def register():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Registration is now handled by Firebase Authentication on the frontend."
    )

@router.post("/login")
def login():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Backend-managed password login is disabled. Use Firebase Authentication on the frontend to obtain an ID token, then use the /me endpoint to sync."
    )

@router.get("/me", response_model=auth_schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
