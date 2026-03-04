from app.db.session import engine
from app.models import Base
try:
    print("Initializing mappers...")
    # This triggers mapper initialization
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
    print("Mappers initialized successfully!")
except Exception as e:
    print(f"Error: {e}")
