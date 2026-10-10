"""Website endpoints: /chatbot/... (login, chat, booking). Glue between crud, agent and vision."""
import os
import base64
import time
from collections import defaultdict, deque
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from src.exception import CustomException
from src.logger import get_logger
from chatbot.database import crud
from chatbot.security import hash_password, verify_password
from chatbot import agent, vision , mcp_agent

logger = get_logger(__name__)
router = APIRouter(prefix="/chatbot")
templates = Jinja2Templates(directory="templates")

class Signup(BaseModel): name: str; email: str; password: str
class Login(BaseModel): email: str; password: str
class Message(BaseModel): message: str = ""; history: list = []; image: Optional[str] = None; lang: str = "en"

MAX_IMAGE_BYTES = 3 * 1024 * 1024  # 3 MB
def check_image(data: str):
    """Photo ka type (magic bytes) aur size check. Galat ho to error."""
    b64 = data.split(",", 1)[1] if data.startswith("data:") else data
    try:
        raw = base64.b64decode(b64)
    except Exception:
        raise HTTPException(400, "Invalid image file.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Image too large. Max 3 MB allowed.")
    is_jpg = raw[:3] == b"\xff\xd8\xff"
    is_png = raw[:8] == b"\x89PNG\r\n\x1a\n"
    is_webp = raw[:4] == b"RIFF" and raw[8:12] == b"WEBP"
    if not (is_jpg or is_png or is_webp):
        raise HTTPException(400, "Only JPG, PNG or WebP images are allowed.")



def clean_history(items):
    """Keep only well-formed user/assistant turns sent by the browser."""
    return [{"role": h["role"], "content": str(h["content"])[:1500]} for h in items[-12:]
            if isinstance(h, dict) and h.get("role") in ("user", "assistant") and h.get("content")]


HITS = defaultdict(deque)      # user id -> times of the recent chat messages
LIMIT, WINDOW = 10, 60         # at most 10 chat messages per 60 seconds per user


def rate_limit(user_id):
    """Stop a user who sends too many chat messages (protects the LLM and our cost)."""
    now = time.time()
    q = HITS[user_id]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= LIMIT:
        raise HTTPException(429, "Too many messages. Please wait a minute and try again.")
    q.append(now)


def role_of(u):
    """super_admin if the logged-in user's email is in ADMIN_EMAILS (.env), else user."""
    allowed = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]
    user = crud.get_user(u["id"])
    return "super_admin" if user and user["email"].lower() in allowed else "user"


def save_log(u, status, res=None):
    """Dashboard ke liye ek row: kaun, kya status, kaunsa tool, kitne tokens."""
    tool = ",".join(t["tool"] for t in res["tools_used"]) or "none" if res else None
    tin, tout = (res["tokens"]["in"], res["tokens"]["out"]) if res else (0, 0)
    try:
        crud.log_request(u["id"], role_of(u), "POST", "/chatbot/message", status, tool, tin, tout, 0)
    except Exception as e:
        logger.warning(f"api_log not saved: {e}")


def wants_mcp(text):
    """MCP tools wale sawal yahan se MCP me jate hain. Baaki sab purane agent ke paas rehta hai."""
    t = text.lower()
    names_doctor = "dr." in t or "dr " in t or "doctor" in t
    asks_info = any(w in t for w in ("detail", "about", "info", "schedule", "timing", "batao", "bataiye"))
    asks_mine = any(w in t for w in ("my appointment", "meri appointment", "my booking"))
    asks_my_more = any(w in t for w in ("my prescription", "my medicine", "my bill", "my bills",
                                        "meri prescription", "meri medicine", "mera bill", "mere bill"))
    asks_patient = "patient" in t and "appointment" in t
    asks_admin = any(w in t for w in ("all patients", "list patients", "patients list", "registered patients"))
    asks_admin2 = any(w in t for w in ("all appointment", "pending bill", "unpaid bill", "pending bills"))
    return ((names_doctor and asks_info) or asks_mine or asks_my_more
            or asks_patient or asks_admin or asks_admin2)


class Book(BaseModel): slot_id: int
class Cancel(BaseModel): appointment_id: int
class Reschedule(BaseModel): appointment_id: int; slot_id: int

def current_user(request: Request):
    u = request.session.get("user")
    if not u:
        raise HTTPException(401, "Please log in first")
    return u

@router.get("", response_class=HTMLResponse)
async def page(request: Request):
    return templates.TemplateResponse(request, "chatbot.html")

@router.get("/me")
async def me(request: Request):
    u = request.session.get("user")
    return {"user": u, "appointments": crud.get_user_appointments(u["id"]) if u else []}

@router.post("/signup")
async def signup(body: Signup, request: Request):
    email, name = body.email.strip().lower(), body.name.strip()
    if len(body.password) < 6 or not name or "@" not in email:
        raise HTTPException(400, "Enter a name, a valid email and a password of 6+ characters")
    if crud.get_user_by_email(email):
        raise HTTPException(409, "This email is already registered. Please log in.")
    uid = crud.create_user(name, email, hash_password(body.password))
    request.session["user"] = {"id": uid, "name": name}
    return {"user": request.session["user"]}

@router.post("/login")
async def login(body: Login, request: Request):
    u = crud.get_user_by_email(body.email.strip().lower())
    if not u or not verify_password(body.password, u["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect")
    request.session["user"] = {"id": u["id"], "name": u["name"]}
    return {"user": request.session["user"], "role": role_of(u)}

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}

@router.get("/greet")
async def greet(request: Request, lang: str = "en"):
    u = current_user(request)
    summary = crud.get_summary(u["id"])
    if summary:   # returning patient: AI picks up where they left off
        reply, _ = agent.run_agent(u, summary, [], "hi", lang)
        return {"reply": reply}
    if lang == "hi":
        return {"reply": f"नमस्ते {u['name']}, मैं संजीवनी क्लिनिक का सहायक हूँ। अपने लक्षण बताइए, चोट की फोटो भेजिए या डॉक्टर के बारे में पूछिए।"}
    return {"reply": f"Hi {u['name']}, I'm the Sanjeevani Clinic assistant. Tell me your symptoms, send a photo of an injury, or ask for a doctor."}

@router.post("/message")
async def message(body: Message, request: Request):
    u = current_user(request)
    try:
        rate_limit(u["id"])
    except HTTPException as e:
        save_log(u, 429)
        raise 
    if body.image:
        check_image(body.image)
    text = body.message.strip()[:1500]
    try:
        if body.image:
            if len(body.image) > 4_000_000:
                raise HTTPException(413, "Photo is too large (max about 3 MB)")
            info = vision.analyze_image(body.image, text)
            if info is None:   # no photo-capable model available -> fall back to text, no crash
                return {"reply": "Sorry, I can't read photos right now. Please describe the problem in words "
                                 "(which body part, since when, pain or swelling) and I'll help you book the right doctor.",
                        "doctors": []}
            text = (f"[Photo analysis: {info.get('description')} | body part: {info.get('body_part')} | "
                    f"suggested specialty: {info['specialty']} | urgent: {info.get('urgent')}] {text}")
        if not text:
            raise HTTPException(400, "Please type a message")
        
        if not body.image and wants_mcp(text):
            try:
                res = await mcp_agent.ask_agent(text, u["id"], role_of(u))   # RBAC: the AI only sees this role's tools
                save_log(u, 200, res)
                return {"reply": res["answer"], "doctors": [], "tools_used": res["tools_used"]}
            except Exception as e:   # MCP server band ho to purana chat chalta rahe
                logger.warning(f"MCP failed, using normal chat: {e}")
        
        
        summary = crud.get_summary(u["id"])
        reply, doctors = agent.run_agent(u, summary, clean_history(body.history), text, "hi" if body.lang == "hi" else "en")
        try:
            crud.save_summary(u["id"], agent.summarize(summary, text, reply))
        except Exception as e:   # the reply is already good; a failed summary must not break the chat
            logger.warning(f"Summary not saved: {e}")
        save_log(u, 200)
        return {"reply": reply, "doctors": doctors}
    except CustomException as e:
        logger.error(str(e))
        raise HTTPException(500, "Something went wrong on our side. Please try again.")

@router.post("/book")
async def book(body: Book, request: Request):
    u = current_user(request)
    res = crud.book_slot(u["id"], body.slot_id)
    if not res:
        raise HTTPException(409, "That slot was just taken. Please pick another one.")
    summary = crud.get_summary(u["id"])
    crud.add_history(u["id"], res["doctor_id"], summary or "Appointment booked")   # feeds the returning-patient flow
    crud.save_summary(u["id"], (summary + f" Booked {res['doctor']} on {res['when']}.").strip()[-600:])
    return res


@router.get("/profile")
async def profile(request: Request):
    """Everything about the logged-in patient, used by the /profile page."""
    u = current_user(request)
    user = crud.get_user(u["id"])
    appts = crud.list_appointments(u["id"])
    return {
        "user": {"name": user["name"], "email": user["email"], "member_since": user["created_at"].strftime("%d %b %Y"), "role": role_of(u)},
        "appointments": appts,
        "screenings": crud.list_screenings(u["id"]),
        "history": crud.list_history(u["id"]),
        "summary": crud.get_summary(u["id"]),
        "prescriptions": crud.list_prescriptions(u["id"]),
        "bills": crud.list_bills(u["id"]),
        "records": crud.list_records(u["id"]),
        "doctor": crud.get_assigned_doctor(u["id"]),
    }

@router.post("/cancel")
async def cancel(body: Cancel, request: Request):
    u = current_user(request)
    if not crud.cancel_appointment(u["id"], body.appointment_id):
        raise HTTPException(409, "This appointment can no longer be cancelled.")
    return {"ok": True}


@router.get("/slots/{appointment_id}")
async def slots_for_reschedule(appointment_id: int, request: Request):
    u = current_user(request)
    return {"slots": crud.free_slots_for_appointment(u["id"], appointment_id)}

@router.post("/reschedule")
async def reschedule(body: Reschedule, request: Request):
    u = current_user(request)
    res = crud.reschedule_appointment(u["id"], body.appointment_id, body.slot_id)
    if not res:
        raise HTTPException(409, "That time was just taken. Please pick another one.")
    return res


class McpMessage(BaseModel):
    message: str



@router.post("/mcp-message")
async def mcp_message(body: McpMessage, request: Request):
    u = current_user(request)
    rate_limit(u["id"])
    res = await mcp_agent.ask_agent(body.message.strip()[:500], u["id"], role_of(u))
    save_log(u, 200, res)
    return res


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Sirf super admin: total hits, total tokens, response codes."""
    u = current_user(request)
    if role_of(u) != "super_admin":
        raise HTTPException(403, "Only super admin can see the dashboard.")
    s = crud.dashboard_stats()
    t = s["totals"]

    rows = ""
    for c in s["codes"]:
        code = c["status_code"]
        cls = "ok" if 200 <= code < 300 else "bad"
        rows += f'<tr><td><span class="pill {cls}">{code}</span></td><td>{c["n"]}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="2">No requests yet.</td></tr>'

    page = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard · Sanjeevani Clinic</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
body { margin: 0; background: #F6F3EC; color: #22302B; font-family: 'Inter', Arial, sans-serif; }
.bar { display: flex; align-items: center; justify-content: space-between; padding: 22px 48px; border-bottom: 1px solid #DAD4C6; }
.brand { display: flex; align-items: center; gap: 12px; font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.2rem; color: #143832; text-decoration: none; }
.mark { width: 36px; height: 36px; border-radius: 50%; background: #1F4B43; display: flex; align-items: center; justify-content: center; }
.links { display: flex; gap: 26px; }
.links a { color: #5B6B64; text-decoration: none; font-size: 0.95rem; font-weight: 500; }
.links a:hover { color: #143832; }
.wrap { max-width: 1000px; margin: 0 auto; padding: 44px 48px 64px; }
h1 { font-family: 'Fraunces', serif; color: #143832; font-size: 2.1rem; margin: 0 0 6px; }
.sub { color: #5B6B64; margin: 0 0 30px; }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 40px; }
.tile { background: #fff; border: 1px solid #DAD4C6; border-radius: 20px; padding: 22px 24px; }
.num { font-family: 'Fraunces', serif; font-size: 2.2rem; font-weight: 600; color: #1F4B43; }
.lbl { font-size: 0.85rem; color: #5B6B64; margin-top: 4px; }
h2 { font-family: 'Fraunces', serif; color: #143832; font-size: 1.3rem; margin: 0 0 12px; }
table { width: 100%; max-width: 420px; border-collapse: collapse; background: #fff; border: 1px solid #DAD4C6; border-radius: 12px; overflow: hidden; }
th { text-align: left; background: #EEF4EF; color: #143832; font-size: 0.85rem; }
th, td { padding: 12px 18px; border-bottom: 1px solid #DAD4C6; }
tr:last-child td { border-bottom: none; }
.pill { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; }
.pill.ok { background: #E3F0E6; color: #3C7a52; }
.pill.bad { background: #F4E3DA; color: #C6603F; }
.note { color: #5B6B64; font-size: 0.85rem; margin-top: 18px; }
@media (max-width: 800px) { .tiles { grid-template-columns: repeat(2, 1fr); } .bar, .wrap { padding-left: 22px; padding-right: 22px; } }
</style></head>
<body>
<div class="bar">
  <a class="brand" href="/">
    <span class="mark"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 21s-7.5-4.6-9.8-9.4C.6 7.9 2.4 4.5 6 4.1c2-.2 3.6.9 6 3 2.4-2.1 4-3.2 6-3 3.6.4 5.4 3.8 3.8 7.5C19.5 16.4 12 21 12 21z" fill="#F6F3EC"/></svg></span>
    Sanjeevani Clinic
  </a>
  <div class="links"><a href="/admin">Admin desk</a><a href="/chatbot">AI assistant</a></div>
</div>
<div class="wrap">
  <h1>Super admin dashboard</h1>
  <p class="sub">How the AI assistant is being used.</p>
  <div class="tiles">
    <div class="tile"><div class="num">__HITS__</div><div class="lbl">Total hits</div></div>
    <div class="tile"><div class="num">__TOKENS__</div><div class="lbl">Total tokens</div></div>
    <div class="tile"><div class="num">__TIN__</div><div class="lbl">Input tokens</div></div>
    <div class="tile"><div class="num">__TOUT__</div><div class="lbl">Output tokens</div></div>
  </div>
  <h2>Response codes</h2>
  <table><tr><th>Code</th><th>Count</th></tr>__ROWS__</table>
  <p class="note">Hits are chat requests. Tokens are counted for answers given through the MCP tools.</p>
</div>
</body></html>"""
    page = (page.replace("__HITS__", str(t["hits"])).replace("__TOKENS__", str(t["tokens"]))
                .replace("__TIN__", str(t["tin"])).replace("__TOUT__", str(t["tout"]))
                .replace("__ROWS__", rows))
    return HTMLResponse(page)