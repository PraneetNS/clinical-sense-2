import groq
import json
import time
import asyncio
from typing import Dict, Any, Optional, List
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
            
    async def structure_clinical_note(self, text: str, note_type: str = "SOAP", encounter_date: Optional[str] = None) -> dict:
        """
        Structures raw clinical text into JSON using Groq.
        """
        if not self.client:
            raise HTTPException(
                status_code=503, 
                detail="clinical intelligence service (Groq) is not configured on the backend."
            )

        system_prompt = PROMPTS.get(note_type, PROMPTS["SOAP"])
        
        # Add temporal context if available
        user_content = text
        if encounter_date:
            user_content = f"CONTEXT: This encounter occurred on {encounter_date}.\n\nCLINICAL NOTE:\n{text}"
            
        retries = 3
        
        for attempt in range(retries):
            try:
                start_time = time.time()
                # Strict timeout to prevent hanging requests
                response = self.client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
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

    async def analyze_risks(self, note_content: Dict[str, Any], patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes clinical note for risks, red flags, and missing info.
        """
        if not self.client:
             logger.warning("GROQ_API_KEY missing, skipping risk analysis")
             return {"risk_score": "Low (AI Offline)", "red_flags": [], "suggestions": [], "missing_info": []}
        
        context_str = f"""
        Patient Context:
        History: {patient_context.get('history', 'N/A')}
        Meds: {', '.join(patient_context.get('medications', []) or [])}
        Allergies: {', '.join(patient_context.get('allergies', []) or [])}
        Vitals: {patient_context.get('vitals', 'N/A')}
        
        Clinical Note:
        {json.dumps(note_content, indent=2)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPTS["RISK_ANALYSIS"]},
                    {"role": "user", "content": context_str}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            return {"risk_score": "Error", "red_flags": ["Analysis failed"], "suggestions": [], "missing_info": []}

    async def generate_differential(self, symptoms: List[str], vitals: Dict, age: int, gender: str) -> Dict[str, Any]:
        if not self.client:
            return {"differentials": []}

        input_text = f"Patient: {age} {gender}. Symptoms: {', '.join(symptoms)}. Vitals: {vitals}"
        try:
             response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPTS["DIFFERENTIAL"]},
                    {"role": "user", "content": input_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
             return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Differential diagnosis failed: {e}")
            return {"differentials": []}

    async def medical_legal_review(self, note_text: str) -> Dict[str, Any]:
        if not self.client:
            return {"suggestions": [], "missing_info": []}

        try:
             response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPTS["MEDICO_LEGAL"]},
                    {"role": "user", "content": note_text}
                ],
                response_format={"type": "json_object"}
            )
             return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Medico-legal review failed: {e}")
            return {"suggestions": [], "missing_info": []}
            
    async def get_copilot_suggestion(self, partial_text: str) -> Dict[str, Any]:
        if not self.client:
            return {"suggestions": [], "warnings": []}

        try:
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPTS["COPILOT"]},
                    {"role": "user", "content": partial_text}
                ],
                response_format={"type": "json_object"},
                max_tokens=150
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Copilot suggestion failed: {e}")
            return {"suggestions": [], "warnings": []}

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

    async def run_hospital_agent(self, agent_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic handler for HOS Agents (Deterioration, Flow, Executive, etc.)
        """
        # Lazy import to avoid circular dependency if any (though unlikely here)
        # But ensure PROMPTS is available. It is imported at top level.
        
        prompt_template = PROMPTS.get(agent_type)
        if not prompt_template:
            # Fallback or error
            logger.error(f"Unknown agent type: {agent_type}")
            return {"error": "Unknown agent type"}

        if not self.client:
            return {"error": "AI Service Unavailable"}

        try:
            messages = [
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": json.dumps(context, default=str)}
            ]

            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.1, # Low temp for analytical tasks
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}

    async def generate_patient_communication(self, note_text: str, language: str = "en") -> Dict[str, Any]:
        context = {"note_text": note_text, "language": language}
        return await self.run_hospital_agent("PATIENT_SUMMARY", context)

    async def draft_message_response(self, patient_message: str, patient_context: str) -> Dict[str, Any]:
        context = {"patient_message": patient_message, "medical_context": patient_context}
        return await self.run_hospital_agent("MESSAGE_DRAFT", context)

    async def analyze_message_urgency(self, message: str) -> Dict[str, Any]:
        return await self.run_hospital_agent("URGENCY_DETECTION", {"message": message})

    async def generate_shift_handover(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.run_hospital_agent("SHIFT_HANDOVER", patient_data)

    async def check_medication_safety(self, current_meds: List[str], new_med: str, allergies: List[str]) -> Dict[str, Any]:
        context = {
            "current_medications": current_meds,
            "new_medication": new_med,
            "allergies": allergies
        }
        return await self.run_hospital_agent("MEDICATION_SAFETY", context)

    async def predict_readmission_risk(self, patient_history: str, discharge_condition: str) -> Dict[str, Any]:
        context = {
            "history": patient_history,
            "discharge_condition": discharge_condition
        }
        return await self.run_hospital_agent("READMISSION_RISK", context)

    async def analyze_population_patterns(self, aggregated_data: str) -> Dict[str, Any]:
        return await self.run_hospital_agent("PATTERN_RECOGNITION", {"data": aggregated_data})
