from app.db.session import SessionLocal
from app.models import User

def list_users():
    db = SessionLocal()
    users = db.query(User).all()
    for user in users:
        print(f"ID: {user.id}, Email: {user.email}")
    db.close()

if __name__ == "__main__":
    list_users()
