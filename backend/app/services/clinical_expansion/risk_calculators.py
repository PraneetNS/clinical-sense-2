"""
Deterministic Risk Calculator Engine
====================================
Implements structured risk scores (BMI, Polypharmacy, Readmission, Fall).
Deterministic, AI-free. Must execute < 5ms.
"""

from typing import Any, Dict, List

def calculate_structured_risks(
    patient_context: Dict[str, Any], 
    meds: List[Dict[str, Any]], 
    vitals: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate risk scores based on patient data, vitals, and medications.
    """
    # 1. BMI Calculation
    height_m = vitals.get("height_m")
    weight_kg = vitals.get("weight_kg")
    bmi = None
    if height_m and weight_kg and height_m > 0:
        bmi = round(weight_kg / (height_m * height_m), 1)

    # 2. Polypharmacy Risk (>= 5 meds + age > 65)
    age = patient_context.get("age")
    med_count = len(meds)
    polypharmacy_risk = (age is not None and age > 65 and med_count >= 5)

    # 3. Simple Readmission Heuristic (Based on age and complexity)
    # Simple risk score (0-100)
    readmission_risk_score = 0.0
    if age is not None:
        if age > 75: readmission_risk_score += 30.0
        elif age > 65: readmission_risk_score += 15.0
        
    if med_count > 10: readmission_risk_score += 20.0
    if vitals.get("blood_pressure_sys") and vitals.get("blood_pressure_sys") > 160: 
        readmission_risk_score += 10.0
    
    # Check for known high-risk conditions in history
    high_risk_conditions = {"heart failure", "copd", "pneumonia", "diabetes"}
    active_conditions = [c.lower() for c in (patient_context.get("active_conditions") or [])]
    if any(cond in active_conditions for cond in high_risk_conditions):
        readmission_risk_score += 25.0
    
    readmission_risk_score = min(readmission_risk_score, 100.0)

    # 4. Fall Risk Heuristic
    # Simplified version of Morse Fall Scale or similar
    fall_risk_score = 0.0
    if age is not None and age > 65: fall_risk_score += 20.0
    if age is not None and age > 80: fall_risk_score += 20.0
    
    # Check for medications that increase fall risk (e.g., benzodiazepines, antihypertensives)
    fall_risk_med_keywords = {"lorazepam", "diazepam", "amlodipine", "lisinopril", "metoprolol"}
    med_names = [m.get("name", "").lower() for m in meds]
    if any(keyword in name for keyword in fall_risk_med_keywords for name in med_names):
        fall_risk_score += 30.0
        
    # Check for mobility-related conditions (e.g., neuropathy, vertigo, parkinson)
    mobility_conditions = {"parkinson", "vertigo", "neuropathy", "gait"}
    if any(cond in active_conditions for cond in mobility_conditions):
        fall_risk_score += 30.0

    fall_risk_score = min(fall_risk_score, 100.0)

    return {
        "bmi": bmi,
        "polypharmacy_risk": polypharmacy_risk,
        "fall_risk_score": fall_risk_score,
        "readmission_risk_score": readmission_risk_score
    }
