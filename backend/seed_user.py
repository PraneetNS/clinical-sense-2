import logging
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def test_connection():
    db_url = settings.DATABASE_URL
    
    logger.info(f"Connecting to: {db_url.split('@')[1] if '@' in db_url else 'LOCAL'}")
    
    try:
        engine = create_engine(db_url)
        # Verify connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            row = result.fetchone()
            logger.info(f"✅ Connection confirmed! DB Version: {row[0]}")
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
