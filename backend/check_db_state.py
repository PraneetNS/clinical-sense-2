from app.db.session import SessionLocal
from app.models import User, Patient, ClinicalNote
db = SessionLocal()
try:
    user_count = db.query(User).count()
    patient_count = db.query(Patient).count()
    note_count = db.query(ClinicalNote).count()
    print(f"Users: {user_count}")
    print(f"Patients: {patient_count}")
    print(f"Notes: {note_count}")
    
    if user_count > 0:
        first_user = db.query(User).first()
        print(f"First User: ID={first_user.id}, Email={first_user.email}, Role={first_user.role}")
    
    if patient_count > 0:
        first_patient = db.query(Patient).first()
        print(f"First Patient: ID={first_patient.id}, Name={first_patient.name}, UserID={first_patient.user_id}")
finally:
    db.close()
