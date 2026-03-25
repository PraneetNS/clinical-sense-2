from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, MetaData, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import uuid

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    firebase_uid = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    role = Column(String, default="DOCTOR", index=True)  # DOCTOR | NURSE | BILLING_ADMIN | READ_ONLY_AUDITOR | SUPER_ADMIN
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    patients = relationship("Patient", back_populates="creator")
    notes = relationship("ClinicalNote", back_populates="owner")
    tasks_assigned = relationship("Task", back_populates="assignee")
    procedures_performed = relationship("Procedure", back_populates="performer")
    documents_uploaded = relationship("Document", back_populates="uploader")
    audit_logs = relationship("AuditLog", back_populates="user")
    ai_metrics = relationship("DoctorAIMetrics", back_populates="user", uselist=False)

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    mrn = Column(String, index=True) # Medical Record Number
    name = Column(String, index=True) # Encrypted in production
    date_of_birth = Column(DateTime)
    gender = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    # Insurance
    insurance_provider = Column(String, nullable=True)
    policy_number = Column(String, nullable=True)
    
    # Emergency Contact
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_relation = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    
    # System fields
    status = Column(String, default="Active", index=True) # 'Active', 'Closed'
    
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('user_id', 'mrn', name='uq_patient_user_mrn'),)
    
    # Relationships
    creator = relationship("User", back_populates="patients")
    notes = relationship("ClinicalNote", back_populates="patient")
    admissions = relationship("Admission", back_populates="patient")
    medical_history = relationship("MedicalHistory", back_populates="patient")
    allergies = relationship("Allergy", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    procedures = relationship("Procedure", back_populates="patient")
    documents = relationship("Document", back_populates="patient")
    tasks = relationship("Task", back_populates="patient")
    billing_items = relationship("BillingItem", back_populates="patient")
    risk_profile = relationship("HospitalPatientRisk", back_populates="patient", uselist=False)

class Admission(Base):
    __tablename__ = "admissions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    admission_date = Column(DateTime, default=datetime.datetime.utcnow)
    discharge_date = Column(DateTime, nullable=True)
    reason = Column(Text)
    ward = Column(String, nullable=True)
    room = Column(String, nullable=True)
    status = Column(String, default="Active") # 'Active', 'Discharged'
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="admissions")
    clinical_notes = relationship("ClinicalNote", back_populates="admission")

class ClinicalNote(Base):
    __tablename__ = "clinical_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=True)
    
    title = Column(String, index=True)
    raw_content = Column(Text, nullable=False)
    structured_content = Column(Text)  # JSON or Structured SOAP
    
    note_type = Column(String, default="SOAP", index=True) # 'SOAP', 'PROGRESS', 'DISCHARGE'
    status = Column(String, default="draft") # 'draft', 'finalized'
    
    encounter_date = Column(DateTime, nullable=True, index=True)
    
    patient_summary = Column(Text, nullable=True) # Patient-friendly summary
    embedding = Column(Text, nullable=True) # JSON string for vector search
    
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    idempotency_key = Column(String, unique=True, index=True, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    owner = relationship("User", back_populates="notes")
    patient = relationship("Patient", back_populates="notes")
    admission = relationship("Admission", back_populates="clinical_notes")
    audit_logs = relationship("AuditLog", back_populates="note")
    versions = relationship("NoteVersion", back_populates="note")
    ai_insights = relationship("ClinicalAIInsight", back_populates="note", uselist=False)

class NoteVersion(Base):
    __tablename__ = "note_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("clinical_notes.id"), index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    structured_content = Column(Text)
    raw_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    note = relationship("ClinicalNote", back_populates="versions")

class MedicalHistory(Base):
    __tablename__ = "medical_history"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    condition_name = Column(String, nullable=False)
    diagnosis_date = Column(DateTime, nullable=True)
    status = Column(String, default="Active") # 'Active', 'Resolved', 'History'
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="medical_history")

class Allergy(Base):
    __tablename__ = "allergies"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    allergen = Column(String, nullable=False)
    reaction = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="allergies")

class Medication(Base):
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescribed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    source_note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True)
    
    name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, default="Active") # 'Active', 'Discontinued'
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="medications")

class Procedure(Base):
    __tablename__ = "procedures"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    performer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=True)
    source_note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True)
    
    name = Column(String, nullable=False)
    code = Column(String, nullable=True) # CPT/ICD
    date = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="procedures")
    performer = relationship("User", back_populates="procedures_performed")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    title = Column(String, nullable=False)
    file_type = Column(String) # PDF, Image, etc
    file_url = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="documents")
    uploader = relationship("User", back_populates="documents_uploaded")



class ClinicalTrajectory(Base):
    __tablename__ = "clinical_trajectories"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True, index=True)
    
    trend = Column(String) # Improving, Stable, Deteriorating, Uncertain
    risk_score = Column(Integer) # 0-100
    confidence_score = Column(Float) # 0.0-1.0
    key_changes = Column(Text) # JSON list of changes
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient")
    note = relationship("ClinicalNote")

class DischargeReadiness(Base):
    __tablename__ = "discharge_readiness"
    
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=True, index=True) # Optional if outpatient tracking
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    readiness_score = Column(Integer) # 0-100
    missing_requirements = Column(Text) # JSON list
    suggested_date = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient")
    admission = relationship("Admission")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    source_note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True)
    
    description = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=True, index=True)
    status = Column(String, default="Pending", index=True) # 'Pending', 'In Progress', 'Completed'
    
    priority = Column(String, default="Medium") # High, Medium, Low
    category = Column(String, default="General") # Lab, Medication, Referral, Imaging, Follow-up
    is_auto_generated = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks_assigned")
    source_note = relationship("ClinicalNote")

class BillingItem(Base):
    __tablename__ = "billing_items"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    item_name = Column(String, nullable=False)
    code = Column(String, nullable=True, index=True)
    cost = Column(Float, default=0.0)
    status = Column(String, default="Pending", index=True) # 'Pending', 'Billed', 'Paid'
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="billing_items")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True, index=True)
    
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True) # 'Patient', 'Medication', etc.
    entity_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="audit_logs")
    note = relationship("ClinicalNote", back_populates="audit_logs")

class ClinicalAIInsight(Base):
    __tablename__ = "clinical_ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=False, index=True)
    
    risk_score = Column(String, nullable=True) # High/Medium/Low
    red_flags = Column(Text, nullable=True) # JSON list
    suggestions = Column(Text, nullable=True) # JSON list
    missing_info = Column(Text, nullable=True) # JSON list
    news2_score = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    note = relationship("ClinicalNote", back_populates="ai_insights")

class DifferentialDiagnosis(Base):
    __tablename__ = "differential_diagnoses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    input_data = Column(Text, nullable=False) # JSON of symptoms, vitals, etc.
    output_data = Column(Text, nullable=False) # JSON of differentials
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# --- AI Hospital Operating System Models ---

class HospitalPatientRisk(Base):
    __tablename__ = "hospital_patient_risk"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, unique=True, index=True)
    
    risk_score = Column(Integer, default=0) # 0-100
    risk_level = Column(String, default="Low") # Low, Medium, High, Critical
    suggested_actions = Column(Text, nullable=True) # JSON list of actions
    
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="risk_profile")

class DoctorAIMetrics(Base):
    __tablename__ = "doctor_ai_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    workload_score = Column(Float, default=0.0) # 0-100 index
    burnout_probability = Column(Float, default=0.0) # 0-1.0
    active_patients_count = Column(Integer, default=0)
    notes_last_7d = Column(Integer, default=0)
    
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="ai_metrics")


# --- New AI Communication & Safety Models ---

class PatientCommunication(Base):
    __tablename__ = "patient_communications"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True)
    
    simplified_diagnosis = Column(Text)
    treatment_plan = Column(Text) # JSON list
    medication_explanation = Column(Text) # JSON list
    warning_signs = Column(Text) # JSON list
    next_steps = Column(Text, nullable=True)
    language = Column(String, default="en")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", backref="communications")
    note = relationship("ClinicalNote")

class SecureMessage(Base):
    __tablename__ = "secure_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Doctor handling the thread or target
    
    direction = Column(String) # 'Inbound' (from Patient), 'Outbound' (from Doctor)
    content = Column(Text, nullable=False)
    
    urgency_score = Column(Integer, default=0) # 0-10
    category = Column(String, default="Routine") # Routine, Urgent, Emergency
    flagged_keywords = Column(Text, nullable=True) # JSON list
    
    draft_response = Column(Text, nullable=True) # AI Draft
    status = Column(String, default="Unread") # Unread, Replied, Archived
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", backref="messages")
    user = relationship("User")

class ShiftHandover(Base):
    __tablename__ = "shift_handovers"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    generated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    shift_type = Column(String) # "Day", "Night"
    content = Column(Text) # JSON summary
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", backref="handovers")
    generator = relationship("User")

class ReadmissionRisk(Base):
    __tablename__ = "readmission_risks"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    risk_score = Column(Integer) # 0-100
    risk_level = Column(String) # Low, Medium, High
    contributing_factors = Column(Text) # JSON
    prevention_recommendations = Column(Text) # JSON
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", backref="readmission_risks")

class MedicationAlert(Base):
    __tablename__ = "medication_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    
    alert_type = Column(String) # Interaction, Allergy, Contraindication
    severity = Column(String) # High, Medium, Low
    description = Column(Text)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    patient = relationship("Patient", backref="medication_alerts")
    medication = relationship("Medication")


# =========================================================
# CLINICAL INTELLIGENCE PLATFORM — AI ENCOUNTER MODELS
# =========================================================

class AIEncounter(Base):
    """Root record for a single AI-orchestrated clinical encounter."""
    __tablename__ = "ai_encounters"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    encounter_date = Column(DateTime, nullable=False)
    raw_note = Column(Text, nullable=False)

    # SOAP output (JSON string)
    soap_note = Column(Text, nullable=True)

    # Summary outputs
    chief_complaint = Column(String, nullable=True)
    case_status = Column(String, default="active")           # active / needs_review / closed
    billing_complexity = Column(String, nullable=True)       # low / medium / high
    admission_required = Column(Boolean, default=False)
    icu_required = Column(Boolean, default=False)
    follow_up_days = Column(Integer, nullable=True)

    # Risk
    risk_score = Column(String, nullable=True)               # High / Medium / Low
    risk_flags = Column(Text, nullable=True)                 # JSON list

    # Medico-legal
    legal_flags = Column(Text, nullable=True)                # JSON list

    # Pipeline statuses (JSON list of {pipeline_name, status, error, latency_ms})
    pipeline_statuses = Column(Text, nullable=True)

    # Status flags
    status = Column(String, default="pending")               # pending / ready / confirmed / rejected
    is_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Token usage telemetry (JSON)
    token_usage = Column(Text, nullable=True)

    # Observability — added safely as nullable
    model_version = Column(String(100), nullable=True)
    processing_latency_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", backref="ai_encounters")
    note = relationship("ClinicalNote")
    creator = relationship("User", foreign_keys=[created_by_id])
    confirmer = relationship("User", foreign_keys=[confirmed_by_id])
    medications = relationship("AIGeneratedMedication", back_populates="encounter", cascade="all, delete-orphan")
    diagnoses = relationship("AIGeneratedDiagnosis", back_populates="encounter", cascade="all, delete-orphan")
    procedures = relationship("AIGeneratedProcedure", back_populates="encounter", cascade="all, delete-orphan")
    billing_items = relationship("AIGeneratedBilling", back_populates="encounter", cascade="all, delete-orphan")
    timeline_events = relationship("AITimelineEvent", back_populates="encounter", cascade="all, delete-orphan")
    followups = relationship("AIFollowupRecommendation", back_populates="encounter", cascade="all, delete-orphan")
    quality_report = relationship("AIQualityReport", uselist=False, back_populates="encounter", cascade="all, delete-orphan")
    usage_metrics = relationship("AIUsageMetrics", uselist=False, back_populates="encounter", cascade="all, delete-orphan")


class AIGeneratedMedication(Base):
    """AI-extracted medication from a clinical note — pending doctor confirmation."""
    __tablename__ = "ai_generated_medications"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    route = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    start_date_text = Column(String, nullable=True)       # Raw text, e.g. "start immediately"

    # If structured date is missing, doctor must confirm
    requires_confirmation = Column(Boolean, default=False)
    fields_required = Column(Text, nullable=True)         # JSON list of missing fields

    # Doctor confirmation
    is_confirmed = Column(Boolean, default=False)
    confirmed_medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)

    ai_generated = Column(Boolean, default=True)
    confidence = Column(String, nullable=True)            # high / medium / low

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounter = relationship("AIEncounter", back_populates="medications")
    patient = relationship("Patient")
    confirmed_medication = relationship("Medication")


class AIGeneratedProcedure(Base):
# ... (same as before, it was correct)
    """AI-extracted procedure from a clinical note — pending doctor confirmation."""
    __tablename__ = "ai_generated_procedures"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    code = Column(String, nullable=True) # CPT/ICD
    notes = Column(Text, nullable=True)

    # Doctor confirmation
    is_confirmed = Column(Boolean, default=False)
    confirmed_procedure_id = Column(Integer, ForeignKey("procedures.id"), nullable=True)

    ai_generated = Column(Boolean, default=True)
    confidence = Column(String, nullable=True)            # high / medium / low

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounter = relationship("AIEncounter", back_populates="procedures")
    patient = relationship("Patient")
    confirmed_procedure = relationship("Procedure")


class AIGeneratedDiagnosis(Base):
    """AI-inferred ICD-10 diagnosis from a clinical note."""
    __tablename__ = "ai_generated_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    condition_name = Column(String, nullable=False)
    icd10_code = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)       # 0.0 - 1.0
    reasoning = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False)

    # Doctor confirmation
    is_confirmed = Column(Boolean, default=False)

    ai_generated = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounter = relationship("AIEncounter", back_populates="diagnoses")
    patient = relationship("Patient")


class AIGeneratedBilling(Base):
    """AI-inferred billing draft from encounter data."""
    __tablename__ = "ai_generated_billing"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    cpt_code = Column(String, nullable=True)
    description = Column(String, nullable=False)
    estimated_cost = Column(Float, nullable=True)
    complexity = Column(String, nullable=True)            # low / medium / high
    confidence = Column(Float, nullable=True)             # 0.0 - 1.0
    requires_review = Column(Boolean, default=True)
    review_reason = Column(String, nullable=True)

    # Doctor confirmation
    is_confirmed = Column(Boolean, default=False)
    confirmed_billing_id = Column(Integer, ForeignKey("billing_items.id"), nullable=True)

    ai_generated = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounter = relationship("AIEncounter", back_populates="billing_items")
    patient = relationship("Patient")
    confirmed_billing = relationship("BillingItem")


class AITimelineEvent(Base):
    """AI-extracted timeline event from a clinical note."""
    __tablename__ = "ai_timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    event_type = Column(String, nullable=False)           # symptom_onset, lab_result, medication_change, etc.
    event_description = Column(Text, nullable=False)
    event_date_text = Column(String, nullable=True)       # Relative or absolute text
    event_date = Column(DateTime, nullable=True)          # Parsed datetime if possible
    severity = Column(String, nullable=True)              # high / medium / low / info

    ai_generated = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounter = relationship("AIEncounter", back_populates="timeline_events")
    patient = relationship("Patient")


class AIFollowupRecommendation(Base):
    """AI-suggested follow-up actions from an encounter."""
    __tablename__ = "ai_followup_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    recommendation = Column(Text, nullable=False)
    follow_up_type = Column(String, nullable=True)        # lab, referral, imaging, appointment, medication
    urgency = Column(String, default="routine")           # stat / urgent / routine
    suggested_days = Column(Integer, nullable=True)

    # Doctor confirmation
    is_confirmed = Column(Boolean, default=False)
    converted_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    ai_generated = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    encounter = relationship("AIEncounter", back_populates="followups")
    patient = relationship("Patient")
    converted_task = relationship("Task")


# =========================================================
# AI GOVERNANCE & OBSERVABILITY MODELS
# =========================================================

class AIQualityReport(Base):
    """Governance quality evaluation for an AI encounter."""
    __tablename__ = "ai_quality_reports"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id", ondelete="CASCADE"), nullable=False, index=True)

    # Scores (0.0 – 1.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    compliance_score = Column(Float, nullable=False, default=0.0)
    billing_accuracy_score = Column(Float, nullable=True)

    # JSONB fields for rich flag storage
    hallucination_flags = Column(JSONB, nullable=True)
    missing_critical_fields = Column(JSONB, nullable=True)
    clinical_safety_flags = Column(JSONB, nullable=True)   # output of clinical_rules engine

    risk_level = Column(String(20), nullable=False, default="HIGH")
    model_version = Column(String(100), nullable=True)

    # Clinical Sense v2: Deterministic + Explainable Extensions (JSONB)
    rationale_json = Column(JSONB, nullable=True)
    drug_safety_flags = Column(JSONB, nullable=True)
    structured_risk_metrics = Column(JSONB, nullable=True)
    guideline_flags = Column(JSONB, nullable=True)
    differential_output = Column(JSONB, nullable=True)
    lab_interpretation = Column(JSONB, nullable=True)
    handoff_sbar = Column(JSONB, nullable=True)
    
    # Feature Toggles
    evidence_mode_enabled = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        CheckConstraint("risk_level IN ('LOW','MEDIUM','HIGH')", name="ck_quality_risk_level"),
    )

    encounter = relationship("AIEncounter", back_populates="quality_report")


class AIUsageMetrics(Base):
    """Per-encounter AI usage metrics for observability and admin analytics."""
    __tablename__ = "ai_usage_metrics"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    accepted_without_edit = Column(Boolean, default=False)
    edit_distance_score = Column(Float, nullable=True)   # 0.0 = no edits, 1.0 = fully rewritten

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('ix_ai_usage_metrics_user_created', 'user_id', 'created_at'),
    )

    encounter = relationship("AIEncounter", back_populates="usage_metrics")
    user = relationship("User")


class Prescription(Base):
    """Printable digital prescriptions for patients."""
    __tablename__ = "prescriptions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id"), nullable=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    diagnosis = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # JSONB structure: [{medicine_name, dosage, frequency, duration, time_of_day: [], special_instruction}]
    prescription_items = Column(JSONB, nullable=False, default=list)
    
    verification_code = Column(PG_UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", backref="prescriptions")
    encounter = relationship("AIEncounter", backref="prescriptions")
    doctor = relationship("User", backref="prescriptions_issued")

class PatientPortalLink(Base):
    __tablename__ = "patient_portal_links"
    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("ai_encounters.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    accessed_at = Column(DateTime, nullable=True)
    
    encounter = relationship("AIEncounter", foreign_keys=[encounter_id])
    patient = relationship("Patient", foreign_keys=[patient_id])

class DeteriorationAlert(Base):
    __tablename__ = "deterioration_alerts"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    note_id = Column(Integer, ForeignKey("clinical_notes.id"), nullable=False)
    score = Column(Integer, nullable=False)
    delta = Column(Integer, nullable=False)
    triggered_at = Column(DateTime, default=datetime.datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    
    patient = relationship("Patient", foreign_keys=[patient_id])
    note = relationship("ClinicalNote", foreign_keys=[note_id])

