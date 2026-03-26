"""
Clinical Intelligence Orchestrator
====================================
Transforms a single raw clinical note into a fully structured AI encounter object.

Architecture:
  1. Run 5 parallel AI pipelines (asyncio.gather)
  2. Validate each output through Pydantic schemas
  3. Persist to ai_encounters + related tables
  4. Return EncounterResponse for frontend

PHI Safety: Patient names / dates are never logged.
Idempotency: Each pipeline carries its own retry + fallback.
"""

import asyncio
import json
import time
import datetime
import uuid
import secrets
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Literal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..core.logging import logger
from ..core.config import settings
from ..models import (
    Patient,
    ClinicalNote,
    AIEncounter,
    AIGeneratedMedication,
    AIGeneratedDiagnosis,
    AIGeneratedProcedure,
    AIGeneratedBilling,
    AITimelineEvent,
    AIFollowupRecommendation,
    FollowUpCall,
    Medication,
    Procedure,
    MedicalHistory,
    BillingItem,
    Task,
    AuditLog,
    AIQualityReport,
    AIUsageMetrics,
)
from ..services.ai.ai_service import AIService
from ..services.clinical_rules import evaluate_clinical_rules
from .clinical_expansion.explainability import ExplainabilityEngine
from .clinical_expansion.drug_safety import evaluate_drug_safety
from .clinical_expansion.risk_calculators import calculate_structured_risks
from .clinical_expansion.guideline_validator import evaluate_guideline_compliance
from .clinical_expansion.differential_assistant import DifferentialAssistant
from .clinical_expansion.lab_interpreter import evaluate_labs
from .clinical_expansion.handoff import HandoffGenerator
from .clinical_expansion.workflow_engine import WorkflowAutomationEngine
from ..schemas.encounter import (
    EncounterRequest,
    EncounterResponse,
    AIMedicationOut,
    AIDiagnosisOut,
    AIProcedureOut,
    AIBillingOut,
    AITimelineEventOut,
    AIFollowupOut,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_json_loads(text: Optional[str], fallback: Any = None) -> Any:
    if not text:
        return fallback
    try:
        return json.loads(text)
    except Exception:
        return fallback


def _clamp_float(val: Any, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        return max(lo, min(hi, float(val)))
    except Exception:
        return 0.5


class PipelineResult(TypedDict):
    """Typed result from a single AI pipeline execution."""
    pipeline_name: str
    status: Literal["success", "failed", "partial"]
    data: Optional[Dict]
    error: Optional[str]
    latency_ms: float


CRITICAL_PIPELINES = {"RISK_ANALYSIS", "MEDICO_LEGAL"}


# ---------------------------------------------------------------------------
# Core Orchestrator
# ---------------------------------------------------------------------------

class ClinicalIntelligenceOrchestrator:
    """
    Executes parallel AI pipelines for a full clinical encounter.

    Usage:
        orchestrator = ClinicalIntelligenceOrchestrator(db, ai_service)
        encounter = await orchestrator.generate_encounter(request, user_id)
    """

    MAX_RETRIES = 2
    PIPELINE_TIMEOUT = 30.0   # seconds per AI call
    CONFIDENCE_REVIEW_THRESHOLD = 0.65

    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai = ai_service
        self._token_log: Dict[str, int] = {}
        
        # Expansion Engines
        self.explainer = ExplainabilityEngine(ai_service)
        self.differential_assistant = DifferentialAssistant(ai_service)
        self.handoff_generator = HandoffGenerator(ai_service)
        self.workflow_engine = WorkflowAutomationEngine(db)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def generate_encounter(
        self,
        request: EncounterRequest,
        user_id: int,
    ) -> EncounterResponse:
        """
        Main orchestration method. Runs all AI pipelines in parallel,
        persists results, and returns unified encounter response.
        """
        start_ts = time.time()

        # Validate patient access
        patient = self._get_patient(request.patient_id, user_id)

        # Build patient context for pipelines
        patient_ctx = self._build_patient_context(patient)

        # --------------- Parallel AI pipelines (resilient) ---------------
        pipeline_configs = [
            ("ENCOUNTER_EXTRACTOR", "encounter", lambda: self._run_pipeline("ENCOUNTER_EXTRACTOR", request.raw_note, "encounter")),
            ("SOAP", "soap", lambda: self._run_pipeline("SOAP", request.raw_note, "soap")),
            ("MEDICATION_STRUCTURING", "medications", lambda: self._run_pipeline("MEDICATION_STRUCTURING", request.raw_note, "medications")),
            ("DIAGNOSIS_CODING", "diagnoses", lambda: self._run_pipeline_with_context("DIAGNOSIS_CODING", request.raw_note, patient_ctx, "diagnoses")),
            ("BILLING_INTELLIGENCE", "billing", lambda: self._run_pipeline_with_context("BILLING_INTELLIGENCE", json.dumps({"raw_note": request.raw_note, "patient_context": patient_ctx}), None, "billing")),
            ("CASE_INTELLIGENCE", "case", lambda: self._run_pipeline("CASE_INTELLIGENCE", request.raw_note, "case")),
            ("RISK_ANALYSIS", "risk", lambda: self._run_pipeline("RISK_ANALYSIS", request.raw_note, "risk")),
            ("MEDICO_LEGAL", "legal", lambda: self._run_pipeline("MEDICO_LEGAL", request.raw_note, "legal")),
        ]

        async def _run_pipeline_safe(name: str, label: str, coro_fn) -> PipelineResult:
            t0 = time.time()
            try:
                data = await coro_fn()
                latency = round((time.time() - t0) * 1000, 1)
                has_data = isinstance(data, dict) and len(data) > 0
                return PipelineResult(
                    pipeline_name=name,
                    status="success" if has_data else "partial",
                    data=data,
                    error=None,
                    latency_ms=latency,
                )
            except Exception as e:
                latency = round((time.time() - t0) * 1000, 1)
                logger.error(f"Pipeline '{label}' ({name}) failed: {e}")
                return PipelineResult(
                    pipeline_name=name,
                    status="failed",
                    data={},
                    error=str(e),
                    latency_ms=latency,
                )

        pipeline_results: List[PipelineResult] = await asyncio.gather(
            *[_run_pipeline_safe(name, label, fn) for name, label, fn in pipeline_configs]
        )

        # Build pipeline_statuses list and extract data by label
        pipeline_statuses = []
        _pipeline_data = {}
        for cfg, result in zip(pipeline_configs, pipeline_results):
            name, label, _ = cfg
            pipeline_statuses.append({
                "pipeline_name": result["pipeline_name"],
                "status": result["status"],
                "error": result["error"],
                "latency_ms": result["latency_ms"],
            })
            _pipeline_data[label] = result["data"] or {}

        encounter_data = _pipeline_data["encounter"]
        soap_data = _pipeline_data["soap"]
        med_data = _pipeline_data["medications"]
        diag_data = _pipeline_data["diagnoses"]
        billing_data = _pipeline_data["billing"]
        case_data = _pipeline_data["case"]
        risk_data = _pipeline_data["risk"]
        legal_data = _pipeline_data["legal"]

        # --------------- 2. Quality & Safety Evaluation ---------------
        # Model version for observability
        model_version = settings.GROQ_MODEL_NAME if hasattr(settings, "GROQ_MODEL_NAME") else "llama-3-70b"

        # Merge preliminary outputs to provide context for evaluator
        prelim_merged = self._merge_pipeline_outputs(
            encounter_data, soap_data, med_data,
            diag_data, billing_data, case_data,
            risk_data, legal_data,
        )


        # Run deterministic clinical rule engine (safe, <5ms)
        safety_results = evaluate_clinical_rules(
            soap_json=soap_data,
            meds_json=prelim_merged["medications"],
            patient_context=patient_ctx
        )

        # Run AI Quality Evaluator Agent
        try:
            eval_input = json.dumps({
                "raw_note": request.raw_note,
                "structured_output": prelim_merged
            })
            quality_data = await self._run_pipeline("QUALITY_EVALUATOR", eval_input, "quality")
        except Exception as e:
            logger.error(f"Quality evaluator failed: {e}")
            quality_data = {
                "confidence_score": 0.0,
                "compliance_score": 0.0,
                "risk_level": "HIGH",
                "reasoning": "Evaluator execution error"
            }

        total_latency_ms = int((time.time() - start_ts) * 1000)

        # --------------- 4. Clinical Expansion Pipeline (v2) ---------------
        expansion_data = {
            "rationale_json": None,
            "drug_safety_flags": None,
            "structured_risk_metrics": None,
            "guideline_flags": None,
            "differential_output": None,
            "lab_interpretation": None,
            "handoff_sbar": None,
        }

        if request.evidence_mode_enabled:
            try:
                # A. Deterministic modules
                expansion_data["drug_safety_flags"] = evaluate_drug_safety(
                    prelim_merged["medications"], 
                    patient_ctx.get("allergies", []), 
                    patient_ctx
                )
                
                vitals = self._extract_vitals_from_soap(soap_data)
                expansion_data["structured_risk_metrics"] = calculate_structured_risks(
                    patient_ctx, prelim_merged["medications"], vitals
                )

                expansion_data["guideline_flags"] = evaluate_guideline_compliance(
                    soap_data, prelim_merged["medications"], patient_ctx
                )

                expansion_data["lab_interpretation"] = evaluate_labs(soap_data, patient_ctx)

                # B. LLM-powered modules (Parallel)
                (
                    rationale, 
                    differentials, 
                    sbar
                ) = await asyncio.gather(
                    self.explainer.generate_clinical_rationale(prelim_merged, patient_ctx),
                    self.differential_assistant.generate_differentials(soap_data, patient_ctx),
                    self.handoff_generator.generate_sbar(soap_data),
                    return_exceptions=True
                )
                
                expansion_data["rationale_json"] = rationale if not isinstance(rationale, Exception) else None
                expansion_data["differential_output"] = differentials if not isinstance(differentials, Exception) else None
                expansion_data["handoff_sbar"] = sbar if not isinstance(sbar, Exception) else None

                # C. Workflow Engine
                # Staged tasks are returned but not yet promoted to DB Task model
                # they will be shown in the UI for confirmation.
                staged_tasks = self.workflow_engine.stage_tasks(
                    encounter_id=0, # Placeholder
                    patient_id=request.patient_id,
                    user_id=user_id,
                    follow_up_recommendations=prelim_merged.get("followups", [])
                )
                expansion_data["staged_tasks"] = staged_tasks

            except Exception as e:
                logger.error(f"Clinical expansion failed: {e}")

        # --------------- 5. Persist to database ---------------
        encounter = self._persist_encounter(
            patient_id=request.patient_id,
            user_id=user_id,
            request=request,
            merged=prelim_merged,
            latency_ms=total_latency_ms,
            model_version=model_version,
            quality_data=quality_data,
            safety_results=safety_results,
            token_usage_total=sum(self._token_log.values()) if self._token_log else 0,
            expansion_data=expansion_data,
            pipeline_statuses=pipeline_statuses,
        )

        logger.info(
            "Clinical intelligence encounter generated (v3 resilient)",
            extra={"metadata": {
                "encounter_id": encounter.id,
                "latency_ms": total_latency_ms,
                "evidence_mode": request.evidence_mode_enabled,
                "risk_level": quality_data.get("risk_level", "HIGH"),
                "pipeline_failures": [p["pipeline_name"] for p in pipeline_statuses if p["status"] == "failed"],
            }},
        )

        return self._build_response(encounter, prelim_merged, pipeline_statuses)

    # ------------------------------------------------------------------
    # Encounter confirmation (doctor clicks "Confirm & Save")
    # ------------------------------------------------------------------

    async def confirm_encounter(
        self,
        encounter_id: int,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Promotes AI-generated encounter data into the live clinical tables.
        All records marked as is_confirmed = True.
        Only the assigned clinician or admin can confirm.
        """
        encounter = (
            self.db.query(AIEncounter)
            .filter(AIEncounter.id == encounter_id)
            .first()
        )
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")
        if encounter.is_confirmed:
            raise HTTPException(status_code=409, detail="Encounter already confirmed")

        # 1. Promote AI Encounter to a real Clinical Note
        note = ClinicalNote(
            user_id=user_id,
            patient_id=encounter.patient_id,
            title=f"AI Encounter - {encounter.chief_complaint or 'General Consultation'}",
            raw_content=encounter.raw_note,
            structured_content=encounter.soap_note,
            note_type="SOAP",
            status="finalized",
            encounter_date=encounter.encounter_date,
        )
        self.db.add(note)
        self.db.flush()
        encounter.note_id = note.id

        # 2. Promote medications
        confirmed_meds = []
        for ai_med in encounter.medications:
            if not ai_med.requires_confirmation or ai_med.is_confirmed:
                med = Medication(
                    patient_id=encounter.patient_id,
                    prescribed_by_id=user_id,
                    source_note_id=note.id,
                    name=ai_med.name,
                    dosage=ai_med.dosage,
                    frequency=ai_med.frequency,
                    status="Active",
                )
                self.db.add(med)
                self.db.flush()
                ai_med.is_confirmed = True
                ai_med.confirmed_medication_id = med.id
                confirmed_meds.append(ai_med.name)

        # 3. Promote procedures
        confirmed_procs = []
        for ai_proc in encounter.procedures:
            proc = Procedure(
                patient_id=encounter.patient_id,
                performer_id=user_id,
                source_note_id=note.id,
                name=ai_proc.name,
                code=ai_proc.code,
                notes=ai_proc.notes,
                date=encounter.encounter_date,
            )
            self.db.add(proc)
            self.db.flush()
            ai_proc.is_confirmed = True
            ai_proc.confirmed_procedure_id = proc.id
            confirmed_procs.append(ai_proc.name)

        # 4. Promote billing items
        confirmed_billing = []
        for ai_bill in encounter.billing_items:
            if not ai_bill.requires_review or (ai_bill.confidence and ai_bill.confidence >= self.CONFIDENCE_REVIEW_THRESHOLD):
                bill = BillingItem(
                    patient_id=encounter.patient_id,
                    item_name=ai_bill.description,
                    code=ai_bill.cpt_code,
                    cost=ai_bill.estimated_cost or 0.0,
                    status="Pending",
                )
                self.db.add(bill)
                self.db.flush()
                ai_bill.is_confirmed = True
                ai_bill.confirmed_billing_id = bill.id
                confirmed_billing.append(ai_bill.cpt_code)

        # 5. Promote follow-ups as tasks
        confirmed_tasks = []
        for fu in encounter.followups:
            days = fu.suggested_days or 7
            task = Task(
                patient_id=encounter.patient_id,
                assigned_to_id=user_id,
                source_note_id=note.id,
                description=f"[AI Follow-up] {fu.recommendation}",
                priority="High" if fu.urgency == "stat" else ("Medium" if fu.urgency == "urgent" else "Low"),
                category=fu.follow_up_type or "General",
                is_auto_generated=True,
                status="Pending",
                due_date=datetime.datetime.utcnow() + datetime.timedelta(days=days),
            )
            self.db.add(task)
            self.db.flush()
            fu.is_confirmed = True
            fu.converted_task_id = task.id
            confirmed_tasks.append(fu.recommendation[:60])

        # 6. Promote diagnoses to Medical History
        confirmed_diagnoses = []
        for diag in encounter.diagnoses:
            history = MedicalHistory(
                patient_id=encounter.patient_id,
                condition_name=diag.condition_name,
                diagnosis_date=encounter.encounter_date,
                status="Active",
                notes=f"AI Inferred (Confidence: {diag.confidence_score}). {diag.reasoning or ''}",
            )
            self.db.add(history)
            diag.is_confirmed = True
            confirmed_diagnoses.append(diag.condition_name)

        # Mark encounter as confirmed
        encounter.is_confirmed = True
        encounter.status = "confirmed"
        encounter.confirmed_at = datetime.datetime.utcnow()
        encounter.confirmed_by_id = user_id

        # 7. Auto-create Patient Portal Link
        from ..models import PatientPortalLink
        portal_token = secrets.token_urlsafe(32)
        portal_link = PatientPortalLink(
            encounter_id=encounter_id,
            patient_id=encounter.patient_id,
            token=portal_token,
            expires_at=datetime.datetime.utcnow() + timedelta(hours=48)
        )
        self.db.add(portal_link)

        # 8. Schedule AI Follow-up Phone Call (T+24h)
        # Fetch patient phone number
        patient_record = self.db.query(Patient).filter(Patient.id == encounter.patient_id).first()
        if patient_record and patient_record.phone:
            followup_call = FollowUpCall(
                patient_id=encounter.patient_id,
                encounter_id=encounter_id,
                phone_number=patient_record.phone,
                scheduled_at=datetime.datetime.utcnow() + timedelta(hours=24),
                status="Scheduled"
            )
            self.db.add(followup_call)
            self.db.flush()
            
            # TODO: Trigger background task (Celery or background_tasks)
            # Example: background_tasks.add_task(initiate_twilio_call, followup_call_id=followup_call.id)
            logger.info(f"Follow-up call scheduled for encounter {encounter_id} at {followup_call.scheduled_at}")

        # Audit log
        self._log_audit(user_id, "confirm_encounter", "AIEncounter", encounter_id)
        self.db.commit()

        return {
            "encounter_id": encounter_id,
            "confirmed": True,
            "confirmed_medications": confirmed_meds,
            "confirmed_procedures": confirmed_procs,
            "confirmed_diagnoses": confirmed_diagnoses,
            "confirmed_billing": confirmed_billing,
            "confirmed_tasks": confirmed_tasks,
        }

    # ------------------------------------------------------------------
    # Internal — AI Pipeline runners
    # ------------------------------------------------------------------

    async def _run_pipeline(
        self,
        prompt_key: str,
        input_text: str,
        label: str,
        fallback: Optional[Dict] = None,
    ) -> Dict:
        """
        Runs a single AI pipeline with retry + structured JSON validation.
        On final failure, returns a safe fallback dict.
        """
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                result = await asyncio.wait_for(
                    self.ai.run_hospital_agent(prompt_key, {"note": input_text}),
                    timeout=self.PIPELINE_TIMEOUT,
                )
                # Track token usage if available (Groq SDK may surface usage)
                self._token_log[label] = self._token_log.get(label, 0)
                if isinstance(result, dict) and "error" not in result:
                    return result
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(1.5 * (attempt + 1))
            except asyncio.TimeoutError:
                logger.warning(f"Pipeline '{label}' timed out (attempt {attempt+1})")
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Pipeline '{label}' error: {str(e)}")
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(1.0)

        logger.warning(f"Pipeline '{label}' failed after {self.MAX_RETRIES+1} attempts — using fallback")
        return fallback or {}

    async def _run_pipeline_with_context(
        self,
        prompt_key: str,
        input_text: str,
        context: Optional[Dict],
        label: str,
    ) -> Dict:
        merged_input = {"note": input_text}
        if context:
            merged_input["patient_context"] = context
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                result = await asyncio.wait_for(
                    self.ai.run_hospital_agent(prompt_key, merged_input),
                    timeout=self.PIPELINE_TIMEOUT,
                )
                if isinstance(result, dict) and "error" not in result:
                    return result
            except Exception as e:
                logger.error(f"Pipeline '{label}' context error: {str(e)}")
            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(1.5)
        return {}

    # ------------------------------------------------------------------
    # Internal — Data merging
    # ------------------------------------------------------------------

    def _merge_pipeline_outputs(
        self,
        encounter_data: Dict,
        soap_data: Dict,
        med_data: Dict,
        diag_data: Dict,
        billing_data: Dict,
        case_data: Dict,
        risk_data: Dict,
        legal_data: Dict,
    ) -> Dict:
        """
        Merges outputs from all pipelines into a single canonical dict.
        encounter_data is the primary source; others are supplements.
        """
        # Medications: prefer dedicated medication pipeline over encounter extractor
        medications = (
            med_data.get("medications")
            or encounter_data.get("medications")
            or []
        )

        # Diagnoses: prefer dedicated coding pipeline
        diagnoses = (
            diag_data.get("diagnoses")
            or encounter_data.get("diagnoses")
            or []
        )

        # Billing
        billing_items = billing_data.get("billing_items") or []

        # Case intelligence
        case_status = (
            case_data.get("case_status")
            or encounter_data.get("case_status", "active")
        )
        follow_up_days = (
            case_data.get("follow_up_days")
            or encounter_data.get("follow_up_days")
        )
        admission_required = (
            case_data.get("admission_recommended")
            or encounter_data.get("admission_required", False)
        )
        icu_required = (
            case_data.get("icu_recommended")
            or encounter_data.get("icu_required", False)
        )

        # Risk
        risk_score = (
            case_data.get("risk_score")
            or risk_data.get("risk_score", "Low")
        )
        risk_flags = (
            case_data.get("risk_flags")
            or risk_data.get("red_flags")
            or []
        )

        # Legal
        legal_flags = (
            case_data.get("legal_flags")
            or legal_data.get("missing_info")
            or []
        )

        # Follow-ups
        followups = case_data.get("follow_up_recommendations") or []

        return {
            "soap": soap_data,
            "chief_complaint": encounter_data.get("chief_complaint", ""),
            "medications": medications,
            "diagnoses": diagnoses,
            "procedures": encounter_data.get("procedures", []),
            "timeline_events": encounter_data.get("timeline_events", []),
            "billing_items": billing_items,
            "billing_complexity": (
                billing_data.get("overall_complexity")
                or encounter_data.get("billing_complexity", "medium")
            ),
            "case_status": case_status,
            "follow_up_days": follow_up_days,
            "admission_required": bool(admission_required),
            "icu_required": bool(icu_required),
            "risk_score": risk_score,
            "risk_flags": risk_flags,
            "legal_flags": legal_flags,
            "followups": followups,
        }

    # ------------------------------------------------------------------
    # Internal — Persistence
    # ------------------------------------------------------------------

    def _persist_encounter(
        self,
        patient_id: int,
        user_id: int,
        request: EncounterRequest,
        merged: Dict,
        latency_ms: int,
        model_version: str,
        quality_data: Dict,
        safety_results: Dict,
        token_usage_total: int,
        expansion_data: Optional[Dict] = None,
        pipeline_statuses: Optional[List[Dict]] = None,
    ) -> AIEncounter:
        """
        Persists the full encounter, related items, quality report, and usage metrics.
        Now includes expansion data for v2 and pipeline statuses for v3.
        """
        try:
            # Root encounter
            encounter = AIEncounter(
                patient_id=patient_id,
                created_by_id=user_id,
                encounter_date=request.encounter_date or datetime.datetime.utcnow(),
                raw_note=request.raw_note,
                soap_note=json.dumps(merged.get("soap", {})),
                chief_complaint=merged.get("chief_complaint", "")[:500],
                case_status=merged.get("case_status", "active"),
                billing_complexity=merged.get("billing_complexity", "medium"),
                admission_required=merged.get("admission_required", False),
                icu_required=merged.get("icu_required", False),
                follow_up_days=merged.get("follow_up_days"),
                risk_score=merged.get("risk_score", "Low"),
                risk_flags=json.dumps(merged.get("risk_flags", [])),
                legal_flags=json.dumps(merged.get("legal_flags", [])),
                pipeline_statuses=json.dumps(pipeline_statuses or []),
                status="ready",
                token_usage=json.dumps(self._token_log),
                model_version=model_version,
                processing_latency_ms=latency_ms,
            )
            self.db.add(encounter)
            self.db.flush()  # Get encounter.id

            # Governance: Quality Report
            quality_report = AIQualityReport(
                encounter_id=encounter.id,
                confidence_score=_clamp_float(quality_data.get("confidence_score", 0.0)),
                compliance_score=_clamp_float(quality_data.get("compliance_score", 0.0)),
                billing_accuracy_score=quality_data.get("billing_accuracy_score"),
                hallucination_flags=quality_data.get("hallucination_flags"),
                missing_critical_fields=quality_data.get("missing_critical_fields"),
                clinical_safety_flags=safety_results,
                risk_level=quality_data.get("risk_level", "HIGH"),
                model_version=model_version,
                
                # Clinical Sense v2 Expansion
                evidence_mode_enabled=request.evidence_mode_enabled,
                rationale_json=expansion_data.get("rationale_json") if expansion_data else None,
                drug_safety_flags=expansion_data.get("drug_safety_flags") if expansion_data else None,
                structured_risk_metrics=expansion_data.get("structured_risk_metrics") if expansion_data else None,
                guideline_flags=expansion_data.get("guideline_flags") if expansion_data else None,
                differential_output=expansion_data.get("differential_output") if expansion_data else None,
                lab_interpretation=expansion_data.get("lab_interpretation") if expansion_data else None,
                handoff_sbar=expansion_data.get("handoff_sbar") if expansion_data else None,
            )
            self.db.add(quality_report)

            # Observability: Usage Metrics
            usage = AIUsageMetrics(
                encounter_id=encounter.id,
                user_id=user_id,
                tokens_used=token_usage_total,
                latency_ms=latency_ms,
                accepted_without_edit=False, # Default until confirmed
                edit_distance_score=None
            )
            self.db.add(usage)

            # Medications
            for med in merged.get("medications", []):
                self.db.add(AIGeneratedMedication(
                    encounter_id=encounter.id,
                    patient_id=patient_id,
                    name=med.get("name", "Unknown"),
                    dosage=med.get("dosage"),
                    frequency=med.get("frequency"),
                    route=med.get("route"),
                    duration=med.get("duration"),
                    start_date_text=med.get("start_date_text"),
                    requires_confirmation=bool(med.get("requires_confirmation", False)),
                    fields_required=json.dumps(med.get("fields_required", [])),
                    confidence=med.get("confidence", "medium"),
                ))

            # Diagnoses
            for diag in merged.get("diagnoses", []):
                self.db.add(AIGeneratedDiagnosis(
                    encounter_id=encounter.id,
                    patient_id=patient_id,
                    condition_name=diag.get("condition_name", "Unknown"),
                    icd10_code=diag.get("icd10_code"),
                    confidence_score=_clamp_float(diag.get("confidence_score", 0.5)),
                    reasoning=diag.get("reasoning"),
                    is_primary=bool(diag.get("is_primary", False)),
                ))

            # Procedures
            for proc in merged.get("procedures", []):
                self.db.add(AIGeneratedProcedure(
                    encounter_id=encounter.id,
                    patient_id=patient_id,
                    name=proc.get("name", "Unknown"),
                    code=proc.get("code"),
                    notes=proc.get("notes"),
                    confidence=proc.get("confidence", "medium"),
                ))

            # Billing
            for item in merged.get("billing_items", []):
                conf = _clamp_float(item.get("confidence", 0.5))
                self.db.add(AIGeneratedBilling(
                    encounter_id=encounter.id,
                    patient_id=patient_id,
                    cpt_code=item.get("cpt_code"),
                    description=item.get("description", "Billing item"),
                    estimated_cost=item.get("estimated_cost"),
                    complexity=item.get("complexity", "medium"),
                    confidence=conf,
                    requires_review=bool(item.get("requires_review", True)),
                    review_reason=item.get("review_reason"),
                ))

            # Timeline events
            for evt in merged.get("timeline_events", []):
                self.db.add(AITimelineEvent(
                    encounter_id=encounter.id,
                    patient_id=patient_id,
                    event_type=evt.get("event_type", "other"),
                    event_description=evt.get("event_description", ""),
                    event_date_text=evt.get("event_date_text"),
                    severity=evt.get("severity", "info"),
                ))

            # Follow-up recommendations
            for fu in merged.get("followups", []):
                self.db.add(AIFollowupRecommendation(
                    encounter_id=encounter.id,
                    patient_id=patient_id,
                    recommendation=fu.get("recommendation", ""),
                    follow_up_type=fu.get("follow_up_type"),
                    urgency=fu.get("urgency", "routine"),
                    suggested_days=fu.get("suggested_days"),
                ))

            self._log_audit(user_id, "generate_encounter", "AIEncounter", encounter.id)
            self.db.commit()
            self.db.refresh(encounter)
            return encounter

        except Exception as e:
            self.db.rollback()
            logger.error(f"Encounter persistence failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save encounter data.")

    # ------------------------------------------------------------------
    # Internal — Response builder
    # ------------------------------------------------------------------

    def _build_response(self, encounter: AIEncounter, merged: Dict, pipeline_statuses: Optional[List[Dict]] = None) -> EncounterResponse:
        """Converts DB encounter object + merged pipeline dict into a response schema."""
        return EncounterResponse(
            encounter_id=encounter.id,
            patient_id=encounter.patient_id,
            status=encounter.status,
            is_confirmed=encounter.is_confirmed,
            encounter_date=encounter.encounter_date,
            chief_complaint=encounter.chief_complaint or "",
            soap=merged.get("soap", {}),
            medications=[
                AIMedicationOut(
                    id=m.id,
                    name=m.name,
                    dosage=m.dosage,
                    frequency=m.frequency,
                    route=m.route,
                    duration=m.duration,
                    start_date_text=m.start_date_text,
                    requires_confirmation=m.requires_confirmation,
                    fields_required=_safe_json_loads(m.fields_required, []),
                    confidence=m.confidence or "medium",
                )
                for m in encounter.medications
            ],
            diagnoses=[
                AIDiagnosisOut(
                    id=d.id,
                    condition_name=d.condition_name,
                    icd10_code=d.icd10_code,
                    confidence_score=d.confidence_score or 0.5,
                    reasoning=d.reasoning,
                    is_primary=d.is_primary,
                )
                for d in encounter.diagnoses
            ],
            procedures=[
                AIProcedureOut(
                    id=p.id,
                    name=p.name,
                    code=p.code,
                    notes=p.notes,
                    confidence=p.confidence or "medium",
                )
                for p in encounter.procedures
            ],
            billing=[
                AIBillingOut(
                    id=b.id,
                    cpt_code=b.cpt_code,
                    description=b.description,
                    estimated_cost=b.estimated_cost,
                    complexity=b.complexity or "medium",
                    confidence=b.confidence or 0.5,
                    requires_review=b.requires_review,
                    review_reason=b.review_reason,
                )
                for b in encounter.billing_items
            ],
            timeline_events=[
                AITimelineEventOut(
                    id=t.id,
                    event_type=t.event_type,
                    event_description=t.event_description,
                    event_date_text=t.event_date_text,
                    severity=t.severity or "info",
                )
                for t in encounter.timeline_events
            ],
            followups=[
                AIFollowupOut(
                    id=f.id,
                    recommendation=f.recommendation,
                    follow_up_type=f.follow_up_type,
                    urgency=f.urgency,
                    suggested_days=f.suggested_days,
                )
                for f in encounter.followups
            ],
            risk_score=encounter.risk_score or "Low",
            risk_flags=_safe_json_loads(encounter.risk_flags, []),
            legal_flags=_safe_json_loads(encounter.legal_flags, []),
            admission_required=encounter.admission_required,
            icu_required=encounter.icu_required,
            follow_up_days=encounter.follow_up_days,
            case_status=encounter.case_status,
            billing_complexity=encounter.billing_complexity or "medium",
            ai_watermark="AI-GENERATED DRAFT ⚠️ — Requires licensed clinician review and confirmation before any clinical action.",
            pipeline_statuses=pipeline_statuses or _safe_json_loads(encounter.pipeline_statuses, []),
            created_at=encounter.created_at,
        )

    # ------------------------------------------------------------------
    # Internal — Helpers
    # ------------------------------------------------------------------

    def _get_patient(self, patient_id: int, user_id: int) -> Patient:
        # Relaxed check: clinical staff can access any active patient for AI orchestration
        patient = (
            self.db.query(Patient)
            .filter(Patient.id == patient_id, Patient.is_deleted == False)
            .first()
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found or access denied")
        return patient

    def _build_patient_context(self, patient: Patient) -> Dict:
        """Builds a safe (non-PHI) context dict for AI pipeline enrichment."""
        age = None
        if patient.date_of_birth:
            today = datetime.date.today()
            dob = patient.date_of_birth
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        meds = [m.name for m in patient.medications if m.status == "Active"][:10]
        allergies = [a.allergen for a in patient.allergies][:10]
        history = [h.condition_name for h in patient.medical_history if h.status == "Active"][:10]

        return {
            "age": age,
            "gender": patient.gender,
            "active_medications": meds,
            "allergies": allergies,
            "active_conditions": history,
        }

    def _extract_vitals_from_soap(self, soap_json: Dict) -> Dict:
        """Extracts simple vitals from SOAP objective text using regex."""
        import re
        objective = str(soap_json.get("objective", "")).lower()
        
        vitals = {
            "weight_kg": None,
            "height_m": None,
            "blood_pressure_sys": None,
            "blood_pressure_dia": None
        }
        
        # Weight (kg)
        w_match = re.search(r'(\d+(\.\d+)?)\s*kg', objective)
        if w_match: vitals["weight_kg"] = float(w_match.group(1))
        
        # Height (m)
        h_match = re.search(r'(\d+(\.\d+)?)\s*m', objective)
        if h_match: vitals["height_m"] = float(h_match.group(1))
        
        # BP
        bp_match = re.search(r'bp\s*[:=]?\s*(\d{2,3})/(\d{2,3})', objective)
        if bp_match:
            vitals["blood_pressure_sys"] = int(bp_match.group(1))
            vitals["blood_pressure_dia"] = int(bp_match.group(2))
            
        return vitals

    def _log_audit(self, user_id: int, action: str, entity_type: str, entity_id: int):
        try:
            log = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                timestamp=datetime.datetime.utcnow(),
                details="Clinical Intelligence Orchestrator",
            )
            self.db.add(log)
        except Exception:
            pass  # Audit failure must never block clinical workflow
