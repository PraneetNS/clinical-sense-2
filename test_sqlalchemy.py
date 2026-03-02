
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv()

url = os.getenv("DATABASE_URL")
print(f"Testing SQLAlchemy connection to: {url}")

try:
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"Success! Result: {result.fetchone()}")
except Exception as e:
    print(f"Error: {e}")
