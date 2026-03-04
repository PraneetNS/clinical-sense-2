from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..core.config import settings
from ..db.session import get_db
from .. import models
from ..core.logging import user_id_contextvar
import firebase_admin
from firebase_admin import auth
from typing import Optional, List

security = HTTPBearer()

# Canonical RBAC roles
VALID_ROLES = {"DOCTOR", "NURSE", "BILLING_ADMIN", "READ_ONLY_AUDITOR", "SUPER_ADMIN"}

def verify_token_and_get_user(db: Session, token_str: str) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify Firebase ID Token
        decoded_token = auth.verify_id_token(token_str)
        email = decoded_token.get("email")
        firebase_uid = decoded_token.get("uid")
        
        if not email:
            raise credentials_exception
            
    except Exception as e:
        from ..core.logging import logger
        logger.error(f"Auth Error: {e}")
        raise credentials_exception
        
    # Get or Create User
    # Use a safe get-or-create pattern to handle race conditions
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        try:
            # Auto-create user from Firebase info
            from ..core.logging import logger
            logger.info(f"Auto-creating user from Firebase: {email}")
            user = models.User(
                email=email,
                firebase_uid=firebase_uid,
                full_name=decoded_token.get("name", email.split('@')[0]),
                is_active=True,
                role="DOCTOR"  # Default role
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            # If creation failed, check if user was created by a parallel request
            user = db.query(models.User).filter(models.User.email == email).first()
            if not user:
                from ..core.logging import logger
                logger.error(f"Failed to sync user {email}: {e}")
                raise HTTPException(status_code=500, detail="User account synchronization failed.")
    
    # Ensure firebase_uid is linked if it wasn't already
    if user and not user.firebase_uid:
        user.firebase_uid = firebase_uid
        db.add(user)
        db.commit()
    elif user and user.firebase_uid != firebase_uid:
        # If UID changed for some reason, update it (or log a warning)
        user.firebase_uid = firebase_uid
        db.add(user)
        db.commit()
        
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")
        
    user_id_contextvar.set(user.id)
    return user

def get_current_user(
    db: Session = Depends(get_db), 
    token: HTTPAuthorizationCredentials = Depends(security)
) -> models.User:
    return verify_token_and_get_user(db, token.credentials)

def get_current_user_from_token(
    db: Session = Depends(get_db),
    token: str = Query(...)
) -> models.User:
    """Special dependency for browser-opened files that can't send headers easily."""
    return verify_token_and_get_user(db, token)

def check_role(roles: list[str]):
    """Legacy helper — prefer require_role() for new endpoints."""
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )
        return current_user
    return role_checker

def require_role(allowed_roles: List[str]):
    """
    Server-side RBAC dependency factory.

    Usage:
        @router.get("/admin/...")
        async def endpoint(user = Depends(require_role(["SUPER_ADMIN"]))):
            ...
    """
    def _dependency(
        db: Session = Depends(get_db),
        token: HTTPAuthorizationCredentials = Depends(security),
    ) -> models.User:
        user = verify_token_and_get_user(db, token.credentials)
        # Normalise — support legacy lowercase roles
        user_role_upper = (user.role or "").upper()
        allowed_upper = [r.upper() for r in allowed_roles]
        if user_role_upper not in allowed_upper:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(allowed_roles)}",
            )
        return user
    return _dependency
