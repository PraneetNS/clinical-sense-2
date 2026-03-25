import os
import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings

# Initialize Firebase Admins if not already
if not firebase_admin._apps:
    cert_dict = {
        "type": "service_account",
        "project_id": settings.FIREBASE_PROJECT_ID,
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "private_key": settings.FIREBASE_PRIVATE_KEY,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    cred = credentials.Certificate(cert_dict)
    firebase_admin.initialize_app(cred)

try:
    user = auth.create_user(
        email='test_user_today@example.com',
        password='Password123!',
        display_name='Test User'
    )
    print("Created new user:", user.uid)
except Exception as e:
    print("Error creating user:", e)
    try:
        user = auth.get_user_by_email('test_user_today@example.com')
        print("User already exists:", user.uid)
    except:
        pass
