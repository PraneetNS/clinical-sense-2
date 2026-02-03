from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form
import shutil
import os
import uuid
from sqlalchemy.orm import Session
from typing import List, Optional

from ...db.session import get_db
from ...api.deps import get_current_user
from ...models import User
from ... import models
from ...schemas.clinical import (
    AdmissionCreate, AdmissionResponse,
    MedicalHistoryCreate, MedicalHistoryResponse,
    AllergyCreate, AllergyResponse, AllergyUpdate,
    MedicationCreate, MedicationResponse, MedicationUpdate,
    ProcedureCreate, ProcedureResponse, ProcedureUpdate,
    DocumentCreate, DocumentResponse, DocumentUpdate,
    TaskResponse, TaskCreate, TaskUpdate,
    BillingItemResponse, BillingItemCreate, BillingItemUpdate
)
from ...services.clinical_service import ClinicalService

router = APIRouter()

# --- Admissions ---
@router.get("/{patient_id}/admissions", response_model=List[AdmissionResponse])
def get_admissions(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.get_admissions(db, patient_id)

@router.post("/{patient_id}/admissions", response_model=AdmissionResponse)
def create_admission(
    patient_id: int,
    admission_in: AdmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.create_admission(db, patient_id, admission_in, user_id=current_user.id)

@router.put("/admissions/{admission_id}", response_model=AdmissionResponse)
def update_admission(
    admission_id: int,
    admission_in: AdmissionCreate, # Reusing create schema or add AdmissionUpdate if needed
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.update_entity(db, models.Admission, admission_id, admission_in.model_dump(exclude_unset=True), user_id=current_user.id)

@router.delete("/admissions/{admission_id}")
def delete_admission(
    admission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.delete_entity(db, models.Admission, admission_id, user_id=current_user.id)

@router.get("/{patient_id}/history", response_model=List[MedicalHistoryResponse])
def get_medical_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.get_history(db, patient_id)

# --- History ---
@router.post("/{patient_id}/history", response_model=MedicalHistoryResponse)
def create_medical_history(
    patient_id: int,
    history_in: MedicalHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.create_medical_history(db, patient_id, history_in, user_id=current_user.id)

@router.put("/history/{history_id}", response_model=MedicalHistoryResponse)
def update_medical_history(
    history_id: int,
    history_in: MedicalHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.update_entity(db, models.MedicalHistory, history_id, history_in.model_dump(exclude_unset=True), user_id=current_user.id)

@router.delete("/history/{history_id}")
def delete_medical_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.delete_entity(db, models.MedicalHistory, history_id, user_id=current_user.id)

# --- Allergies ---
@router.post("/{patient_id}/allergies", response_model=AllergyResponse)
def create_allergy(
    patient_id: int,
    allergy_in: AllergyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.create_allergy(db, patient_id, allergy_in, user_id=current_user.id)

@router.put("/allergies/{allergy_id}", response_model=AllergyResponse)
def update_allergy(
    allergy_id: int,
    allergy_in: AllergyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.update_entity(db, models.Allergy, allergy_id, allergy_in.model_dump(exclude_unset=True), user_id=current_user.id)

@router.delete("/allergies/{allergy_id}")
def delete_allergy(
    allergy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.delete_entity(db, models.Allergy, allergy_id, user_id=current_user.id)

# --- Medications ---
@router.get("/{patient_id}/medications", response_model=List[MedicationResponse])
def get_medications(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.get_medications(db, patient_id)

@router.post("/{patient_id}/medications", response_model=MedicationResponse)
def create_medication(
    patient_id: int,
    med_in: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.create_medication(db, patient_id, med_in, prescriber_id=current_user.id)

@router.put("/medications/{med_id}", response_model=MedicationResponse)
def update_medication(
    med_id: int,
    med_in: MedicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.update_entity(db, models.Medication, med_id, med_in.model_dump(exclude_unset=True), user_id=current_user.id)

@router.delete("/medications/{med_id}")
def delete_medication(
    med_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.delete_entity(db, models.Medication, med_id, user_id=current_user.id)

# --- Procedures ---
@router.get("/{patient_id}/procedures", response_model=List[ProcedureResponse])
def get_procedures(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.get_procedures(db, patient_id)

@router.post("/{patient_id}/procedures", response_model=ProcedureResponse)
def create_procedure(
    patient_id: int,
    proc_in: ProcedureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.create_procedure(db, patient_id, proc_in, performer_id=current_user.id)

@router.put("/procedures/{proc_id}", response_model=ProcedureResponse)
def update_procedure(
    proc_id: int,
    proc_in: ProcedureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.update_entity(db, models.Procedure, proc_id, proc_in.model_dump(exclude_unset=True), user_id=current_user.id)

@router.delete("/procedures/{proc_id}")
def delete_procedure(
    proc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.delete_entity(db, models.Procedure, proc_id, user_id=current_user.id)

# --- Documents ---
@router.get("/{patient_id}/documents", response_model=List[DocumentResponse])
def get_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.get_documents(db, patient_id)

@router.post("/{patient_id}/documents/upload", response_model=DocumentResponse)
async def upload_document(
    patient_id: int,
    file: UploadFile = File(...),
    title: str = Form(..., max_length=100),
    summary: Optional[str] = Form(None, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Security: Validate file size (e.g. 10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (Max 10MB)")

    # Security: Validate file extension
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.txt'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed")

    # Ensure uploads directory exists
    UPLOAD_DIR = "uploads"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    # Generate unique filename (prevents directory traversal & collisions)
    filename = f"{uuid.uuid4()}{file_ext}"
    # Use path join safely
    file_path = os.path.abspath(os.path.join(UPLOAD_DIR, filename))
    if not file_path.startswith(os.path.abspath(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Return relative URL
    file_url = f"/uploads/{filename}"
    
    doc_in = DocumentCreate(
        title=title,
        file_type=file.content_type,
        file_url=file_url,
        summary=summary
    )
    
    return ClinicalService.create_document(db, patient_id, doc_in, uploader_id=current_user.id)

@router.post("/{patient_id}/documents", response_model=DocumentResponse)
def create_document(
    patient_id: int,
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.create_document(db, patient_id, doc_in, uploader_id=current_user.id)

@router.put("/documents/{doc_id}", response_model=DocumentResponse)
def update_document(
    doc_id: int,
    doc_in: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.update_entity(db, models.Document, doc_id, doc_in.model_dump(exclude_unset=True), user_id=current_user.id)

@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.delete_entity(db, models.Document, doc_id, user_id=current_user.id)

# --- Tasks ---
@router.get("/{patient_id}/tasks", response_model=List[TaskResponse])
def get_tasks(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.get_tasks(db, patient_id)

@router.post("/{patient_id}/tasks", response_model=TaskResponse)
def create_task(
    patient_id: int,
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.create_task(db, task_in, patient_id, user_id=current_user.id) # API expects patient_id in URL, service handles it

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.update_entity(db, models.Task, task_id, task_in.model_dump(exclude_unset=True), user_id=current_user.id)

@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.delete_entity(db, models.Task, task_id, user_id=current_user.id)

# --- Billing ---
@router.get("/{patient_id}/billing", response_model=List[BillingItemResponse])
def get_billing_items(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.get_billing_items(db, patient_id)

@router.post("/{patient_id}/billing", response_model=BillingItemResponse)
def create_billing_item(
    patient_id: int,
    item_in: BillingItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.create_billing_item(db, patient_id, item_in, user_id=current_user.id)

@router.put("/billing/{item_id}", response_model=BillingItemResponse)
def update_billing_item(
    item_id: int,
    item_in: BillingItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.update_entity(db, models.BillingItem, item_id, item_in.model_dump(exclude_unset=True), user_id=current_user.id)

@router.delete("/billing/{item_id}")
def delete_billing_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ClinicalService.delete_entity(db, models.BillingItem, item_id, user_id=current_user.id)
