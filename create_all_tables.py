
import sys
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

load_dotenv()

from app.db.session import engine
from app.models import Base

def create_tables():
    print(f"Creating tables in: {os.getenv('DATABASE_URL')}")
    try:
        # This will create all tables defined in models.py
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()
