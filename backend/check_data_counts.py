from app.db.session import SessionLocal
from app.models import User, Patient, ClinicalNote

def check_counts():
    db = SessionLocal()
    users = db.query(User).all()
    print(f"{'User Email':<30} | {'Patients':<10} | {'Notes':<10}")
    print("-" * 55)
    for user in users:
        p_count = db.query(Patient).filter(Patient.user_id == user.id).count()
        n_count = db.query(ClinicalNote).filter(ClinicalNote.user_id == user.id).count()
        print(f"{user.email:<30} | {p_count:<10} | {n_count:<10}")
    db.close()

if __name__ == "__main__":
    check_counts()
