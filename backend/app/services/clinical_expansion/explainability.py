"""
Clinical Explainability Engine
==============================
LLM-powered generation of clinical rationales and source evidence.
Must extract evidence from SOAP and include reference snippet.
"""

import json
from typing import Any, Dict, List, Optional
from ...services.ai.ai_service import AIService

class ExplainabilityEngine:
    """
    Generates structured rationales for AI-generated clinical findings.
    """
    def __init__(self, ai_service: AIService):
        self.ai = ai_service

    async def generate_clinical_rationale(
        self, 
        ai_outputs: Dict[str, Any], 
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for explainability. Calls LLM to generate rationales.
        """
        # Formulate input for LLM to provide evidence/rationales
        prompt_input = {
            "ai_findings": ai_outputs,
            "patient_context": patient_context
        }

        # We need a new prompt for this. Let's define it here for now or 
        # assume it exists in a main PROMPTS registry.
        try:
            result = await self.ai.run_hospital_agent("CLINICAL_EXPLAINER", {"note_data": json.dumps(prompt_input)})
            
            # If result is not dict or error, return default structure
            if not isinstance(result, dict) or "error" in result:
                return {
                    "diagnosis_rationale": [],
                    "billing_rationale": [],
                    "risk_rationale": [],
                    "source_references": []
                }
            
            return {
                "diagnosis_rationale": result.get("diagnosis_rationale", []),
                "billing_rationale": result.get("billing_rationale", []),
                "risk_rationale": result.get("risk_rationale", []),
                "source_references": result.get("source_references", [])
            }
        except Exception:
            return {
                "diagnosis_rationale": [],
                "billing_rationale": [],
                "risk_rationale": [],
                "source_references": []
            }
