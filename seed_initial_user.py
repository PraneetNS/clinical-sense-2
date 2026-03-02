
import sys
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv()

from app.db.session import engine
from app.models import User
from app.core.auth import get_password_hash

def seed():
    print(f"Seeding user in: {os.getenv('DATABASE_URL')}")
    db = Session(bind=engine)
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == "praneet@clinic.com").first()
        if existing:
            print("User already exists.")
            return

        user = User(
            email="praneet@clinic.com",
            hashed_password=get_password_hash("password123"),
            full_name="Dr. Praneet",
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        db.commit()
        print("User seeded successfully: praneet@clinic.com / password123")
    except Exception as e:
        print(f"Error seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
