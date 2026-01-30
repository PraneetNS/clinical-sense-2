import sys
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.getcwd())

load_dotenv()

from app.core.config import settings
from app.services.ai.ai_service import AIService
import asyncio

async def test_groq():
    print(f"Testing Groq with Model: {settings.GROQ_MODEL}")
    print(f"API Key present: {bool(settings.GROQ_API_KEY)}")
    if settings.GROQ_API_KEY:
        print(f"API Key starts with: {settings.GROQ_API_KEY[:7]}...")
    
    svc = AIService()
    result = await svc.structure_clinical_note("Patient presents with a cough and fever since yesterday.")
    print("\n--- Result ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_groq())
