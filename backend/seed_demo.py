import datetime
from app.db.session import SessionLocal
from app.models import User, Patient, ClinicalNote

def seed_data_for_user(email):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"User {email} not found. Creating...")
        user = User(email=email, is_active=True, full_name="Demo Clinician")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check if patients already exist
    if db.query(Patient).filter(Patient.user_id == user.id).count() > 0:
        print(f"User {email} already has patients. Skipping seed.")
        db.close()
        return

    print(f"Seeding dummy patients for {email}...")
    patients = [
        Patient(
            user_id=user.id,
            mrn="MRN-001",
            name="Alice Thompson",
            date_of_birth=datetime.datetime(1985, 5, 12),
            gender="Female",
            status="Active"
        ),
        Patient(
            user_id=user.id,
            mrn="MRN-002",
            name="Robert Miller",
            date_of_birth=datetime.datetime(1972, 11, 24),
            gender="Male",
            status="Active"
        ),
        Patient(
            user_id=user.id,
            mrn="MRN-003",
            name="Elena Rodriguez",
            date_of_birth=datetime.datetime(1998, 2, 3),
            gender="Female",
            status="Active"
        )
    ]
    db.add_all(patients)
    db.commit()

    # Add a note for Alice
    alice = db.query(Patient).filter(Patient.mrn == "MRN-001").first()
    note = ClinicalNote(
        user_id=user.id,
        patient_id=alice.id,
        title="Initial Consultation",
        raw_content="Patient presents with recurring migraines. Reported sensitivity to light and sound. Duration 4-6 hours per episode. No aura reported.",
        structured_content='{"subjective": "Recurring migraines with light/sound sensitivity", "objective": "BP 120/80", "assessment": "Migraine without aura", "plan": "Keep headache diary"}',
        note_type="SOAP",
        status="finalized",
        encounter_date=datetime.datetime.utcnow()
    )
    db.add(note)
    db.commit()
    print("Seeding complete!")
    db.close()

if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else "demo_test@hospital.org"
    seed_data_for_user(email)
