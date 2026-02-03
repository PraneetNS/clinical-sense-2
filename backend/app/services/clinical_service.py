from sqlalchemy.orm import Session
from ..models import Admission, MedicalHistory, Allergy, Medication, Patient, Procedure, Document, Task, BillingItem, AuditLog
from ..schemas.clinical import (
    AdmissionCreate, MedicalHistoryCreate, AllergyCreate, MedicationCreate,
    ProcedureCreate, DocumentCreate, TaskCreate, BillingItemCreate
)
from fastapi import HTTPException
import datetime

class ClinicalService:
    @staticmethod
    def log_audit(db: Session, user_id: int, action: str, entity_type: str, entity_id: int, details: str = None):
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
    def _get_patient(db: Session, patient_id: int):
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient

    # --- Admissions ---
    @staticmethod
    def create_admission(db: Session, patient_id: int, admission_in: AdmissionCreate, user_id: int = None):
        ClinicalService._get_patient(db, patient_id)
        try:
            db_obj = Admission(**admission_in.model_dump(), patient_id=patient_id)
            db.add(db_obj)
            db.flush()
            ClinicalService.log_audit(db, user_id, "create", "Admission", db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_admissions(db: Session, patient_id: int):
        return db.query(Admission).filter(Admission.patient_id == patient_id).all()

    @staticmethod
    def get_history(db: Session, patient_id: int):
        return db.query(MedicalHistory).filter(MedicalHistory.patient_id == patient_id).all()

    # --- History ---
    @staticmethod
    def create_medical_history(db: Session, patient_id: int, history_in: MedicalHistoryCreate, user_id: int = None):
        ClinicalService._get_patient(db, patient_id)
        try:
            db_obj = MedicalHistory(**history_in.model_dump(), patient_id=patient_id)
            db.add(db_obj)
            db.flush()
            ClinicalService.log_audit(db, user_id, "create", "MedicalHistory", db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # --- Allergies ---
    @staticmethod
    def create_allergy(db: Session, patient_id: int, allergy_in: AllergyCreate, user_id: int = None):
        ClinicalService._get_patient(db, patient_id)
        try:
            db_obj = Allergy(**allergy_in.model_dump(), patient_id=patient_id)
            db.add(db_obj)
            db.flush()
            ClinicalService.log_audit(db, user_id, "create", "Allergy", db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # --- Medications ---
    @staticmethod
    def create_medication(db: Session, patient_id: int, med_in: MedicationCreate, prescriber_id: int = None):
        ClinicalService._get_patient(db, patient_id)
        try:
            db_obj = Medication(**med_in.model_dump(), patient_id=patient_id, prescribed_by_id=prescriber_id)
            db.add(db_obj)
            db.flush()
            ClinicalService.log_audit(db, prescriber_id, "create", "Medication", db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_medications(db: Session, patient_id: int):
        return db.query(Medication).filter(Medication.patient_id == patient_id).all()

    # --- Procedures ---
    @staticmethod
    def create_procedure(db: Session, patient_id: int, proc_in: ProcedureCreate, performer_id: int = None):
        ClinicalService._get_patient(db, patient_id)
        try:
            db_obj = Procedure(**proc_in.model_dump(), patient_id=patient_id, performer_id=performer_id)
            db.add(db_obj)
            db.flush()
            ClinicalService.log_audit(db, performer_id, "create", "Procedure", db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_procedures(db: Session, patient_id: int):
        return db.query(Procedure).filter(Procedure.patient_id == patient_id).all()

    # --- Documents ---
    @staticmethod
    def create_document(db: Session, patient_id: int, doc_in: DocumentCreate, uploader_id: int = None):
        ClinicalService._get_patient(db, patient_id)
        try:
            db_obj = Document(**doc_in.model_dump(), patient_id=patient_id, uploader_id=uploader_id)
            db.add(db_obj)
            db.flush()
            ClinicalService.log_audit(db, uploader_id, "create", "Document", db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    @staticmethod
    def get_documents(db: Session, patient_id: int):
        return db.query(Document).filter(Document.patient_id == patient_id, Document.is_deleted == False).all()

    # --- Tasks ---
    @staticmethod
    def create_task(db: Session, task_in: TaskCreate, patient_id: int = None, user_id: int = None):
        if patient_id:
            ClinicalService._get_patient(db, patient_id)
        try:
            db_obj = Task(**task_in.model_dump(), patient_id=patient_id)
            db.add(db_obj)
            db.flush()
            ClinicalService.log_audit(db, user_id, "create", "Task", db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_tasks(db: Session, patient_id: int):
        return db.query(Task).filter(Task.patient_id == patient_id).all()
        
    @staticmethod
    def approve_task(db: Session, task_id: int, user_id: int):
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        try:
            task.status = "Approved"
            ClinicalService.log_audit(db, user_id, "approve", "Task", task.id)
            db.commit()
            db.refresh(task)
            return task
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # --- Billing ---
    @staticmethod
    def create_billing_item(db: Session, patient_id: int, item_in: BillingItemCreate, user_id: int = None):
         ClinicalService._get_patient(db, patient_id)
         try:
            db_obj = BillingItem(**item_in.model_dump(), patient_id=patient_id)
            db.add(db_obj)
            db.flush()
            ClinicalService.log_audit(db, user_id, "create", "BillingItem", db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
         except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def get_billing_items(db: Session, patient_id: int):
        return db.query(BillingItem).filter(BillingItem.patient_id == patient_id).all()

    # --- Update/Delete Helpers ---
    @staticmethod
    def update_entity(db: Session, model, entity_id: int, update_data: dict, user_id: int = None):
        db_obj = db.query(model).filter(model.id == entity_id).first()
        if not db_obj:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
        
        try:
            for field, value in update_data.items():
                if value is not None:
                    setattr(db_obj, field, value)
            
            ClinicalService.log_audit(db, user_id, "update", model.__name__, db_obj.id)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    def delete_entity(db: Session, model, entity_id: int, user_id: int = None):
        db_obj = db.query(model).filter(model.id == entity_id).first()
        if not db_obj:
            raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
        
        try:
            if hasattr(db_obj, "is_deleted"):
                 db_obj.is_deleted = True
            else:
                db.delete(db_obj)
            
            ClinicalService.log_audit(db, user_id, "delete", model.__name__, entity_id)
            db.commit()
            return {"ok": True}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
