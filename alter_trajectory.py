
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv()

url = os.getenv("DATABASE_URL")

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE clinical_trajectories ALTER COLUMN note_id DROP NOT NULL;"))
        conn.commit()
        print("Successfully updated clinical_trajectories table.")
except Exception as e:
    print(f"Error: {e}")
