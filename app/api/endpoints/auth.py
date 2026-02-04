from fastapi import APIRouter, Depends, HTTPException, status
import logging
logger = logging.getLogger(__name__)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from ...core import security
from ...core.config import settings
from ... import models
from ...schemas import auth as auth_schemas
from ...db.session import get_db
from ..deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=auth_schemas.UserResponse)
def register_user(user: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=auth_schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info(f"Login attempt for user: {form_data.username}")
        user = db.query(models.User).filter(models.User.email == form_data.username).first()
        if not user:
            logger.warning(f"Login failed: User {form_data.username} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password - susceptible to crashes if bcrypt/passlib version mismatch
        try:
            is_valid = security.verify_password(form_data.password, user.hashed_password)
        except Exception as e:
            logger.error(f"Password verification error for {form_data.username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Authentication system error"
            )

        if not is_valid:
            logger.warning(f"Login failed: Incorrect password for {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Login successful for user: {form_data.username}")
    except HTTPException as he:
        # Re-raise HTTP exceptions (404, 401)
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during login for {form_data.username}: {str(e)}")
        # Return 500 instead of crashing (502)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal login error"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=auth_schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
