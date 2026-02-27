
import os
import sys
import asyncio
from sqlalchemy.orm import Session
from backend.app.db.session import SessionLocal
from backend.app.services.patient_service import PatientService
from backend.app.models import Patient

async def test_report():
    db = SessionLocal()
    try:
        # Get first patient
        patient = db.query(Patient).first()
        if not patient:
            print("No patients found in DB")
            return
        
        print(f"Testing report for patient ID: {patient.id}")
        report = await PatientService.get_patient_report(db, patient.id, user_id=None) 
        print("Report data fetched successfully")
        
        # Test serialization (mock FastAPI response model behavior)
        from backend.app.schemas.patient import PatientReport
        p_report = PatientReport.model_validate(report)
        print("Report serialized to Pydantic successfully")
        
        # Test PDF gen
        from backend.app.core.pdf_gen import generate_patient_pdf
        pdf = generate_patient_pdf(report)
        print("PDF generated successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Add backend to path
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    
    # Redirect stdout to a file
    with open('debug_log.txt', 'w') as f:
        sys.stdout = f
        sys.stderr = f
        asyncio.run(test_report())
