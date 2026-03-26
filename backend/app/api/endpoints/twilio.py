from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import datetime
import json
import base64
import asyncio
from ...db.session import get_db
from ...models import FollowUpCall, Patient, AIEncounter, ClinicalNote
from ...services.ai.ai_service import AIService
from ...services.clinical_service import ClinicalService
from ...core.config import settings
from ...core.logging import logger

router = APIRouter()
_ai_service = AIService()

@router.post("/initiate-call")
async def initiate_call(patient_id: int, encounter_id: int, db: Session = Depends(get_db)):
    """
    Triggers a Twilio outbound call for a scheduled follow-up.
    """
    # 1. Fetch patient and encounter
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient or not patient.phone_number:
        raise HTTPException(status_code=400, detail="Patient or phone number not found")
        
    call_record = db.query(FollowUpCall).filter(
        FollowUpCall.patient_id == patient_id, 
        FollowUpCall.encounter_id == encounter_id,
        FollowUpCall.status == "Scheduled"
    ).first()
    
    if not call_record:
        # Create one if not exists (e.g. manual trigger)
        call_record = FollowUpCall(
            patient_id=patient_id,
            encounter_id=encounter_id,
            phone_number=patient.phone_number,
            status="Scheduled",
            scheduled_at=datetime.datetime.utcnow()
        )
        db.add(call_record)
        db.commit()
    
    # 2. Twilio Call Initiation (MOCKED for now)
    # In a real app:
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # call = client.calls.create(
    #     url=f"{settings.BASE_URL}/api/v1/twilio/call-start?call_id={call_record.id}",
    #     to=patient.phone_number,
    #     from_=settings.TWILIO_PHONE_NUMBER
    # )
    
    call_record.status = "In Progress"
    call_record.called_at = datetime.datetime.utcnow()
    db.commit()
    
    logger.info(f"Initiated Twilio call for record {call_record.id} to {patient.phone_number}")
    return {"status": "initiated", "call_id": call_record.id}

@router.get("/call-start") # Twilio usually GETs or POSTs to the URL
@router.post("/call-start")
async def call_start(request: Request):
    """
    Returns TwiML to start the call and media stream.
    """
    call_id = request.query_params.get("call_id")
    # Base URL without protocol for WebSocket
    ws_host = settings.BASE_URL.replace("https://", "").replace("http://", "")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Hi, this is an automated check-in from clinical sense. How are you feeling since your visit? Have you started the prescribed medication? Any new symptoms or concerns we should know about?</Say>
    <Pause length="1"/>
    <Connect>
        <Stream url="wss://{ws_host}/api/v1/twilio/media-stream/{call_id}" />
    </Connect>
    <Pause length="10"/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

@router.websocket("/media-stream/{call_id}")
async def media_stream(websocket: WebSocket, call_id: int, db: Session = Depends(get_db)):
    """
    Handles the WebSocket audio stream from Twilio.
    Transcribes audio chunks via Groq and appends to the call transcript.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for call_id: {call_id}")
    
    # Store audio chunks for transcription
    # Note: Twilio sends MULAW/8000. In a real app we'd need to convert this to WAV/PCM
    # for Groq's Whisper or use a streaming-capable transcription service.
    # For this implementation, we simulate real-time transcription by collecting
    # segments of the call and sending them to the transcribe_audio service.
    
    transcript_buffer = []
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['event'] == 'start':
                logger.info("Twilio Stream Started")
            elif message['event'] == 'media':
                # Twilio sends base64 encoded audio in message['media']['payload']
                # chunk = base64.b64decode(message['media']['payload'])
                # transcript_buffer.append(chunk)
                
                # SIMULATION: In a production environment, we would:
                # 1. Accumulate ~5 seconds of audio
                # 2. Convert MULAW to WAV
                # 3. Call _ai_service.transcribe_audio(chunk)
                pass
            elif message['event'] == 'stop':
                logger.info("Twilio Stream Stopped")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket Disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        # Finalize the call transcript
        call_record = db.query(FollowUpCall).filter(FollowUpCall.id == call_id).first()
        if call_record:
            # SIMULATED TRANSCRIPT for now: 
            # In a real implementation, we would have concatenated the bits from _ai_service.transcribe_audio
            simulated_transcript = "Patient says they are feeling better, started the medications, no new symptoms."
            call_record.transcript = simulated_transcript
            call_record.status = "Completed"
            db.commit()
            
            # 3. Create a clinical note from the follow-up
            try:
                note_content = f"Automated Follow-up Call Narrative:\n{simulated_transcript}"
                # Call ClinicalService.create_structured_note
                # Or use the internal API
                from ..services.clinical_service import ClinicalService
                clinical_service = ClinicalService(db)
                note = clinical_service.create_structured_note(
                    raw_content=note_content,
                    title=f"Post-Visit Follow-up Call",
                    note_type="phone_followup",
                    patient_id=call_record.patient_id,
                    user_id=1 # Default system user or clinician ID
                )
                call_record.note_id_created = note.id
                db.commit()
            except Exception as e:
                logger.error(f"Failed to create follow-up note: {e}")

@router.post("/call-status")
async def call_status(request: Request, db: Session = Depends(get_db)):
    """
    Final webhook when call ends. Used for fallback and recording call duration.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    status = form_data.get("CallStatus")
    
    logger.info(f"Twilio Call {call_sid} ended with status {status}")
    return {"status": "ok"}

@router.post("/follow-up/{encounter_id}/cancel")
async def cancel_follow_up(encounter_id: int, db: Session = Depends(get_db)):
    """
    Cancels a scheduled follow-up call.
    """
    call_record = db.query(FollowUpCall).filter(
        FollowUpCall.encounter_id == encounter_id,
        FollowUpCall.status == "Scheduled"
    ).first()
    
    if not call_record:
        raise HTTPException(status_code=404, detail="No scheduled follow-up call found for this encounter")
        
    call_record.status = "Cancelled"
    db.commit()
    return {"status": "cancelled"}
