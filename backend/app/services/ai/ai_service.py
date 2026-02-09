import groq
import json
import time
import asyncio
from typing import Dict, Any, Optional
from fastapi import HTTPException
from ...core.config import settings
from ...core.logging import logger, request_id_contextvar
from .prompts import PROMPTS

class AIService:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.critical("GROQ_API_KEY is missing. AI structured note generation will fail.")
            self.client = None
        else:
            self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
            
    async def structure_clinical_note(self, text: str, note_type: str = "SOAP") -> dict:
        """
        Structures raw clinical text into JSON using Groq.
        """
        if not self.client:
            raise HTTPException(
                status_code=503, 
                detail="clinical intelligence service (Groq) is not configured on the backend."
            )

        system_prompt = PROMPTS.get(note_type, PROMPTS["SOAP"])
        retries = 3
        
        for attempt in range(retries):
            try:
                start_time = time.time()
                # Strict timeout to prevent hanging requests
                response = self.client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    response_format={"type": "json_object"},
                    timeout=20.0 
                )
                latency = time.time() - start_time
                
                content = response.choices[0].message.content
                data = json.loads(content)
                
                # Validation: Ensure keys exist based on note_type
                validated_data = self._validate_and_fix_response(data, note_type)
                
                logger.info(f"Groq structure call successful", extra={"metadata": {
                    "request_id": request_id_contextvar.get() or "N/A",
                    "latency": round(latency, 3),
                    "model": settings.GROQ_MODEL
                }})
                
                return validated_data
                
            except (json.JSONDecodeError, groq.APIError, groq.RateLimitError) as e:
                logger.warning(f"Groq call failed (Attempt {attempt+1}): {str(e)}")
                if attempt == retries - 1:
                     raise HTTPException(status_code=503, detail="AI provider is currently overwhelmed.")
                await asyncio.sleep(1.0 * (attempt + 1)) # Simple exponential backoff
                
            except Exception as e:
                logger.error(f"Critical AI Error: {str(e)}")
                raise HTTPException(status_code=500, detail="Error structuring clinical note.")

    async def summarize_patient_initially(self, history_text: str) -> str:
        """
        Summarizes patient history for the final report.
        """
        if not self.client:
            return "Clinical summary unavailable (AI not configured)."
            
        system_prompt = "You are a senior clinical documentation assistant. Summarize the patient clinical history into a professional, concise summary. Stick to facts entered. No advice."
        
        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": history_text}
                ],
                timeout=25.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            return "Summary generation failed."

    def _validate_and_fix_response(self, data: dict, note_type: str) -> dict:
        """
        Ensures the response has the required keys for the specific note type.
        Injects 'Not documented' if a section is missing.
        """
        required_keys = {
            "SOAP": ["subjective", "objective", "assessment", "plan"],
            "PROGRESS": ["interval_history", "exam", "impression", "plan"],
            "DISCHARGE": ["admission_diagnosis", "hospital_course", "discharge_condition", "discharge_medication", "follow_up"]
        }
        
        keys = required_keys.get(note_type, required_keys["SOAP"])
        for key in keys:
            if key not in data:
                data[key] = "Not documented (Auto-filled)"
        
        # Remove extra keys to keep schema strict? Or allow them? 
        # For safety, strictly keeping only expected keys might be better, but flexibility is okay.
        # Let's ensure top-level keys are strings.
        for k, v in data.items():
            if not isinstance(v, str) and not isinstance(v, (int, float, bool)):
                # Flatten complex structures or coerce to string
                data[k] = str(v)
                
        return data

    def _get_demo_response(self, note_type: str) -> dict:
        defaults = {
            "SOAP": {
                "subjective": "DEMO MODE: API Key missing.",
                "objective": "Vitals: T 98.6, BP 120/80.",
                "assessment": "Stable.",
                "plan": "Continue current care."
            },
            "PROGRESS": {
                "interval_history": "DEMO MODE: API Key missing.",
                "exam": "Stable.",
                "impression": "Improving.",
                "plan": "Continue."
            },
            "DISCHARGE": {
                "admission_diagnosis": "DEMO MODE",
                "hospital_course": "Unremarkable.",
                "discharge_condition": "Stable.",
                "discharge_medication": "None.",
                "follow_up": "None."
            }
        }
        return defaults.get(note_type, defaults["SOAP"])

    def _get_error_response(self, note_type: str, error_msg: str) -> dict:
        """
        Returns a valid dictionary structure but filled with error messages.
        This prevents the frontend from crashing due to missing keys.
        """
        required_keys = {
            "SOAP": ["subjective", "objective", "assessment", "plan"],
            "PROGRESS": ["interval_history", "exam", "impression", "plan"],
            "DISCHARGE": ["admission_diagnosis", "hospital_course", "discharge_condition", "discharge_medication", "follow_up"]
        }
        
        keys = required_keys.get(note_type, required_keys["SOAP"])
        # Put the error in the first field, N/A in others
        response = {key: "N/A" for key in keys}
        response[keys[0]] = f"Error: {error_msg}"
        return response
