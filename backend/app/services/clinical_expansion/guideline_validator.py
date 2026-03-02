"""
Clinical Guideline Validator Engine
====================================
Rule-based guideline reminders for chronic disease management and screening.
Deterministic, AI-free. Must execute < 5ms.
"""

from typing import Any, Dict, List

def evaluate_guideline_compliance(
    soap_json: Dict[str, Any], 
    meds_json: List[Dict[str, Any]], 
    patient_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run rule-based guideline checks against SOAP, Medications, and Context.
    """
    guideline_gaps: List[str] = []
    preventive_care_suggestions: List[str] = []

    active_conditions = [c.lower() for c in (patient_context.get("active_conditions") or [])]
    med_names = [m.get("name", "").lower() for m in meds_json]
    
    soap_text = " ".join([
        str(soap_json.get("subjective", "")),
        str(soap_json.get("objective", "")),
        str(soap_json.get("assessment", "")),
        str(soap_json.get("plan", ""))
    ]).lower()
    
    age = patient_context.get("age")
    is_smoker = "smoker" in soap_text or "tobacco" in soap_text or "smoking" in soap_text

    # 1. Hypertension guidelines (JNC8)
    # Check for HTN condition and ACE/ARB mention
    if any("hypertension" in cond or "htn" in cond for cond in active_conditions):
        ace_arb_keywords = {"lisinopril", "enalapril", "losartan", "valsartan", "irbesartan", "candesartan", "telmisartan"}
        if not any(kw in name for kw in ace_arb_keywords for name in med_names):
            # Check if mentioned in SOAP (already taking) 
            if not any(kw in soap_text for kw in ace_arb_keywords):
                guideline_gaps.append(
                    "HYPERTENSION: Patient has HTN but no ACE inhibitor or ARB medication mentioned or currently prescribed."
                )

    # 2. Smoking screening (USPSTF)
    if age is not None and 50 <= age <= 80 and is_smoker:
        if "lung cancer screening" not in soap_text and "ct scan" not in soap_text:
            preventive_care_suggestions.append(
                "SMOKING SCREENING: Smoker age 50-80 should be evaluated for annual low-dose CT lung cancer screening."
            )

    # 3. Diabetes management (ADA)
    if "diabetes" in active_conditions or "dm" in active_conditions:
        if "hba1c" not in soap_text and "hemoglobin a1c" not in soap_text:
             guideline_gaps.append(
                "DIABETES: No recent HbA1c mentioned in current encounter or plan for follow-up testing."
            )
        # Check for foot exam mention
        if "foot exam" not in soap_text and "feet" not in soap_text:
            preventive_care_suggestions.append(
                "DIABETES: Ensure annual comprehensive foot examination is performed for diabetic patients."
            )

    # 4. Colon Cancer Screening (USPSTF)
    if age is not None and 45 <= age <= 75:
        screening_keywords = {"colonoscopy", "fit test", "fecal occult", "screening"}
        if not any(kw in soap_text for kw in screening_keywords):
             preventive_care_suggestions.append(
                "PREVENTIVE CARE: Ensure patient age 45-75 is up to date with colorectal cancer screening."
            )

    return {
        "guideline_gaps": guideline_gaps,
        "preventive_care_suggestions": preventive_care_suggestions
    }
