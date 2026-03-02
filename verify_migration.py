import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('ai_quality_reports', 'ai_usage_metrics', 'users', 'ai_encounters')")
    tables = cur.fetchall()
    print("Tables found:", [t[0] for t in tables])
    
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role'")
    print("User role column:", cur.fetchone())
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'ai_encounters' AND column_name IN ('model_version', 'processing_latency_ms')")
    print("AIEncounter cols:", cur.fetchall())
    
    conn.close()
except Exception as e:
    print("Error:", e)
