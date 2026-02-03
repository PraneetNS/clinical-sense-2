from sqlalchemy.orm import Session
from ..models import Patient, AuditLog
from ..schemas.patient import PatientCreate, PatientUpdate
from fastapi import HTTPException
import datetime

class PatientService:
    @staticmethod
    def log_audit(db: Session, user_id: int, action: str, entity_type: str, entity_id: int, details: str = None):
        if not user_id: return
        audit = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(audit)

    @staticmethod
    def create_patient(db: Session, patient_in: PatientCreate, creator_id: int = None):
        try:
            db_patient = Patient(**patient_in.model_dump())
            db.add(db_patient)
            db.flush()
            PatientService.log_audit(db, creator_id, "create", "Patient", db_patient.id)
            db.commit()
            db.refresh(db_patient)
            return db_patient
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_patients(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Patient).offset(skip).limit(limit).all()

    @staticmethod
    def get_patient(db: Session, patient_id: int):
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
             raise HTTPException(status_code=404, detail="Patient not found")
        
        # Calculate billing totals
        total = 0.0
        outstanding = 0.0
        for item in patient.billing_items:
            total += (item.cost or 0.0)
            if item.status != "Paid":
                outstanding += (item.cost or 0.0)
        
        patient.total_billing_amount = total
        patient.outstanding_billing_amount = outstanding
        
        return patient

    @staticmethod
    async def get_patient_report(db: Session, patient_id: int):
        patient = PatientService.get_patient(db, patient_id)
        from ..models import ClinicalNote, Task, Document
        notes = db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id, ClinicalNote.is_deleted == False).order_by(ClinicalNote.created_at.desc()).all()
        tasks = db.query(Task).filter(Task.patient_id == patient_id).all()
        docs = db.query(Document).filter(Document.patient_id == patient_id, Document.is_deleted == False).all()
        timeline = PatientService.get_unified_timeline(db, patient_id)
        
        # Prepare text for AI summary
        history_text = f"Patient: {patient.name}. \nNotes: "
        for n in notes[:5]: # Last 5 notes for summary
            history_text += f"\n- {n.title}: {n.raw_content[:200]}"
            
        from .ai.ai_service import AIService
        ai = AIService()
        summary = await ai.summarize_patient_initially(history_text)
        
        return {
            "patient": patient,
            "notes": notes,
            "tasks": tasks,
            "documents": docs,
            "timeline": timeline,
            "summary": summary,
            "generated_at": datetime.datetime.utcnow()
        }

    @staticmethod
    def update_patient(db: Session, patient_id: int, patient_in: PatientUpdate, user_id: int = None):
        db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not db_patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        try:
            update_data = patient_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_patient, field, value)
            
            PatientService.log_audit(db, user_id, "update", "Patient", db_patient.id)
            db.commit()
            db.refresh(db_patient)
            return db_patient
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    @staticmethod
    def get_unified_timeline(db: Session, patient_id: int):
        from ..models import ClinicalNote, Admission, Medication, Procedure, Document, Task, MedicalHistory
        
        # 1. Fetch all relevant records
        notes = db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id, ClinicalNote.is_deleted == False).all()
        admissions = db.query(Admission).filter(Admission.patient_id == patient_id).all()
        meds = db.query(Medication).filter(Medication.patient_id == patient_id).all()
        procs = db.query(Procedure).filter(Procedure.patient_id == patient_id).all()
        docs = db.query(Document).filter(Document.patient_id == patient_id, Document.is_deleted == False).all()
        tasks = db.query(Task).filter(Task.patient_id == patient_id).all()
        history = db.query(MedicalHistory).filter(MedicalHistory.patient_id == patient_id).all()
        
        events = []
        
        for n in notes:
            events.append({
                "id": n.id,
                "type": "note",
                "title": n.title or "Clinical Note",
                "description": n.raw_content[:200] + "..." if len(n.raw_content) > 200 else n.raw_content,
                "timestamp": n.created_at,
                "author": n.owner.full_name if n.owner else "System",
                "status": n.status,
                "metadata": {"note_type": n.note_type}
            })
            
        for a in admissions:
            events.append({
                "id": a.id,
                "type": "admission",
                "title": f"Admission: {a.reason[:50]}...",
                "description": f"Ward: {a.ward}, Room: {a.room}",
                "timestamp": a.admission_date,
                "status": a.status
            })
            
        for m in meds:
            events.append({
                "id": m.id,
                "type": "medication",
                "title": f"Meds: {m.name}",
                "description": f"Dosage: {m.dosage}, Frequency: {m.frequency}",
                "timestamp": m.created_at,
                "status": m.status
            })
            
        for p in procs:
            events.append({
                "id": p.id,
                "type": "procedure",
                "title": f"Proc: {p.name}",
                "description": p.notes,
                "timestamp": p.date,
                "author": p.performer.full_name if p.performer else None
            })
            
        for d in docs:
            events.append({
                "id": d.id,
                "type": "document",
                "title": d.title,
                "description": d.summary,
                "timestamp": d.created_at,
                "metadata": {"file_type": d.file_type, "url": d.file_url}
            })
            
        for t in tasks:
            events.append({
                "id": t.id,
                "type": "task",
                "title": "Task Assigned",
                "description": t.description,
                "timestamp": t.created_at,
                "status": t.status,
                "author": t.assignee.full_name if t.assignee else None
            })
            
        for h in history:
            events.append({
                "id": h.id,
                "type": "history",
                "title": f"Medical Condition: {h.condition_name}",
                "description": f"Status: {h.status}. {h.notes or ''}",
                "timestamp": h.created_at,
                "status": h.status
            })
            
        # Sort by timestamp descending
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events
