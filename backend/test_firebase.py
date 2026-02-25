import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings
import sys

# Init
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

print("Firebase Initialized.")

try:
    # This should fail fast with invalid token error, 
    # but proving we can import and call function without crash.
    auth.verify_id_token("invalid.token.here")
except Exception as e:
    print(f"Verification Failed (Expected): {e}")
