import json
import os
import sys
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from groq import Groq
from sarvamai import SarvamAI

load_dotenv()   # root ki .env se SARVAM_API_KEY aur GROQ_API_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
METADATA_FILE = os.path.join(LOG_DIR, "conversation_metadata.jsonl")

# Project ka logger (src/logger.py)
sys.path.insert(0, os.path.dirname(BASE_DIR))
from src.logger import get_logger
logger = get_logger(__name__)

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
SYSTEM_PROMPT = (
    "You are a friendly voice assistant. Reply in the same language the user "
    "spoke. Keep answers short (2 to 3 sentences) in plain spoken style: no "
    "bullet points, no markdown, no emojis."
)

if not os.getenv("SARVAM_API_KEY") or not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("SARVAM_API_KEY aur GROQ_API_KEY available in .env ")

sarvam_client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI(title="Voice Note Assistant")


# 3 AI steps
def speech_to_text(wav_bytes):
    """Awaaz (WAV) -> (text, language_code)"""
    response = sarvam_client.speech_to_text.transcribe(
        file=("audio.wav", wav_bytes, "audio/wav"),
        model="saaras:v4",
        mode="transcribe",
    )
    return response.transcript.strip(), response.language_code


def ask_llm(history, user_text):
    """Text -> LLM ka jawab (pichle 6 messages history me)"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history[-6:]
    messages.append({"role": "user", "content": user_text})
    response = groq_client.chat.completions.create(model=GROQ_MODEL, messages=messages, max_tokens=800)
    return response.choices[0].message.content.strip()


def text_to_speech(text, language_code):
    """Text -> awaaz (base64 WAV)"""
    language = language_code or "en-IN"
    response = sarvam_client.text_to_speech.convert(
        text=text[:1000], language_code=language, model="bulbul:v4-flash"
    )
    return response.audios[0]


# main pipeline
def process_voice(wav_bytes, history_json="[]"):
    if len(wav_bytes) < 1000:
        raise HTTPException(status_code=400, detail="The recording is too short. Please try again.")
    try:
        history = json.loads(history_json)
    except ValueError:
        history = []

    start_total = time.perf_counter()           # total latency yahin se shuru

    # Step 1: speech to text
    t = time.perf_counter()
    try:
        transcript, language = speech_to_text(wav_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Speech-to-text failed: {e}")
    stt_time = round(time.perf_counter() - t, 3)
    if not transcript:
        raise HTTPException(status_code=422, detail="Couldn't hear anything. Hold the mic closer and try again.")

    # Step 2: LLM
    t = time.perf_counter()
    try:
        reply = ask_llm(history, transcript)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM failed: {e}")
    llm_time = round(time.perf_counter() - t, 3)

    # Step 3: text to speech
    t = time.perf_counter()
    try:
        audio_b64 = text_to_speech(reply, language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Text-to-speech failed: {e}")
    tts_time = round(time.perf_counter() - t, 3)   # time.perf_counter => count every step time

    total_time = round(time.perf_counter() - start_total, 3)    # awaaz mili -> jawab ki awaaz ready

    # Metadata
    now = datetime.now().astimezone()
    metadata = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": now.isoformat(timespec="seconds"),
        "date": now.strftime("%d %b %Y"),
        "time": now.strftime("%I:%M:%S %p"),
        "user_input": transcript,
        "bot_response": reply,
        "language": language,
        "llm_model": GROQ_MODEL,
        "latency_seconds": {
            "speech_to_text": stt_time,
            "llm": llm_time,
            "text_to_speech": tts_time,
            "total": total_time,
        },
    }

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(METADATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(metadata, ensure_ascii=False) + "\n")

    logger.info(
        f"user: {transcript!r} | bot: {reply[:60]!r} | total latency: {total_time}s "
        f"(STT {stt_time}s, LLM {llm_time}s, TTS {tts_time}s)"
    )

    return {"transcript": transcript, "reply": reply, "language": language,
            "audio_base64": audio_b64, "metadata": metadata}


# routes
@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.post("/api/voice")
def voice(audio: UploadFile = File(...), history: str = Form("[]")):
    return process_voice(audio.file.read(), history)


@app.get("/api/metadata")
def get_metadata():
    if not os.path.isfile(METADATA_FILE):
        return {"count": 0, "entries": []}
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    return {"count": len(entries), "entries": entries}



##Voice assistant backend (FastAPI): metadata + latency tracking.

##Flow:  Browser (mic, WAV) -> /api/voice -> Sarvam STT -> Groq LLM -> Sarvam TTS -> browser

##Har baat ka metadata (user_input, bot_response, date/time, latency) ek line ki tarah
#voicenote/logs/conversation_metadata.jsonl me save hota hai.

##Run (project root se):  uvicorn app:app --reload --app-dir voicenote
##Browser:                http://127.0.0.1:8000
##Metadata dekhne ke liye: http://127.0.0.1:8000/api/metadata
