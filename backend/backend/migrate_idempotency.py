from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clinical_notes ADD COLUMN idempotency_key VARCHAR"))
            conn.execute(text("CREATE UNIQUE INDEX ix_clinical_notes_idempotency_key ON clinical_notes (idempotency_key)"))
            print("Migration successful: Added idempotency_key to clinical_notes")
        except Exception as e:
            print(f"Migration likely already applied or failed: {e}")

if __name__ == "__main__":
    migrate()
