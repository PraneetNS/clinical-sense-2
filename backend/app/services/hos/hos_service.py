import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import (
    Patient, ClinicalNote, Admission, User, 
    HospitalPatientRisk, DoctorAIMetrics, 
    Task, BillingItem, AuditLog
)
from app.services.ai.ai_service import AIService
from app.core.logging import logger

class HOSService:
    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai = ai_service

    # 1. COMMAND CENTER
    async def get_command_center_overview(self) -> Dict[str, Any]:
        """
        Aggregates real-time hospital metrics.
        """
        try:
            total_active_patients = self.db.query(Patient).filter(Patient.status == "Active").count()
            
            # Critical / High Risk
            high_risk = self.db.query(HospitalPatientRisk).filter(
                HospitalPatientRisk.risk_level.in_(["Critical", "High"])
            ).count()
            
            # Pending Labs/Tasks
            pending_tasks = self.db.query(Task).filter(Task.status == "Pending").count()
            
            # ICU/Bed - Mock data for now as we don't have detailed bed model yet
            # But we can infer from Admissions
            active_admissions = self.db.query(Admission).filter(Admission.status == "Active").count()
            
            # Staff Burnout
            avg_burnout = self.db.query(func.avg(DoctorAIMetrics.burnout_probability)).scalar() or 0.0

            return {
                "critical_patient_count": high_risk,
                "active_patients": total_active_patients,
                "pending_urgent_tasks": pending_tasks,
                "icu_occupancy_percent": min(100, int((active_admissions / 50) * 100)), # Mock 50 beds
                "staff_burnout_risk_avg": round(avg_burnout, 2),
                "system_status": "Operational"
            }
        except Exception as e:
            logger.error(f"Command Center Error: {e}")
            return {"error": "Failed to load command center"}

    # 2. DETERIORATION PREDICTOR
    async def run_deterioration_scan(self):
        """
        Scans all active patients for risk.
        Designed to run in background.
        """
        active_patients = self.db.query(Patient).filter(Patient.status == "Active").all()
        
        for patient in active_patients:
            # Gather context
            # Get latest vitals from notes (heuristic)
            latest_note = self.db.query(ClinicalNote).filter(
                ClinicalNote.patient_id == patient.id
            ).order_by(ClinicalNote.created_at.desc()).first()
            
            if not latest_note:
                continue

            context = {
                "age": (datetime.datetime.utcnow() - patient.date_of_birth).days // 365,
                "gender": patient.gender,
                "recent_note": latest_note.raw_content[:1000] # Truncate for token limits
            }

            # AI Analysis
            result = await self.ai.run_hospital_agent("DETERIORATION", context)
            
            if "error" in result:
                continue

            # Update DB
            risk_entry = self.db.query(HospitalPatientRisk).filter(
                HospitalPatientRisk.patient_id == patient.id
            ).first()
            
            if not risk_entry:
                risk_entry = HospitalPatientRisk(patient_id=patient.id)
                self.db.add(risk_entry)
            
            risk_entry.risk_score = result.get("risk_score", 0)
            risk_entry.risk_level = result.get("risk_level", "Low")
            risk_entry.suggested_actions = str(result.get("suggested_actions", []))
            risk_entry.last_updated = datetime.datetime.utcnow()
            
        self.db.commit()

    # 3. BED & FLOW
    async def optimize_bed_flow(self) -> Dict[str, Any]:
        """
        AI optimization for bed management.
        """
        active_admissions = self.db.query(Admission).filter(Admission.status == "Active").count()
        context = {
            "current_occupancy": active_admissions,
            "total_beds": 50, # Mock
            "pending_admissions": 5 # Mock
        }
        
        return await self.ai.run_hospital_agent("FLOW", context)

    # 4. STAFF INTELLIGENCE
    async def update_staff_metrics(self):
        doctors = self.db.query(User).filter(User.role == "doctor").all()
        
        for doc in doctors:
            # Calc metrics
            active_patients = self.db.query(Patient).filter(Patient.user_id == doc.id, Patient.status == "Active").count()
            notes_7d = self.db.query(ClinicalNote).filter(
                ClinicalNote.user_id == doc.id,
                ClinicalNote.created_at >= datetime.datetime.utcnow() - datetime.timedelta(days=7)
            ).count()
            
            context = {
                "active_patients": active_patients,
                "notes_last_week": notes_7d
            }
            
            result = await self.ai.run_hospital_agent("STAFF", context)
            
            if "error" in result:
                continue

            metric = self.db.query(DoctorAIMetrics).filter(DoctorAIMetrics.user_id == doc.id).first()
            if not metric:
                metric = DoctorAIMetrics(user_id=doc.id)
                self.db.add(metric)
            
            metric.workload_score = result.get("workload_score", 0)
            metric.burnout_probability = result.get("burnout_risk", 0.0)
            metric.active_patients_count = active_patients
            metric.notes_last_7d = notes_7d
            metric.last_updated = datetime.datetime.utcnow()
            
        self.db.commit()

    # 5. AUTOMATION ENGINE
    async def process_note_automation(self, note_id: int):
        """
        Called after note save. Extracts tasks/billing.
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

        # Auto-create Tasks
        tasks = result.get("tasks", [])
        for task_def in tasks:
            task = Task(
                patient_id=note.patient_id,
                assigned_to_id=note.user_id,
                description=task_def.get("description", "AI Auto-Task"),
                status="Pending",
                due_date=datetime.datetime.utcnow() + datetime.timedelta(days=1)
            )
            self.db.add(task)
            
        # Suggestions for billing could be stored in a separate table or just logged/returned
        # For MVP, we effectively 'log' them as tasks or just print
        if result.get("billing_suggestions"):
             # Create a billing suggestion task/alert
            billing_task = Task(
                patient_id=note.patient_id,
                assigned_to_id=note.user_id,
                description=f"Review Billing: {result.get('billing_suggestions')}",
                status="Pending"
            )
            self.db.add(billing_task)

        self.db.commit()

    # 6. EXECUTIVE ANALYTICS
    async def get_executive_analytics(self) -> Dict[str, Any]:
        # Aggregate high level data
        total_revenue_potential = self.db.query(func.sum(BillingItem.cost)).scalar() or 0
        
        context = {
            "total_revenue_potential": total_revenue_potential,
            "total_patients": self.db.query(Patient).count(),
            "notes_count": self.db.query(ClinicalNote).count()
        }
        
        return await self.ai.run_hospital_agent("EXECUTIVE", context)
