import os
import psycopg2
import traceback
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

STATEMENTS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'DOCTOR';",
    "UPDATE users SET role = 'DOCTOR' WHERE role IS NULL;",
    """DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_user_roles') THEN
            ALTER TABLE users ADD CONSTRAINT ck_user_roles 
            CHECK (role IN ('DOCTOR', 'NURSE', 'BILLING_ADMIN', 'READ_ONLY_AUDITOR', 'SUPER_ADMIN'));
        END IF;
    END $$;""",
    "CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);",
    "ALTER TABLE ai_encounters ADD COLUMN IF NOT EXISTS model_version VARCHAR(100);",
    "ALTER TABLE ai_encounters ADD COLUMN IF NOT EXISTS processing_latency_ms INTEGER;",
    """CREATE TABLE IF NOT EXISTS ai_quality_reports (
        id SERIAL PRIMARY KEY,
        encounter_id INTEGER NOT NULL REFERENCES ai_encounters(id) ON DELETE CASCADE,
        confidence_score FLOAT NOT NULL DEFAULT 0.0,
        compliance_score FLOAT NOT NULL DEFAULT 0.0,
        billing_accuracy_score FLOAT,
        hallucination_flags JSONB,
        missing_critical_fields JSONB,
        clinical_safety_flags JSONB,
        risk_level VARCHAR(20) NOT NULL DEFAULT 'HIGH',
        model_version VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );""",
    "CREATE INDEX IF NOT EXISTS ix_ai_quality_reports_encounter_id ON ai_quality_reports(encounter_id);",
    "CREATE INDEX IF NOT EXISTS ix_ai_quality_reports_created_at ON ai_quality_reports(created_at);",
    """DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_quality_risk_level') THEN
            ALTER TABLE ai_quality_reports ADD CONSTRAINT ck_quality_risk_level 
            CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH'));
        END IF;
    END $$;""",
    """CREATE TABLE IF NOT EXISTS ai_usage_metrics (
        id SERIAL PRIMARY KEY,
        encounter_id INTEGER NOT NULL REFERENCES ai_encounters(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES users(id),
        tokens_used INTEGER,
        latency_ms INTEGER,
        accepted_without_edit BOOLEAN DEFAULT FALSE,
        edit_distance_score FLOAT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );""",
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_metrics_encounter_id ON ai_usage_metrics(encounter_id);",
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_metrics_user_id ON ai_usage_metrics(user_id);",
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_metrics_created_at ON ai_usage_metrics(created_at);",
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_metrics_user_created ON ai_usage_metrics(user_id, created_at);"
]

def run_migration():
    print(f"Connecting to DB...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        for i, stmt in enumerate(STATEMENTS):
            print(f"Executing statement {i+1}/{len(STATEMENTS)}...")
            try:
                cur.execute(stmt)
            except Exception as e:
                print(f"Error in statement {i+1}: {e}")
                # print(traceback.format_exc())
        conn.close()
        print("Migration process finished.")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    run_migration()
