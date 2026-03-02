import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'ai_encounters'")
    cols = [c[0] for c in cur.fetchall()]
    print("AIEncounter columns:", cols)
    conn.close()
except Exception as e:
    print("Error:", e)
