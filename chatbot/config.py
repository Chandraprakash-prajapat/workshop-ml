"""Settings shared by the whole chatbot package."""
import os
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "")      # empty = pick automatically from your Groq account
SPECIALTIES = ["General Physician", "Neurologist", "Orthopedic", "Gastroenterologist", "Dermatologist", "ENT"]
_client = None

def get_client():
    """One Groq client for the whole app (created on first use)."""
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client

def find_vision_models():
    """Models to try for photos: GROQ_VISION_MODEL if set, else any known vision-capable name on your account."""
    if VISION_MODEL:
        return [VISION_MODEL]
    ids = [m.id for m in get_client().models.list().data]
    found = []
    for word in ("scout", "maverick", "vision", "llama-4", "qwen"):    # qwen: newer Qwen models may accept images
        found += [i for i in ids if word in i.lower() and i not in found]
    return found
