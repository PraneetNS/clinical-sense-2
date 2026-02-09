from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, MetaData, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

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
    role = Column(String, default="doctor") # 'doctor', 'assistant', 'admin'
    
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

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    description = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=True, index=True)
    status = Column(String, default="Pending", index=True) # 'Pending', 'In Progress', 'Completed'
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    patient = relationship("Patient", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks_assigned")

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
