from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, Base
from app.core import security
import os

from app.core.config import settings

# Database Path
DB_URL = settings.DATABASE_URL
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_user():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Check if user exists
    email = "admin@clinical.ai"
    password = "password123"
    
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print(f"User {email} already exists.")
        return

    hashed_pw = security.get_password_hash(password)
    new_user = User(
        email=email,
        hashed_password=hashed_pw,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    print(f"Successfully created user: {email} with password: {password}")
    db.close()

if __name__ == "__main__":
    seed_user()
