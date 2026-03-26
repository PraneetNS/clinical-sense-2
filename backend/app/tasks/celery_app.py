from celery import Celery
import os
from ..core.config import settings

# In a real environment, REDIS_URL should be in settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "clinical_sense_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.follow_up_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
