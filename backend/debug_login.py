from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.core import security
from app.core.config import settings
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_login():
    print("--- DEBUGGING LOGIN ---")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    
    # 1. Test Connection
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database Connection: SUCCESS")
    except Exception as e:
        print(f"❌ Database Connection: FAILED - {e}")
        return

    # 2. Check User
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    email = "admin@clinical.ai"
    password = "Admin@123"
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"❌ User Not Found: {email}")
    else:
        print(f"✅ User Found: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Hashed Password: {user.hashed_password}")
        
        # 3. Verify Password
        try:
            is_valid = security.verify_password(password, user.hashed_password)
            if is_valid:
                print(f"✅ Password Verification: SUCCESS (Password '{password}' matches hash)")
            else:
                print(f"❌ Password Verification: FAILED (Password '{password}' does NOT match hash)")
        except Exception as e:
             print(f"❌ Password Verification Error: {e}")

    db.close()

if __name__ == "__main__":
    debug_login()
