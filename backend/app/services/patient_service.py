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
        # Validate Date of Birth
        if patient_in.date_of_birth:
            now = datetime.datetime.utcnow()
            if patient_in.date_of_birth > now:
                raise HTTPException(status_code=400, detail="Date of birth cannot be in the future")
            if patient_in.date_of_birth.year < 1900:
                raise HTTPException(status_code=400, detail="Date of birth must be after 1900")
                
        try:
            db_patient = Patient(**patient_in.model_dump(), user_id=creator_id)
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
    def get_patients(db: Session, user_id: int = None, skip: int = 0, limit: int = 100):
        # Per-account data isolation: each user only sees their own patients.
        query = db.query(Patient).filter(Patient.is_deleted == False)
        if user_id:
            query = query.filter(Patient.user_id == user_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_patients_minimal(db: Session, user_id: int, skip: int = 0, limit: int = 100, search: str = None):
        """Fast list query — no heavy relationship loading, used for the patients list page."""
        from sqlalchemy import or_
        query = db.query(Patient).filter(
            Patient.is_deleted == False,
            Patient.user_id == user_id
        )
        if search:
            query = query.filter(
                or_(
                    Patient.name.ilike(f"%{search}%"),
                    Patient.mrn.ilike(f"%{search}%")
                )
            )
        return query.order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_patient(db: Session, patient_id: int, user_id: int = None):
        # Per-account isolation: user can only access their own patients.
        query = db.query(Patient).filter(Patient.id == patient_id, Patient.is_deleted == False)
        if user_id:
            query = query.filter(Patient.user_id == user_id)
        patient = query.first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found or access denied")

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
    def delete_patient(db: Session, patient_id: int, user_id: int):
        import datetime
        db_patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.user_id == user_id,
            Patient.is_deleted == False
        ).first()
        if not db_patient:
            raise HTTPException(status_code=404, detail="Patient not found or access denied")
        try:
            db_patient.is_deleted = True
            db_patient.deleted_at = datetime.datetime.utcnow()
            PatientService.log_audit(db, user_id, "delete", "Patient", patient_id, "Soft-deleted patient record")
            db.commit()
            return {"id": patient_id, "message": "Patient deleted successfully"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

    @staticmethod
    async def get_patient_report(db: Session, patient_id: int, user_id: int):
        patient = PatientService.get_patient(db, patient_id, user_id)
        from ..models import ClinicalNote, Task, Document, PatientCommunication, SecureMessage, ShiftHandover, ReadmissionRisk
        notes = db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id, ClinicalNote.is_deleted == False).order_by(ClinicalNote.created_at.desc()).all()
        tasks = db.query(Task).filter(Task.patient_id == patient_id).all()
        docs = db.query(Document).filter(Document.patient_id == patient_id, Document.is_deleted == False).all()
        
        # New models queries
        messages = db.query(SecureMessage).filter(SecureMessage.patient_id == patient_id).order_by(SecureMessage.created_at.desc()).all()
        communications = db.query(PatientCommunication).filter(PatientCommunication.patient_id == patient_id).all()
        handovers = db.query(ShiftHandover).filter(ShiftHandover.patient_id == patient_id).all()
        risks = db.query(ReadmissionRisk).filter(ReadmissionRisk.patient_id == patient_id).order_by(ReadmissionRisk.created_at.desc()).all()

        timeline = PatientService.get_unified_timeline(db, patient_id, user_id=user_id)
        
        # Prepare text for AI summary
        history_text = f"Patient: {patient.name}. \nNotes: "
        for n in notes[:5]: # Last 5 notes for summary
            history_text += f"\n- {n.title}: {n.raw_content[:200]}"
            
        try:
            from .ai.ai_service import AIService
            ai = AIService()
            summary = await ai.summarize_patient_initially(history_text)
        except Exception as e:
            print(f"AI summary failed: {e}")
            summary = "AI summary temporarily unavailable. Please review clinical notes manually."
        
        # Fetch AI encounters
        from ..models import AIEncounter
        from ..services.clinical_intelligence import _safe_json_loads
        db_encounters = db.query(AIEncounter).filter(AIEncounter.patient_id == patient_id).order_by(AIEncounter.created_at.desc()).limit(5).all()
        
        # Simple mapping to EncounterResponse structure for the report
        encounters = []
        for e in db_encounters:
            soap = _safe_json_loads(e.soap_note, {})
            
            # Map child objects to Ensure JSON fields are parsed
            meds_out = []
            for m in e.medications:
                meds_out.append({
                    "id": m.id,
                    "name": m.name,
                    "dosage": m.dosage,
                    "frequency": m.frequency,
                    "route": m.route,
                    "duration": m.duration,
                    "start_date_text": m.start_date_text,
                    "requires_confirmation": m.requires_confirmation,
                    "fields_required": _safe_json_loads(m.fields_required, []),
                    "confidence": m.confidence or "medium"
                })

            encounters.append({
                "encounter_id": e.id,
                "patient_id": e.patient_id,
                "status": e.status,
                "is_confirmed": e.is_confirmed,
                "encounter_date": e.encounter_date,
                "chief_complaint": e.chief_complaint or "",
                "soap": soap,
                "medications": meds_out,
                "diagnoses": e.diagnoses,
                "billing": e.billing_items,
                "timeline_events": e.timeline_events,
                "followups": e.followups,
                "risk_score": e.risk_score or "Low",
                "risk_flags": _safe_json_loads(e.risk_flags, []),
                "legal_flags": _safe_json_loads(e.legal_flags, []),
                "admission_required": e.admission_required,
                "icu_required": e.icu_required,
                "follow_up_days": e.follow_up_days,
                "case_status": e.case_status,
                "billing_complexity": e.billing_complexity or "medium",
                "created_at": e.created_at,
            })

        return {
            "patient": patient,
            "notes": notes,
            "tasks": tasks,
            "documents": docs,
            "timeline": timeline,
            "encounters": encounters,
            "summary": summary,
            "messages": messages,
            "communications": communications,
            "handovers": handovers,
            "risks": risks,
            "generated_at": datetime.datetime.utcnow()
        }

    @staticmethod
    def update_patient(db: Session, patient_id: int, patient_in: PatientUpdate, user_id: int):
        db_patient = db.query(Patient).filter(
            Patient.id == patient_id, 
            Patient.is_deleted == False
        ).first()
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
    def get_unified_timeline(db: Session, patient_id: int, user_id: int):
        # 0. Check access
        PatientService.get_patient(db, patient_id, user_id)
        
        from ..models import ClinicalNote, Admission, Medication, Procedure, Document, Task, MedicalHistory
        
        # 1. Fetch all relevant records
        notes = db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id, ClinicalNote.is_deleted == False).all()
        admissions = db.query(Admission).filter(Admission.patient_id == patient_id).all()
        meds = db.query(Medication).filter(Medication.patient_id == patient_id).all()
        procs = db.query(Procedure).filter(Procedure.patient_id == patient_id).all()
        docs = db.query(Document).filter(Document.patient_id == patient_id, Document.is_deleted == False).all()
        tasks = db.query(Task).filter(Task.patient_id == patient_id).all()
        history = db.query(MedicalHistory).filter(MedicalHistory.patient_id == patient_id).all()
        
        # New models
        from ..models import PatientCommunication, SecureMessage, ShiftHandover, ReadmissionRisk
        comms = db.query(PatientCommunication).filter(PatientCommunication.patient_id == patient_id).all()
        msgs = db.query(SecureMessage).filter(SecureMessage.patient_id == patient_id).all()
        handovers = db.query(ShiftHandover).filter(ShiftHandover.patient_id == patient_id).all()
        risks = db.query(ReadmissionRisk).filter(ReadmissionRisk.patient_id == patient_id).all()

        events = []
        
        for n in notes:
            events.append({
                "id": n.id,
                "type": "note",
                "title": n.title or "Clinical Note",
                "description": n.raw_content[:200] + "..." if len(n.raw_content) > 200 else n.raw_content,
                "timestamp": n.encounter_date or n.created_at,
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
                "timestamp": h.diagnosis_date or h.created_at,
                "status": h.status
            })
            
        # New Events
        for c in comms:
            events.append({
                "id": c.id,
                "type": "communication",
                "title": "Patient Communication Summary",
                "description": f"Summary generated. Diagnosis: {c.simplified_diagnosis[:50]}...",
                "timestamp": c.created_at,
                "status": "Generated"
            })
            
        for msg in msgs:
            events.append({
                "id": msg.id,
                "type": "message",
                "title": f"Message: {msg.direction}",
                "description": msg.content[:100],
                "timestamp": msg.created_at,
                "status": msg.status,
                "metadata": {"urgency": msg.urgency_score, "category": msg.category}
            })

        for ho in handovers:
            events.append({
                "id": ho.id,
                "type": "handover",
                "title": f"{ho.shift_type} Shift Handover",
                "description": "Shift summary generated.",
                "timestamp": ho.created_at,
                "author": ho.generator.full_name if ho.generator else "System",
                "status": "Completed"
            })
            
        for r in risks:
            events.append({
                "id": r.id,
                "type": "risk",
                "title": "Readmission Risk Assessment",
                "description": f"Score: {r.risk_score}, Level: {r.risk_level}",
                "timestamp": r.created_at,
                "status": r.risk_level
            })

        # Sort by timestamp descending
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events
