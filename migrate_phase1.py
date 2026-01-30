from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models import Base

def migrate():
    print("Migrating database...")
    engine = create_engine(settings.DATABASE_URL)
    
    # 1. Update existing Patient table
    with engine.connect() as conn:
        # Check if columns exist in patients table
        result = conn.execute(text("PRAGMA table_info(patients)"))
        columns = [row[1] for row in result.fetchall()]
        
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
        
        for col, dtype in new_columns.items():
            if col not in columns:
                print(f"Adding column {col} to patients table...")
                try:
                    conn.execute(text(f"ALTER TABLE patients ADD COLUMN {col} {dtype}"))
                except Exception as e:
                    print(f"Error adding {col}: {e}")
    
    # 2. Create new tables
    print("Creating new tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
        
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
