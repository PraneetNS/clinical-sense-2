"""
Clinical Safety Rule Engine
============================
Deterministic, AI-free rule evaluation. Must execute < 5ms.
No extra DB calls — all data passed in from caller context.

Rules evaluated:
  1. Allergy conflict (medication name contains known allergen)
  2. Consent not documented (no consent mention in SOAP plan)
  3. High-risk diagnosis without follow-up plan
  4. Polypharmacy risk (5+ meds + patient age > 65)
"""

from __future__ import annotations
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# High-risk condition keywords (lowercase) that require explicit follow-up
# ---------------------------------------------------------------------------
_HIGH_RISK_KEYWORDS = {
    "sepsis", "stroke", "myocardial infarction", "pulmonary embolism",
    "deep vein thrombosis", "heart failure", "acute kidney injury",
    "respiratory failure", "anaphylaxis", "diabetic ketoacidosis",
    "meningitis", "pneumothorax", "hypertensive emergency",
}

_CONSENT_KEYWORDS = {"consent", "informed consent", "patient agrees", "patient consented"}


def evaluate_clinical_rules(
    soap_json: Dict[str, Any],
    meds_json: List[Dict[str, Any]],
    patient_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run all deterministic safety rules against structured encounter data.

    Args:
        soap_json:        Structured SOAP dict (keys: subjective, objective, assessment, plan)
        meds_json:        List of medication dicts with at minimum {"name": str}
        patient_context:  Dict with optional keys:
                            age (int), allergies (List[str]), active_conditions (List[str])

    Returns:
        {
            "critical_flags": [...],
            "warnings": [...],
            "risk_score": 0-100
        }
    """
    critical_flags: List[str] = []
    warnings: List[str] = []

    allergies: List[str] = [a.lower() for a in (patient_context.get("allergies") or [])]
    age: int | None = patient_context.get("age")
    active_conditions: List[str] = [c.lower() for c in (patient_context.get("active_conditions") or [])]

    soap_text = " ".join([
        str(soap_json.get("subjective", "")),
        str(soap_json.get("objective", "")),
        str(soap_json.get("assessment", "")),
        str(soap_json.get("plan", "")),
    ]).lower()

    med_names = [m.get("name", "").lower() for m in (meds_json or [])]

    # ------------------------------------------------------------------
    # RULE 1: Allergy conflict
    # ------------------------------------------------------------------
    for allergen in allergies:
        for med in med_names:
            if allergen and allergen in med:
                critical_flags.append(
                    f"ALLERGY CONFLICT: Medication '{med}' matches known allergen '{allergen}'"
                )

    # ------------------------------------------------------------------
    # RULE 2: No consent documented
    # ------------------------------------------------------------------
    consent_found = any(kw in soap_text for kw in _CONSENT_KEYWORDS)
    if not consent_found:
        warnings.append(
            "CONSENT NOT DOCUMENTED: No informed consent language found in clinical note"
        )

    # ------------------------------------------------------------------
    # RULE 3: High-risk diagnosis without follow-up mention
    # ------------------------------------------------------------------
    plan_text = str(soap_json.get("plan", "")).lower()
    has_follow_up = any(kw in plan_text for kw in ["follow", "review", "admit", "refer", "monitor"])

    for condition in active_conditions:
        for keyword in _HIGH_RISK_KEYWORDS:
            if keyword in condition:
                if not has_follow_up:
                    critical_flags.append(
                        f"HIGH-RISK DIAGNOSIS WITHOUT FOLLOW-UP: '{condition}' documented but no follow-up plan found"
                    )
                break

    # Also check assessment text for high-risk terms
    assessment_text = str(soap_json.get("assessment", "")).lower()
    for keyword in _HIGH_RISK_KEYWORDS:
        if keyword in assessment_text and not has_follow_up:
            flag = f"HIGH-RISK TERM IN ASSESSMENT WITHOUT FOLLOW-UP: '{keyword}'"
            if flag not in critical_flags:
                critical_flags.append(flag)

    # ------------------------------------------------------------------
    # RULE 4: Polypharmacy (5+ meds + age > 65)
    # ------------------------------------------------------------------
    if age is not None and age > 65 and len(med_names) >= 5:
        warnings.append(
            f"POLYPHARMACY RISK: Patient aged {age} has {len(med_names)} medications — review for interactions"
        )

    # ------------------------------------------------------------------
    # Risk score calculation (deterministic, 0-100)
    # ------------------------------------------------------------------
    risk_score = 0
    risk_score += len(critical_flags) * 30
    risk_score += len(warnings) * 10
    risk_score = min(risk_score, 100)

    return {
        "critical_flags": critical_flags,
        "warnings": warnings,
        "risk_score": risk_score,
    }
