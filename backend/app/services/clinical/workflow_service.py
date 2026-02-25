from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import (
    ClinicalNote, Patient, ClinicalTrajectory, 
    DischargeReadiness, Task, Admission
)
from app.services.ai.ai_service import AIService
from app.core.logging import logger
import datetime
import json

class WorkflowService:
    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai = ai_service

    async def analyze_trajectory(self, note_id: int):
        """
        Compares current note with the previous note to determine trajectory.
        """
        current_note = self.db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
        if not current_note or not current_note.patient_id:
            return

        # Get previous note
        previous_note = self.db.query(ClinicalNote).filter(
            ClinicalNote.patient_id == current_note.patient_id,
            ClinicalNote.created_at < current_note.created_at,
            ClinicalNote.is_deleted == False
        ).order_by(ClinicalNote.created_at.desc()).first()

        context = {
            "current_note": current_note.raw_content,
            "previous_note": previous_note.raw_content if previous_note else "No previous history."
        }
        
        result = await self.ai.run_hospital_agent("TRAJECTORY", context)
        
        if "error" in result:
            logger.error(f"Trajectory analysis failed: {result['error']}")
            return

        trajectory = ClinicalTrajectory(
            patient_id=current_note.patient_id,
            note_id=note_id,
            trend=result.get("trend", "Uncertain"),
            risk_score=result.get("risk_score", 0),
            confidence_score=result.get("confidence_score", 0.0),
            key_changes=json.dumps(result.get("key_changes", []))
        )
        self.db.add(trajectory)
        self.db.commit()

    async def generate_patient_summary(self, note_id: int):
        """
        Generates a patient-friendly summary of the note.
        """
        note = self.db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
        if not note: 
            return

        context = {"note_text": note.raw_content}
        result = await self.ai.run_hospital_agent("PATIENT_SUMMARY", context)
        
        if "error" in result:
            return

        summary_text = result.get("summary", "")
        # You might want to save instructions/warnings as well, for now we save the summary text
        # If the prompt returns JSON with instructions, we can store it as JSON string
        full_summary_json = json.dumps(result)
        
        note.patient_summary = full_summary_json
        self.db.commit()

    async def evaluate_discharge_readiness(self, patient_id: int):
        """
        Evaluates if the patient is ready for discharge using clinical context.
        """
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient: return

        # Get active admission
        admission = self.db.query(Admission).filter(
            Admission.patient_id == patient_id, 
            Admission.status == "Active"
        ).first()

        # Get latest notes (last 3 for context)
        notes = self.db.query(ClinicalNote).filter(
            ClinicalNote.patient_id == patient_id
        ).order_by(ClinicalNote.created_at.desc()).limit(3).all()

        # Get pending tasks
        pending_tasks = self.db.query(Task).filter(
            Task.patient_id == patient_id,
            Task.status == "Pending"
        ).all()

        # Get active medications
        active_meds = [m.name for m in patient.medications if m.status == "Active"]
        
        context = {
            "patient_info": {
                "age": (datetime.datetime.utcnow() - patient.date_of_birth).days // 365 if patient.date_of_birth else "Unknown",
                "gender": patient.gender or "Unknown"
            },
            "recent_clinical_notes": [n.raw_content[:500] for n in notes],
            "pending_medical_tasks": [t.description for t in pending_tasks],
            "active_medications": active_meds,
            "admission_reason": admission.reason if admission else "Unknown"
        }
        
        result = await self.ai.run_hospital_agent("DISCHARGE_READINESS", context)
        
        if "error" in result:
             return None

        readiness = DischargeReadiness(
            admission_id=admission.id if admission else None,
            patient_id=patient.id,
            readiness_score=result.get("readiness_score", 0),
            missing_requirements=json.dumps(result.get("missing_requirements", [])),
            suggested_date=result.get("suggested_date", "Uncertain")
        )
        self.db.add(readiness)
        self.db.commit()
        return readiness

        return readiness

    async def get_patient_workflow_dashboard(self, patient_id: int) -> Dict[str, Any]:
        """
        Returns aggregated workflow data: Trajectory, Tasks, Discharge.
        """
        trajectory = self.db.query(ClinicalTrajectory).filter(
            ClinicalTrajectory.patient_id == patient_id
        ).order_by(ClinicalTrajectory.created_at.desc()).first()
        
        readiness = self.db.query(DischargeReadiness).filter(
            DischargeReadiness.patient_id == patient_id
        ).order_by(DischargeReadiness.created_at.desc()).first()
        
        tasks_query = self.db.query(Task).filter(
            Task.patient_id == patient_id, 
            Task.status == "Pending"
        )
        tasks_count = tasks_query.count()
        tasks_list = tasks_query.order_by(Task.created_at.desc()).limit(3).all()
        
        return {
            "trajectory": {
                "trend": trajectory.trend if trajectory else "No Data",
                "risk_score": trajectory.risk_score if trajectory else 0,
                "confidence_score": trajectory.confidence_score if trajectory else 0.0
            },
            "discharge": {
                "score": readiness.readiness_score if readiness else 0,
                "target": readiness.suggested_date if readiness else "TBD",
                "missing": json.loads(readiness.missing_requirements) if readiness and readiness.missing_requirements else []
            },
            "pending_tasks": tasks_count,
            "pending_tasks_list": [
                {
                    "id": t.id,
                    "description": t.description,
                    "due_date": t.due_date,
                    "priority": t.priority
                } for t in tasks_list
            ]
        }

    async def process_auto_tasks(self, note_id: int):
        """
        Extracts tasks with detailed attributes.
        This supersedes the HOS automation for detailed clinical workflow.
        """
        note = self.db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
        if not note:
             return

        context = {
            "note_text": note.raw_content,
            "type": note.note_type
        }
        
        result = await self.ai.run_hospital_agent("AUTOMATION", context)
        
        if "error" in result: 
            return

        tasks = result.get("tasks", [])
        for task_def in tasks:
            task = Task(
                patient_id=note.patient_id,
                assigned_to_id=note.user_id,
                source_note_id=note.id,
                description=task_def.get("description", "AI Task"),
                priority=task_def.get("priority", "Medium"),
                category=task_def.get("category", "General"),
                is_auto_generated=True,
                status="Pending",
                due_date=datetime.datetime.utcnow() + datetime.timedelta(days=2) # Default
            )
            self.db.add(task)
        
        # Follow-ups (Optional)
        follow_ups = result.get("follow_ups", [])
        for fu in follow_ups:
            task = Task(
                patient_id=note.patient_id,
                assigned_to_id=note.user_id,
                source_note_id=note.id,
                description=f"Follow-up: {fu}",
                priority="High",
                category="Follow-up",
                is_auto_generated=True,
                status="Pending",
                due_date=datetime.datetime.utcnow() + datetime.timedelta(days=14)
            )
            self.db.add(task)

        # Billing Suggestions (Optional logging or Task)
        billing = result.get("billing_suggestions", [])
        if billing:
             # Just log or create a billing review task
            pass

        self.db.commit()
