import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Safe, additive-only migration script for Clinical Sense v2
SQL_MIGRATION = """
BEGIN;

-- Extend AIQualityReport with v2 Clinical Expansion columns
ALTER TABLE ai_quality_reports ADD COLUMN IF NOT EXISTS rationale_json JSONB;
ALTER TABLE ai_quality_reports ADD COLUMN IF NOT EXISTS drug_safety_flags JSONB;
ALTER TABLE ai_quality_reports ADD COLUMN IF NOT EXISTS structured_risk_metrics JSONB;
ALTER TABLE ai_quality_reports ADD COLUMN IF NOT EXISTS guideline_flags JSONB;
ALTER TABLE ai_quality_reports ADD COLUMN IF NOT EXISTS differential_output JSONB;
ALTER TABLE ai_quality_reports ADD COLUMN IF NOT EXISTS lab_interpretation JSONB;
ALTER TABLE ai_quality_reports ADD COLUMN IF NOT EXISTS handoff_sbar JSONB;
ALTER TABLE ai_quality_reports ADD COLUMN IF NOT EXISTS evidence_mode_enabled BOOLEAN DEFAULT FALSE;

COMMIT;
"""

def run_migration():
    print(f"Connecting to DB...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(SQL_MIGRATION)
            print("Clinical Sense v2 migration completed successfully!")
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
