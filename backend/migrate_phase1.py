from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.models import Base
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    logger.info("Migrating database...")
    
    # Handle postgres protocol
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    # 1. Update existing Patient table
    if inspector.has_table("patients"):
        logger.info("Checking patients table columns...")
        existing_columns = [col['name'] for col in inspector.get_columns("patients")]
        
        new_columns = {
            "gender": "VARCHAR",
            "phone_number": "VARCHAR",
            "address": "TEXT",
            "insurance_provider": "VARCHAR",
            "policy_number": "VARCHAR",
            "emergency_contact_name": "VARCHAR",
            "emergency_contact_relation": "VARCHAR",
            "emergency_contact_phone": "VARCHAR"
        }
        
        with engine.connect() as conn:
            with conn.begin(): # Transaction
                for col, dtype in new_columns.items():
                    if col not in existing_columns:
                        logger.info(f"Adding column {col} to patients table...")
                        try:
                            # Use text() properly
                            conn.execute(text(f"ALTER TABLE patients ADD COLUMN {col} {dtype}"))
                        except Exception as e:
                            logger.error(f"Error adding {col}: {e}")
    else:
        logger.info("Patients table does not exist, it will be created by create_all")
    
    # 2. Create new tables
    logger.info("Creating new tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
        
    logger.info("Migration complete.")

if __name__ == "__main__":
    migrate()
