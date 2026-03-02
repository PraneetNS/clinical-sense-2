"""
Laboratory Interpretation Engine
================================
Rule-based lab threshold detection and interpretation.
Deterministic, AI-free. Must execute < 5ms.
"""

import re
from typing import Any, Dict, List

# Basic deterministic thresholds (Common values, simplified)
_LAB_THRESHOLDS = {
    "HbA1c": {"low": 0, "high": 6.5, "unit": "%"},
    "Systolic BP": {"low": 90, "high": 140, "unit": "mmHg"},
    "Diastolic BP": {"low": 60, "high": 90, "unit": "mmHg"},
    "LDL": {"low": 0, "high": 130, "unit": "mg/dL"},
    "Glucose": {"low": 70, "high": 100, "unit": "mg/dL"},
    "Hemoglobin": {"low": 13.5, "high": 17.5, "unit": "g/dL", "gender_adj": True}, # 12.0 - 15.5 for women
}

def evaluate_labs(
    soap_json: Dict[str, Any], 
    patient_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run rule-based lab threshold checks against SOAP objective findings.
    """
    abnormal_labs: List[Dict[str, Any]] = []
    interpretations: List[str] = []
    suggested_followups: List[str] = []

    objective_text = str(soap_json.get("objective", "")).lower()
    gender = str(patient_context.get("gender", "")).lower()

    # Regex matches (Simplified logic for parsing, may not handle all formats)
    # Examples: "HbA1c = 7.2%", "LDL 145 mg/dL", "BP 150/95"
    
    # 1. Glycated Hemoglobin (HbA1c)
    hba1c_match = re.search(r'hba1c\s*[:=]?\s*(\d+(\.\d+)?)', objective_text)
    if hba1c_match:
        val = float(hba1c_match.group(1))
        if val >= _LAB_THRESHOLDS["HbA1c"]["high"]:
            abnormal_labs.append({
                "lab": "HbA1c",
                "value": val,
                "threshold": _LAB_THRESHOLDS["HbA1c"]["high"],
                "unit": "%",
                "status": "High"
            })
            interpretations.append(f"Elevated HbA1c ({val}%) may indicate uncontrolled hyperglycemia or newly diagnosed diabetes.")
            suggested_followups.append("Consider confirming with repeat HbA1c or fasting plasma glucose.")

    # 2. Blood Pressure
    bp_match = re.search(r'bp\s*[:=]?\s*(\d{2,3})/(\d{2,3})', objective_text)
    if bp_match:
        sys = int(bp_match.group(1))
        dia = int(bp_match.group(2))
        if sys >= _LAB_THRESHOLDS["Systolic BP"]["high"] or dia >= _LAB_THRESHOLDS["Diastolic BP"]["high"]:
            abnormal_labs.append({
                "lab": f"Blood Pressure ({sys}/{dia})",
                "value": f"{sys}/{dia}",
                "threshold": "140/90",
                "unit": "mmHg",
                "status": "High"
            })
            interpretations.append(f"Elevated Blood Pressure ({sys}/{dia}) noted in current exam.")
            suggested_followups.append("Ensure measurement was taken with proper cuff size and patient at rest. Monitor for sustained hypertension.")

    # 3. LDL Cholesterol
    ldl_match = re.search(r'ldl\s*[:=]?\s*(\d+(\.\d+)?)', objective_text)
    if ldl_match:
        val = float(ldl_match.group(1))
        if val >= _LAB_THRESHOLDS["LDL"]["high"]:
            abnormal_labs.append({
                "lab": "LDL",
                "value": val,
                "threshold": _LAB_THRESHOLDS["LDL"]["high"],
                "unit": "mg/dL",
                "status": "High"
            })
            interpretations.append(f"Elevated LDL ({val} mg/dL) indicates hyperlipidemia.")
            suggested_followups.append("Review lipid management guidelines and cardiovascular risk profile for statin eligibility.")

    # 4. Hemoglobin (Age/Gender adjustment placeholder)
    hb_match = re.search(r'hemoglobin\s*[:=]?\s*(\d+(\.\d+)?)', objective_text) or re.search(r'hgb\s*[:=]?\s*(\d+(\.\d+)?)', objective_text)
    if hb_match:
        val = float(hb_match.group(1))
        threshold_lo = _LAB_THRESHOLDS["Hemoglobin"]["low"]
        if gender == "female": threshold_lo = 12.0
        
        if val < threshold_lo:
            abnormal_labs.append({
                "lab": "Hemoglobin",
                "value": val,
                "threshold": threshold_lo,
                "unit": "g/dL",
                "status": "Low"
            })
            interpretations.append(f"Low Hemoglobin ({val} g/dL) indicates anemia.")
            suggested_followups.append("Evaluate for potential causes: iron deficiency, B12/folate deficiency, chronic kidney disease, or occult blood loss.")

    return {
        "abnormal_labs": abnormal_labs,
        "interpretations": interpretations,
        "suggested_followups": suggested_followups
    }
