import re
from typing import Tuple, List, Optional
from ..core.logging import logger, request_id_contextvar

class SafetyService:
    """
    Service to detect and block unsafe clinical language including:
    - Prescriptive advice (Should, Recommend)
    - Dosage suggestions (Increase to X mg)
    - Prognostic guarantees (Will recover fully)
    """

    # Patterns that are absolutely forbidden in "Documentation Only" mode
    UNSAFE_PATTERNS = [
        (r"(?i)\b(i )?recommend\b", "Recommendation detected"),
        (r"(?i)\b(i )?suggest\b", "Suggestion detected"),
        (r"(?i)\b(i )?advise\b", "Advice detected"),
        (r"(?i)\bshould (take|start|stop|increase|decrease|continue)\b", "Prescriptive language ('should') detected"),
        (r"(?i)\bprescribe\b", "Prescription action detected"),
        (r"(?i)\bguarantee\b", "Prognostic guarantee detected"),
        (r"(?i)\bwill recover\b", "Prediction of recovery detected"),
        (r"(?i)\btry taking\b", "Treatment suggestion detected"),
    ]

    # Patterns that we can attempt to auto-fix (sanitize)
    # Maps unsafe regex -> safe replacement string (or function)
    SANITIZATION_RULES = [
        (r"(?i)\bpatient should take\b", "Patient to take"),
        (r"(?i)\brecommend starting\b", "Consideration for starting"), # Still borderline, but softer
        (r"(?i)\bprognosis is good\b", "Prognosis appears favorable"),
    ]

    @staticmethod
    def validate_content(text: str) -> Tuple[bool, List[str]]:
        """
        Checks text for unsafe patterns.
        Returns (is_safe: bool, violations: List[str])
        """
        violations = []
        for pattern, reason in SafetyService.UNSAFE_PATTERNS:
            if re.search(pattern, text):
                violations.append(reason)
        
        if violations:
            # Log the violation
            logger.warning("Safety Violation Detected", extra={"metadata": {
                "request_id": request_id_contextvar.get() or "N/A",
                "violations": violations,
                "snippet": text[:100] # Log first 100 chars only for context
            }})
            return False, violations
            
        return True, []

    @staticmethod
    def sanitize_content(text: str) -> str:
        """
        Attempts to rephrase minor safety issues into documentation style.
        """
        safe_text = text
        for pattern, replacement in SafetyService.SANITIZATION_RULES:
            safe_text = re.sub(pattern, replacement, safe_text)
        return safe_text

safety_service = SafetyService()
