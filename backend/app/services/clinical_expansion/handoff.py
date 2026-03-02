"""
Clinical Handoff Generator (SBAR)
=================================
LLM-powered generation of structured clinical handoffs using the SBAR framework.
SBAR: Situation, Background, Assessment, Recommendation.
"""

from typing import Any, Dict
from ...services.ai.ai_service import AIService

class HandoffGenerator:
    """
    Generates structured SBAR handoff summaries based on SOAP.
    """
    def __init__(self, ai_service: AIService):
        self.ai = ai_service

    async def generate_sbar(
        self, 
        soap_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for SBAR. Calls LLM to provide structured handoff.
        """
        try:
            result = await self.ai.run_hospital_agent("SBAR_HANDOFF", {"soap": soap_json})
            
            # Formulate structured output
            return {
                "situation": result.get("situation", "Situation unknown"),
                "background": result.get("background", "Background unknown"),
                "assessment": result.get("assessment", "Assessment unknown"),
                "recommendation": result.get("recommendation", "Recommendation unknown"),
            }
        except Exception:
            return {
                "situation": "Situation unknown",
                "background": "Background unknown",
                "assessment": "Assessment unknown",
                "recommendation": "Recommendation unknown",
            }
        
