import os

file_path = r"c:\Users\savan\OneDrive\Desktop\something_crazy\backend\app\api\endpoints\ai.py"

with open(file_path, "r") as f:
    content = f.read()

old_code = '''@router.post("/transcribe")
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Transcribes audio using Groq Whisper model.
    """
    import os
    import tempfile
    import groq
    from ...core.config import settings

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API key not configured")

    client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        content = await file.read()
        temp_audio.write(content)
        temp_audio_path = temp_audio.name
        
    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=(temp_audio_path, audio_file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        return {"text": transcription.text, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(temp_audio_path)'''

new_code = '''@router.post("/transcribe")
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = None, 
    patient_id: int = None,
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Transcribes audio using Groq Whisper model with session buffering.
    Rate limited: 10 calls/minute.
    """
    import os
    import tempfile
    import groq
    import time
    from ...core.config import settings

    # 1. Rate Limiting (Simple)
    now = time.time()
    user_ts = SCRIBE_LIMITS.get(current_user.id, [])
    user_ts = [ts for ts in user_ts if now - ts < 60]
    if len(user_ts) >= 10:
        raise HTTPException(status_code=429, detail="Scribe rate limit exceeded (10/min)")
    user_ts.append(now)
    SCRIBE_LIMITS[current_user.id] = user_ts

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API key not configured")

    client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    # Save Uploaded File
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        content = await file.read()
        temp_audio.write(content)
        temp_audio_path = temp_audio.name
        
    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=(temp_audio_path, audio_file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
            
        transcript = transcription.text
        
        # 2. Buffering
        if session_id and patient_id:
            buffer_key = f"{patient_id}:{session_id}"
            session_data = SCRIBE_BUFFER.get(buffer_key, {"text": "", "last_update": now})
            session_data["text"] += " " + transcript
            session_data["last_update"] = now
            SCRIBE_BUFFER[buffer_key] = session_data
            
            # Cleanup old sessions (> 30 mins)
            for k in list(SCRIBE_BUFFER.keys()):
                if now - SCRIBE_BUFFER[k]["last_update"] > 1800:
                    del SCRIBE_BUFFER[k]
                    
            return {
                "transcript": transcript, 
                "accumulated_text": session_data["text"].strip(),
                "status": "success"
            }
            
        return {"transcript": transcript, "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(temp_audio_path)

@router.get("/portal/{token}")
async def get_portal_summary(token: str, db: Session = Depends(deps.get_db)):
    """
    Publicly accessible endpoint for the patient portal.
    Requires no auth, only a valid non-expired token.
    """
    from ...models import PatientPortalLink, AIEncounter, Patient
    from datetime import datetime
    
    link = db.query(PatientPortalLink).filter(PatientPortalLink.token == token).first()
    if not link:
        return {"expired": True, "error": "Invalid or expired link."}
        
    if link.expires_at < datetime.utcnow():
        return {"expired": True, "error": "This link has expired for your security."}
        
    # Mark viewed
    if not link.accessed_at:
        link.accessed_at = datetime.utcnow()
        db.commit()
        
    encounter = link.encounter
    patient = link.patient
    
    # Extract quality report components for the summary
    report = encounter.quality_report
    patient_summary = "Please contact your provider for details."
    
    if report and report.differential_output:
         patient_summary = report.differential_output.get("patient_summary", patient_summary)
    
    # If no specific patient summary found, fall back to SOAP plan
    if patient_summary == "Please contact your provider for details.":
        try:
            soap = json.loads(encounter.soap_note)
            patient_summary = soap.get("plan", patient_summary)
        except:
            pass

    return {
        "patient_first_name": patient.name.split()[0] if patient.name else "Patient",
        "visit_date": encounter.encounter_date.strftime("%B %d, %Y") if encounter.encounter_date else "Unknown",
        "summary": patient_summary,
        "medications": [m.name for m in encounter.medications],
        "followup_instructions": "Review the summary above for follow-up details.",
        "expired": False
    }'''

if old_code in content:
    new_content = content.replace(old_code, new_code)
    with open(file_path, "w") as f:
        f.write(new_content)
    print("SUCCESS")
else:
    # Try with slight whitespace variation (universal newline match)
    import re
    # Escape special characters and replace any whitespace with \s+
    pattern = re.escape(old_code).replace(r'\ ', r'\s+').replace(r'\n', r'\s+')
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_code, content, count=1)
        with open(file_path, "w") as f:
            f.write(new_content)
        print("SUCCESS (Regex)")
    else:
        print("FAILURE: Old code not found")
        # Print a snippet to debug
        print("CONTENT SNIPPET around /transcribe:")
        idx = content.find("@router.post(\"/transcribe\")")
        if idx != -1:
            print(content[idx:idx+500])
        else:
            print("Could not find @router.post(\"/transcribe\") even with simple search")
