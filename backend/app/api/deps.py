from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..core.config import settings
from ..db.session import get_db
from .. import models
from ..core.logging import user_id_contextvar
import firebase_admin
from firebase_admin import auth

security = HTTPBearer()

def get_current_user(
    db: Session = Depends(get_db), 
    token: HTTPAuthorizationCredentials = Depends(security)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify Firebase ID Token
        decoded_token = auth.verify_id_token(token.credentials)
        email = decoded_token.get("email")
        firebase_uid = decoded_token.get("uid")
        
        if not email:
            raise credentials_exception
            
    except Exception as e:
        print(f"Auth Error: {e}")
        raise credentials_exception
        
    # Get or Create User
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        # Auto-create user from Firebase info
        from ..core.logging import logger
        logger.info(f"Auto-creating user from Firebase: {email}")
        user = models.User(
            email=email,
            firebase_uid=firebase_uid,
            full_name=decoded_token.get("name", email.split('@')[0]),
            is_active=True,
            role="doctor" # Default role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.firebase_uid:
        user.firebase_uid = firebase_uid
        db.commit()
        
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")
        
    user_id_contextvar.set(user.id)
    return user

def check_role(roles: list[str]):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )
        return current_user
    return role_checker
