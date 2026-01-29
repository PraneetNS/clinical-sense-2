import sys
import os
from dotenv import load_dotenv
import asyncio

# Add backend to path
sys.path.append(os.getcwd())
load_dotenv()

from app.services.ai.ai_service import AIService

async def test_groq():
    svc = AIService()
    result = await svc.structure_clinical_note("Patient presents with a cough and fever since yesterday.")
    # Output only the subjective field to check if it's 'Service Unavailable'
    print(f"SUBJECTIVE_RESULT: {result.get('subjective')}")

if __name__ == "__main__":
    asyncio.run(test_groq())
