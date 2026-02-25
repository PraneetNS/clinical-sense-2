"""
Unit tests for the Clinical Intelligence Platform.
Run with: python -m pytest tests/test_clinical_intelligence.py -v
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# ─── Helpers under test ───────────────────────────────────────────────────
from app.services.clinical_intelligence import (
    ClinicalIntelligenceOrchestrator,
    _safe_json_loads,
    _clamp_float,
)
from app.schemas.encounter import EncounterRequest


# ─────────────────────────────────────────────────────────────────────────
# Utility function tests
# ─────────────────────────────────────────────────────────────────────────

class TestUtils:
    def test_safe_json_loads_valid(self):
        assert _safe_json_loads('["a","b"]') == ["a", "b"]

    def test_safe_json_loads_invalid(self):
        assert _safe_json_loads("not json", fallback={"x": 1}) == {"x": 1}

    def test_safe_json_loads_none(self):
        assert _safe_json_loads(None, fallback=[]) == []

    def test_clamp_float_in_range(self):
        assert _clamp_float(0.75) == 0.75

    def test_clamp_float_above_range(self):
        assert _clamp_float(1.5) == 1.0

    def test_clamp_float_below_range(self):
        assert _clamp_float(-0.3) == 0.0

    def test_clamp_float_string_number(self):
        assert _clamp_float("0.88") == 0.88

    def test_clamp_float_bad_value(self):
        assert _clamp_float("bad") == 0.5


# ─────────────────────────────────────────────────────────────────────────
# Medication extraction — merge logic
# ─────────────────────────────────────────────────────────────────────────

class TestMedicationMerge:
    """Tests the _merge_pipeline_outputs medication priority logic."""

    def _make_orchestrator(self):
        db = MagicMock()
        ai = MagicMock()
        return ClinicalIntelligenceOrchestrator(db, ai)

    def test_medication_structuring_pipeline_takes_priority(self):
        orch = self._make_orchestrator()
        med_pipeline = {"medications": [{"name": "Amoxicillin", "dosage": "500mg", "frequency": "TID", "route": "oral", "duration": "7 days", "start_date_text": None, "requires_confirmation": False, "fields_required": [], "confidence": "high"}]}
        encounter_pipeline = {"medications": [{"name": "OldDrug", "confidence": "low"}]}

        merged = orch._merge_pipeline_outputs(
            encounter_data=encounter_pipeline, soap_data={},
            med_data=med_pipeline, diag_data={},
            billing_data={}, case_data={}, risk_data={}, legal_data={}
        )
        assert merged["medications"][0]["name"] == "Amoxicillin"

    def test_no_medications_returns_empty(self):
        orch = self._make_orchestrator()
        merged = orch._merge_pipeline_outputs(
            {}, {}, {}, {}, {}, {}, {}, {}
        )
        assert merged["medications"] == []

    def test_requires_confirmation_flag_from_missing_date(self):
        """Meds missing a start_date should be flagged for confirmation."""
        med = {
            "name": "Warfarin", "dosage": "5mg", "frequency": "daily",
            "route": "oral", "duration": None, "start_date_text": None,
            "requires_confirmation": True, "fields_required": ["start_date"],
            "confidence": "medium"
        }
        orch = self._make_orchestrator()
        merged = orch._merge_pipeline_outputs(
            {}, {}, {"medications": [med]}, {}, {}, {}, {}, {}
        )
        assert merged["medications"][0]["requires_confirmation"] is True
        assert "start_date" in merged["medications"][0]["fields_required"]


# ─────────────────────────────────────────────────────────────────────────
# Diagnosis coding — merge logic
# ─────────────────────────────────────────────────────────────────────────

class TestDiagnosisCoding:

    def _make_orchestrator(self):
        return ClinicalIntelligenceOrchestrator(MagicMock(), MagicMock())

    def test_diagnosis_pipeline_takes_priority(self):
        orch = self._make_orchestrator()
        diag_data = {"diagnoses": [{"condition_name": "Community Acquired Pneumonia", "icd10_code": "J18.9", "confidence_score": 0.92, "reasoning": "Fever + LLL dullness", "is_primary": True}]}
        merged = orch._merge_pipeline_outputs(
            {}, {}, {}, diag_data, {}, {}, {}, {}
        )
        assert merged["diagnoses"][0]["icd10_code"] == "J18.9"
        assert merged["diagnoses"][0]["confidence_score"] == 0.92

    def test_icd10_code_optional(self):
        orch = self._make_orchestrator()
        diag_data = {"diagnoses": [{"condition_name": "Unspecified condition", "icd10_code": None, "confidence_score": 0.4, "is_primary": False}]}
        merged = orch._merge_pipeline_outputs(
            {}, {}, {}, diag_data, {}, {}, {}, {}
        )
        assert merged["diagnoses"][0]["icd10_code"] is None

    def test_confidence_score_clamped(self):
        # confidence_score out of range should be clamped on persist
        assert _clamp_float(1.5) == 1.0
        assert _clamp_float(-0.1) == 0.0


# ─────────────────────────────────────────────────────────────────────────
# Billing intelligence
# ─────────────────────────────────────────────────────────────────────────

class TestBillingIntelligence:

    def _make_orchestrator(self):
        return ClinicalIntelligenceOrchestrator(MagicMock(), MagicMock())

    def test_low_confidence_billing_flagged_for_review(self):
        orch = self._make_orchestrator()
        billing_data = {
            "billing_items": [
                {"cpt_code": "99213", "description": "Office visit", "estimated_cost": 80.0, "complexity": "low", "confidence": 0.55, "requires_review": True, "review_reason": "Multiple chronic conditions"},
            ],
            "overall_complexity": "medium",
        }
        merged = orch._merge_pipeline_outputs(
            {}, {}, {}, {}, billing_data, {}, {}, {}
        )
        assert merged["billing_items"][0]["requires_review"] is True
        assert "multiple chronic" in merged["billing_items"][0]["review_reason"].lower()

    def test_high_confidence_billing_does_not_require_review(self):
        orch = self._make_orchestrator()
        billing_data = {
            "billing_items": [
                {"cpt_code": "99215", "description": "High complexity visit", "estimated_cost": 250.0, "complexity": "high", "confidence": 0.93, "requires_review": False, "review_reason": None},
            ],
            "overall_complexity": "high",
        }
        merged = orch._merge_pipeline_outputs(
            {}, {}, {}, {}, billing_data, {}, {}, {}
        )
        assert merged["billing_items"][0]["requires_review"] is False

    def test_billing_complexity_from_pipeline_preferred(self):
        orch = self._make_orchestrator()
        billing_data = {"billing_items": [], "overall_complexity": "high"}
        encounter_data = {"billing_complexity": "low"}
        merged = orch._merge_pipeline_outputs(
            encounter_data, {}, {}, {}, billing_data, {}, {}, {}
        )
        assert merged["billing_complexity"] == "high"


# ─────────────────────────────────────────────────────────────────────────
# Case intelligence
# ─────────────────────────────────────────────────────────────────────────

class TestCaseIntelligence:

    def _make_orchestrator(self):
        return ClinicalIntelligenceOrchestrator(MagicMock(), MagicMock())

    def test_admission_flag_from_case_pipeline(self):
        orch = self._make_orchestrator()
        case_data = {
            "case_status": "needs_review",
            "requires_follow_up": True,
            "follow_up_days": 2,
            "alert_required": True,
            "admission_recommended": True,
            "icu_recommended": False,
            "risk_score": "High",
            "risk_flags": ["Sepsis screen positive"],
            "legal_flags": ["Consent not documented"],
            "follow_up_recommendations": []
        }
        merged = orch._merge_pipeline_outputs(
            {}, {}, {}, {}, {}, case_data, {}, {}
        )
        assert merged["admission_required"] is True
        assert "Sepsis screen positive" in merged["risk_flags"]

    def test_legal_flags_populated(self):
        orch = self._make_orchestrator()
        case_data = {
            "case_status": "active",
            "legal_flags": ["No informed consent documented", "Missing vital signs"],
            "risk_flags": [],
            "risk_score": "Low",
            "follow_up_recommendations": []
        }
        merged = orch._merge_pipeline_outputs(
            {}, {}, {}, {}, {}, case_data, {}, {}
        )
        assert len(merged["legal_flags"]) == 2

    def test_risk_fallback_to_risk_pipeline(self):
        """When case pipeline has no risk_score, should fall back to risk analysis pipeline."""
        orch = self._make_orchestrator()
        risk_data = {"risk_score": "Medium", "red_flags": ["Elevated WBC"]}
        merged = orch._merge_pipeline_outputs(
            {}, {}, {}, {}, {}, {}, risk_data, {}
        )
        assert merged["risk_score"] == "Medium"


# ─────────────────────────────────────────────────────────────────────────
# Schema validation
# ─────────────────────────────────────────────────────────────────────────

class TestSchemas:

    def test_encounter_request_valid(self):
        req = EncounterRequest(
            patient_id=1,
            raw_note="Patient presents with chest pain, diaphoresis, and SOB since 2 hours.",
            encounter_date=datetime.utcnow()
        )
        assert req.patient_id == 1
        assert len(req.raw_note) > 10

    def test_encounter_request_note_too_short(self):
        with pytest.raises(Exception):
            EncounterRequest(patient_id=1, raw_note="Hi")

    def test_encounter_request_note_stripped(self):
        req = EncounterRequest(
            patient_id=1,
            raw_note="  Patient has fever and cough.  "
        )
        assert req.raw_note == "Patient has fever and cough."
