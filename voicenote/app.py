import json
import os
import sys
import time
import uuid
from datetime import datetime, date
from threading import Lock
import database

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
    "You are the voice assistant of a cafe that books tables for breakfast, lunch and dinner. Reply in the same language as the user's latest message. "
    "Keep the reply short: one sentence, preferably under 15 words. "
    "Ask only one question at a time. No bullets, markdown, or emojis."
)

if not os.getenv("SARVAM_API_KEY") or not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("SARVAM_API_KEY aur GROQ_API_KEY available in .env ")

sarvam_client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI(title="Voice Note Assistant")
database.init_db()
BOOKING_SESSIONS = {}
SESSION_LOCK = Lock()


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
    """Short reply in the user's language."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history[-6:]
    messages.append({"role": "user", "content": user_text})
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL, messages=messages, max_tokens=100, temperature=0.3
    )
    return response.choices[0].message.content.strip()


def text_to_speech(text, language_code):
    """Text -> awaaz (base64 WAV)"""
    language = language_code or "en-IN"
    response = sarvam_client.text_to_speech.convert(
        text=text[:1000], language_code=language, model="bulbul:v4-flash"
    )
    return response.audios[0]

BOOKING_PROMPT = """
You extract cafe booking details.
Return one valid JSON object only. No markdown or extra text.

Required keys:
{
  "intent": "booking",
  "members": null,
  "meal": null,
  "date": null,
  "name": null,
  "confirmed": false
}

Rules:
- intent: booking, other, or cancel
- members: positive integer or null
- meal: breakfast, lunch, dinner, or null
- date: YYYY-MM-DD or null
- name: string or null
- confirmed: true only if user confirms the proposed booking
- Keep existing details unless user clearly changes them.
- Never invent missing details.
- Resolve relative dates using the date supplied in the user message.
"""

def booking_turn(history, transcript, session_id, language_code=None):
    """Collect booking details over multiple voice turns; confirm before insert."""
    english = (language_code or "").lower().startswith("en")

    with SESSION_LOCK:
        state = BOOKING_SESSIONS.setdefault(session_id, {
            "active": False, "completed": False, "name": None,
            "date": None, "meal": None, "members": None, "proposed": None
        })
        if state.get("completed"):
            # A new utterance after a completed booking starts a fresh conversation.
            state = {"active": False, "completed": False, "name": None,
                     "date": None, "meal": None, "members": None, "proposed": None}
            BOOKING_SESSIONS[session_id] = state
        previous = dict(state)

    # Handle a clear rejection before asking the LLM to extract fields.
    # This prevents a spoken "No" from being treated as an ambiguous confirmation.
    negative_answers = {
        "no", "nope", "nah", "no thanks", "don't", "do not",
        "nahi", "nahin", "nhi", "mat karo", "cancel it",
    }
    normalized_transcript = " ".join(
        transcript.lower().strip().replace(".", "").replace("!", "").split()
    )
    if previous.get("proposed") and normalized_transcript in negative_answers:
        with SESSION_LOCK:
            state = dict(previous)
            state["proposed"] = None
            BOOKING_SESSIONS[session_id] = state
        logger.info("booking_confirmation_rejected | session=%s", session_id)
        if english:
            return "Okay, I won't book it. Change the details or cancel?", "rejected"
        return "Theek hai, booking nahi karunga. Details badlein ya cancel karein?", "rejected"

    prompt = (
        f"Today's date: {date.today().isoformat()}\n"
        f"Existing booking state: {json.dumps({k: previous.get(k) for k in ('active','name','date','meal','members','proposed')})}\n"
        f"Recent conversation: {json.dumps(history[-12:], ensure_ascii=False)}\n"
        f"Latest user message: {transcript}\n"
        "Extract the updated booking fields. Keep existing fields unless user changes them."
    )
    result = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": BOOKING_PROMPT}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}, temperature=0, max_tokens=300,
        reasoning_effort="low"
    )
    fields = json.loads(result.choices[0].message.content)
    intent = fields.get("intent")

    if intent == "cancel":
        with SESSION_LOCK:
            BOOKING_SESSIONS.pop(session_id, None)
        logger.info("booking_cancelled | session=%s", session_id)
        reply = "Okay, I've cancelled the booking request." if english else "Theek hai, booking request cancel kar di."
        return reply, "cancelled"

    if intent != "booking" and not previous.get("active"):
        return ask_llm(history, transcript), "chat"

    # Merge extracted values with stored values; null extraction won't erase prior answers.
    state = previous
    state["active"] = True
    for key in ("name", "date", "meal", "members"):
        value = fields.get(key)
        if value is not None and value != "":
            state[key] = value

    # Validate and normalize values before availability lookup.
    if state.get("meal") not in database.CAPACITY:
        state["meal"] = None
    try:
        parsed_date = date.fromisoformat(state["date"]) if state.get("date") else None
        if parsed_date and parsed_date < date.today():
            state["date"] = None
    except (TypeError, ValueError):
        state["date"] = None
    try:
        members = int(state["members"]) if state.get("members") is not None else None
        state["members"] = members if members is not None and not isinstance(state["members"], bool) and members > 0 else None
    except (TypeError, ValueError):
        state["members"] = None
    if state.get("name") is not None:
        state["name"] = str(state["name"]).strip() or None

    with SESSION_LOCK:
        BOOKING_SESSIONS[session_id] = state

    missing = []
    if not state.get("members"):
        missing.append("members")
    if not state.get("date"):
        missing.append("date")
    if not state.get("meal"):
        missing.append("meal")
    if not state.get("name"):
        missing.append("name")
    if missing:
        logger.info("booking_details_pending | session=%s missing=%s", session_id, missing)
        # Ask only for the first missing field; this keeps the spoken reply short.
        question = missing[0]
        prompts = {
            "members": "How many people?" if english else "Kitne logon ke liye booking chahiye?",
            "date": "For which date?" if english else "Kis date ke liye?",
            "meal": "Breakfast, lunch, or dinner?" if english else "Breakfast, lunch ya dinner?",
            "name": "What name should I use?" if english else "Booking kis naam se karun?",
        }
        return prompts[question], "collecting"

    if state["members"] > database.CAPACITY[state["meal"]]:
        logger.info("booking_too_large | session=%s members=%s meal=%s", session_id, state["members"], state["meal"])
        if english:
            reply = f"Maximum {database.CAPACITY[state['meal']]} seats. How many people?"
        else:
            reply = f"Maximum {database.CAPACITY[state['meal']]} seats hain. Kitne log hain?"
        return reply, "collecting"

    details = (state["date"], state["meal"], state["members"], state["name"])
    awaiting = previous.get("proposed") == details
    user_confirmed = bool(fields.get("confirmed"))

    if not awaiting:
        check = database.check_availability(state["date"], state["meal"], state["members"])
        if not check["available"]:
            logger.info("booking_unavailable | session=%s date=%s meal=%s seats_left=%s", session_id, state["date"], state["meal"], check["seats_left"])
            left = check["seats_left"]
            if english:
                reply = "Sorry, that meal is fully booked. Try another date?" if left == 0 else f"Sorry, only {left} seats are left. Try another date?"
            else:
                reply = "Maaf kijiye, is meal me jagah nahi hai. Doosri date try karein?" if left == 0 else f"Maaf kijiye, sirf {left} seats bachi hain. Doosri date try karein?"
            return reply, "unavailable"
        state["proposed"] = details
        with SESSION_LOCK:
            BOOKING_SESSIONS[session_id] = state
        logger.info("booking_awaiting_confirmation | session=%s date=%s meal=%s members=%s", session_id, *details[:3])
        if english:
            reply = f"Book {state['members']} for {state['meal']} on {state['date']} under {state['name']}? Say yes to confirm."
        else:
            reply = f"{state['date']} ko {state['members']} logon ki {state['meal']} booking, naam {state['name']}? Haan bolkar confirm karein."
        return reply, "awaiting_confirmation"

    if not user_confirmed:
        # A changed detail invalidates the old proposal and requires a fresh confirmation.
        if previous.get("proposed") != details:
            state["proposed"] = details
            with SESSION_LOCK:
                BOOKING_SESSIONS[session_id] = state
            if english:
                reply = f"Updated booking: {state['members']} for {state['meal']} on {state['date']}. Confirm?"
            else:
                reply = f"Booking update ho gayi. {state['date']}, {state['members']} log, {state['meal']}. Confirm karein?"
            return reply, "awaiting_confirmation"
        reply = "The booking isn't confirmed yet. Should I confirm it?" if english else "Booking confirm nahi hui. Confirm kar doon?"
        return reply, "awaiting_confirmation"

    # create_booking capacity dobara check karke hi insert karta hai.
    booking = database.create_booking(state["date"], state["meal"], state["members"], state["name"])
    if booking.get("status") == "confirmed":
        with SESSION_LOCK:
            state["active"] = False
            state["completed"] = True
            BOOKING_SESSIONS[session_id] = state
        logger.info("voice_booking_confirmed | session=%s booking_id=%s", session_id, booking["booking_id"])
        if english:
            reply = f"Thank you {state['name']}! Booking confirmed, ID {booking['booking_id']}. See you at the cafe!"
        else:
            reply = f"Shukriya {state['name']}! Booking confirm ho gayi, ID {booking['booking_id']}. Cafe me milte hain!"
        return reply, "confirmed"
    logger.info("voice_booking_unavailable_at_insert | session=%s", session_id)
    state["proposed"] = None
    with SESSION_LOCK:
        BOOKING_SESSIONS[session_id] = state
    reply = "Sorry, those seats are no longer available. Try another date?" if english else "Maaf kijiye, seats ab available nahi hain. Doosri date try karein?"
    return reply, "unavailable"


# main pipeline
def process_voice(wav_bytes, history_json="[]", session_id="default"):
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
        reply, booking_status = booking_turn(history, transcript, session_id, language)
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
        "booking_status": booking_status,
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
def voice(audio: UploadFile = File(...), history: str = Form("[]"), session_id: str = Form("default")):
    return process_voice(audio.file.read(), history, session_id)


@app.post("/api/session/reset")
def reset_session(session_id: str = Form(...)):
    with SESSION_LOCK:
        BOOKING_SESSIONS.pop(session_id, None)
    logger.info("booking_session_reset | session=%s", session_id)
    return {"status": "reset"}


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