"""
Deterministic Drug Interaction & Safety Engine
==============================================
Rule-based drug interaction and safety checks.
Deterministic, AI-free. Must execute < 5ms.
"""

from typing import Any, Dict, List, Set

# Initial interaction mapping (In production, this would be a full clinical database)
_CRITICAL_INTERACTIONS = {
    ("warfarin", "aspirin"): "Increased risk of severe bleeding.",
    ("sildenafil", "nitroglycerin"): "Life-threatening hypotension risk.",
    ("lisinopril", "spironolactone"): "Risk of severe hyperkalemia.",
    ("digoxin", "amiodarone"): "Increased digoxin toxicity risk.",
    ("citalopram", "tramadol"): "Risk of serotonin syndrome.",
}

_MODERATE_INTERACTIONS = {
    ("metformin", "furosemide"): "Possible altered metformin levels/renal impact.",
    ("ibuprofen", "lisinopril"): "Reduced antihypertensive effect and renal risk.",
    ("simvastatin", "amlodipine"): "Increased simvastatin exposure risk.",
}

def evaluate_drug_safety(
    med_list: List[Dict[str, Any]], 
    allergy_list: List[str], 
    patient_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run rule-based drug safety checks against current med list and patient data.
    """
    critical_interactions = []
    moderate_interactions = []
    contraindications = []

    # Prepare med names (normalized)
    med_names = [m.get("name", "").lower().strip() for m in med_list]
    med_set = set(med_names)
    
    # 1. Check for Drug-Drug Interactions
    # Check all pairs
    for (m1, m2), msg in _CRITICAL_INTERACTIONS.items():
        if m1 in med_set and m2 in med_set:
            critical_interactions.append({
                "drugs": [m1, m2],
                "severity": "CRITICAL",
                "message": msg
            })
            
    for (m1, m2), msg in _MODERATE_INTERACTIONS.items():
        if m1 in med_set and m2 in med_set:
            moderate_interactions.append({
                "drugs": [m1, m2],
                "severity": "MODERATE",
                "message": msg
            })

    # 2. Check for Allergy Conflicts
    normalized_allergies = [a.lower().strip() for a in (allergy_list or [])]
    for med in med_names:
        for allergy in normalized_allergies:
            if allergy and (allergy in med or med in allergy):
                contraindications.append({
                    "type": "ALLERGY",
                    "drug": med,
                    "reason": f"Patient has documented allergy to '{allergy}'"
                })

    # 3. Renal Contraindication Placeholder (Simplistic)
    # If eGFR (estimated glomerular filtration rate) is available in context
    egfr = patient_context.get("egfr")
    if egfr is not None and egfr < 30:
        if "metformin" in med_set:
            contraindications.append({
                "type": "RENAL",
                "drug": "metformin",
                "reason": f"Metformin contraindicated in severe renal impairent (eGFR {egfr} < 30)"
            })
        if "nsaid" in med_set or "ibuprofen" in med_set or "naproxen" in med_set:
             contraindications.append({
                "type": "RENAL",
                "drug": "NSAIDs",
                "reason": f"NSAID use should be avoided in severe renal impairment (eGFR {egfr} < 30)"
            })

    return {
        "critical_interactions": critical_interactions,
        "moderate_interactions": moderate_interactions,
        "contraindications": contraindications
    }
