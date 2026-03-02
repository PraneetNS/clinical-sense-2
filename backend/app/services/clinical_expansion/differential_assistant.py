"""
Differential Diagnosis Assistant (Assistive Only)
=================================================
LLM-powered suggestion of differentials for clinician consideration.
Must include disclaimer and confidence scores.
"""

from typing import Any, Dict, List
from ...services.ai.ai_service import AIService

class DifferentialAssistant:
    """
    Assistant for considering differential diagnoses based on SOAP or Note.
    """
    DISCLAIMER = "For clinical consideration only. Not diagnostic advice. Refer to licensed practitioner."

    def __init__(self, ai_service: AIService):
        self.ai = ai_service

    async def generate_differentials(
        self, 
        soap_json: Dict[str, Any], 
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for differentials. Calls LLM to provide suggestions.
        """
        try:
            result = await self.ai.run_hospital_agent("DIFFERENTIAL_ASSISTANT", 
                {"soap": soap_json, "patient_context": patient_context})
            
            # Formulate structured output
            differentials = result.get("possible_differentials", [])
            
            return {
                "disclaimer": self.DISCLAIMER,
                "possible_differentials": [
                    {
                        "condition": d.get("condition", "Undefined"),
                        "confidence": float(d.get("confidence", 0.5)),
                        "reason": d.get("reason", "No reason provided")
                    } for d in differentials
                ]
            }
        except Exception:
            return {
                "disclaimer": self.DISCLAIMER,
                "possible_differentials": []
            }
