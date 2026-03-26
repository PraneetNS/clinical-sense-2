import requests
from .celery_app import celery_app
from ..core.config import settings

@celery_app.task(name="tasks.trigger_follow_up_call")
def trigger_follow_up_call(patient_id: int, encounter_id: int):
    """
    Triggers the Twilio outbound call by POSTing to the internal /twilio/initiate-call endpoint.
    This task is intended to be called with a 24-hour delay.
    """
    # Use internal URL or loopback
    api_url = f"http://localhost:8000{settings.API_V1_STR}/twilio/initiate-call"
    
    payload = {
        "patient_id": patient_id,
        "encounter_id": encounter_id
    }
    
    try:
        # In a real setup, we might need a system token
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        return {"status": "success", "response": response.json()}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
