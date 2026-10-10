"""The AI agent: Groq decides which tool to call, we run it, Groq writes the final reply."""
import json, sys
from chatbot.config import MODEL, get_client
from chatbot import tools
from src.exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)

def detect_script(text):
    dev = sum("\u0900" <= c <= "\u097F" for c in text)
    lat = sum(c.isascii() and c.isalpha() for c in text)
    return "Devanagari (Hindi)" if dev > lat else "Latin/Roman (English or Hinglish)"

def build_system(name, summary, script):
    if script.startswith("Devanagari"):
        lang = "Write in Hindi using Devanagari letters."
    else:
        lang = ("Write in Roman letters only (English or Hinglish like 'Aapki age kitni hai?'). "
                "Do NOT use Devanagari letters.")
    return f"""You are the virtual front-desk assistant of Sanjeevani Clinic. Be warm, brief, professional.
LANGUAGE: reply in the same language and script as the patient's latest message. {lang} Never switch script.
RULES:
- You are NOT a doctor: no diagnosis, no medicines. Give only general safe tips and say a doctor should confirm.
- Never say which doctor is "best". The app shows available doctors as cards with slot buttons; just mention you found options and ask which they prefer. Do not list slots yourself.
- Use a tool when the patient wants a doctor/appointment or symptoms clearly need a specialist.
- If the patient's message starts with [Photo analysis: ...], immediately call find_available_doctors with the suggested specialty. Then write 2 short lines: what the photo seems to show (not a diagnosis) and that a doctor should look at it. No creams, no medicines.
- Severe symptoms (chest pain, breathing trouble, heavy bleeding, fainting) -> tell them to go to the emergency room now.
- Max two questions per reply.
- COVID screening: if the patient has fever/cough/cold-type symptoms, collect age, gender, fever (in Fahrenheit), cough (Mild or Strong) and city. Ask only for what is missing, then call covid_screening.
- If the patient writes the city in Devanagari, pass the city exactly as the patient wrote it.
- NEVER call covid_screening until the patient has told you ALL five values in this chat. Never guess, invent, or use placeholders like <city>. If anything is missing, just ask.
- Explain the screening result as a rough estimate from a small demo model, NEVER as a diagnosis or certainty. Then, in the same turn, call find_available_doctors with General Physician (do not ask which specialty). After the tool result, write ONE short line only; never write doctor names or slot times in text, the cards show them.
Patient name: {name}
Summary of earlier visits: {summary or 'none (new patient)'}
If a summary exists and the patient just greets, welcome them by name and ask a short follow-up about their earlier issue."""

def run_agent(user, summary, history, message, lang="en"):
    """Returns (reply_text, doctors_for_cards)."""
    try:
        client = get_client()
        script = "Devanagari (Hindi)" if lang == "hi" else detect_script(message)   # language switch on the site
        msgs = [{"role": "system", "content": build_system(user["name"], summary, script)}]
        msgs += history[-6:] + [{"role": "user", "content": message}]
        msgs.append({"role": "system", "content": "Reminder: " + build_system(user["name"], summary, script).split("RULES:")[0].split("LANGUAGE:")[1].strip()})
        user_text = " ".join(h["content"] for h in history[-6:] if h["role"] == "user" and h.get("content")) + " " + message
        doctors = []
        for _ in range(3):                                     # max 3 tool rounds
            try:
                m = client.chat.completions.create(model=MODEL, messages=msgs, tools=tools.SCHEMAS,
                                                   tool_choice="auto", temperature=0.3).choices[0].message
            except Exception as e:
                if "tool_use_failed" not in str(e):
                    raise
                # the AI built an invalid tool call -> ask it to reply in plain text instead
                logger.warning("Tool call rejected by Groq, retrying without tools")
                msgs.append({"role": "system", "content": "Your tool call was invalid because some values are unknown. "
                             "Do not call tools now. Politely ask the patient for the missing details."})
                try:
                    m = client.chat.completions.create(model=MODEL, messages=msgs, temperature=0.3).choices[0].message
                except Exception:
                    return "Sorry, could you please tell me your age, gender, fever, cough type and city again?", doctors
            if not m.tool_calls:
                return (m.content or "").strip(), doctors
            msgs.append({"role": "assistant", "content": m.content or "", "tool_calls": [
                {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments or "{}"}}
                for c in m.tool_calls]})
            for c in m.tool_calls:
                out = tools.run_tool(c.function.name, json.loads(c.function.arguments or "{}"), user["id"], user_text)
                if c.function.name == "find_available_doctors":
                    doctors = out.get("doctors", [])
                msgs.append({"role": "tool", "tool_call_id": c.id, "content": json.dumps(out, default=str)})
        return "Sorry, I could not complete that. Please try again.", doctors
    except Exception as e:
        raise CustomException(e, sys)

def summarize(previous, user_msg, reply):
    """One short running summary instead of storing whole chats (saves tokens)."""
    try:
        p = (f"Previous summary: {previous or 'none'}\nPatient: {user_msg}\nAssistant: {reply}\n"
             "Update the summary in max 60 words: symptoms, conditions, doctors seen, follow-ups. Facts only.")
        r = get_client().chat.completions.create(model=MODEL, messages=[{"role": "user", "content": p}], temperature=0.1)
        return (r.choices[0].message.content or previous).strip()
    except Exception as e:
        raise CustomException(e, sys)