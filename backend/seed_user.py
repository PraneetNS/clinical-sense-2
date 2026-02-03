from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.models import User, Base
from app.core import security

# Ensure we are not using SQLite unless explicitly configured
if settings.DATABASE_URL.startswith("sqlite"):
    print("WARNING: Using SQLite in seed script. This project is intended for PostgreSQL.")


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
