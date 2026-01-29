import logging
import sys
import json
import contextvars
from datetime import datetime

request_id_contextvar = contextvars.ContextVar("request_id", default=None)
user_id_contextvar = contextvars.ContextVar("user_id", default=None)

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
            "request_id": request_id_contextvar.get(),
            "user_id": user_id_contextvar.get()
        }
        if hasattr(record, "metadata"):
            log_data["metadata"] = record.metadata
        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger("clinical_assistant")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    logger.addHandler(handler)
    return logger

logger = setup_logging()
