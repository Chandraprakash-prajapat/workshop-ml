import json
import time
from fastmcp.client.transports import StreamableHttpTransport
from mcp_clinic.auth import make_token
from fastmcp import Client
from chatbot.config import MODEL, get_client
from mcp_clinic.roles import can_use
from src.logger import get_logger

MCP_URL = "http://127.0.0.1:8003/mcp"
logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Sanjeevani Clinic assistant. You only help with clinic matters: doctors, specialties, free slots, appointments, prescriptions and bills.
- Use ONLY the tools you are given, and call a tool whenever one fits the question. Never state database facts from memory.
- Doctors and slots: doctor_details, available_doctors.
- A patient's own data: my_appointments, my_prescriptions, my_bills. If the user mentions a patient id, pass it as patient_id to my_appointments. Never guess a patient id. If a tool says access denied, politely tell the user they can only view their own information.
- Staff questions: list_patients (registered patients), all_appointments (appointments of the whole clinic), pending_bills (unpaid bills of all patients). If you have one of these tools and the question matches, CALL it. Only if you do not have a matching tool, politely say you are not allowed to share that.
- Answer ONLY from the tool result. Never invent doctors, timings, bills or any database information.
- If the tool says the doctor is not found, tell the user that doctor is not in our clinic.
- If the question is NOT about the clinic (technology, general knowledge, any other topic), politely say you can only help with clinic questions. Do not answer it from your own knowledge.
- You are not a doctor: no diagnosis, no medicines.
- Write the answer as plain text only: a short friendly sentence or simple lines starting with "-". No markdown, no asterisks, no tables. Never show JSON or raw tool output.
- Reply in the same language as the user (English or Hinglish)."""


# ---- Hybrid: fixed questions are answered WITHOUT the LLM (0 tokens) ----
# (tool, keywords in the question, roles that may use it, title, text if empty)
DIRECT = [
    ("my_prescriptions", ("my prescription", "my medicine", "meri prescription", "meri medicine"),
     ("user",), "Your prescriptions:", "You have no prescriptions yet."),
    ("my_bills", ("my bill", "mera bill", "mere bill"),
     ("user",), "Your bills:", "You have no bills yet."),
    ("my_appointments", ("my appointment", "my all appointment", "meri appointment", "my booking"),
     ("user", "super_admin"), "Your appointments:", "You have no appointments yet."),
    ("pending_bills", ("pending bill", "unpaid bill"),
     ("super_admin",), "Pending bills:", "There are no pending bills."),
    ("all_appointments", ("all appointment",),
     ("super_admin",), "Appointments of the clinic:", "There are no appointments yet."),
    ("list_patients", ("all patients", "list patients", "patients list", "registered patients"),
     ("super_admin",), "Registered patients:", "No patients are registered yet."),
]


def direct_tool(question, role):
    """Fixed question -> (tool, title, empty text). Anything else -> None (the LLM handles it)."""
    q = question.lower()
    if any(ch.isdigit() for ch in q):     # a patient id etc. -> let the LLM and the tool decide
        return None
    for tool, words, roles, title, empty in DIRECT:
        if role in roles and any(w in q for w in words):
            return tool, title, empty
    return None


def show(data, title, empty):
    """Tool result -> short plain text (hard-coded format, no LLM)."""
    if isinstance(data, dict) and data.get("success") is False:
        return data.get("message", "Not allowed.")
    rows = data
    if isinstance(data, dict):
        rows = next((v for v in data.values() if isinstance(v, list)), [])
    if not rows:
        return empty
    lines = []
    for r in rows:
        parts = [f"{str(k).replace('_', ' ').title()}: {v}"
                 for k, v in r.items() if k != "id" and v not in (None, "")]
        lines.append("- " + ", ".join(parts))
    text = title + "\n" + "\n".join(lines)
    if isinstance(data, dict) and "total_pending" in data:
        text += f"\nTotal pending: {data['total_pending']}"
    return text


def schema_of(t):
    return getattr(t, "input_schema", None) or t.inputSchema


def tool_for_ai(t):
    """Tool definition for Groq. The AI must never see (or fill) the user_id field."""
    params = json.loads(json.dumps(schema_of(t)))
    params.get("properties", {}).pop("user_id", None)
    if "user_id" in params.get("required", []):
        params["required"].remove("user_id")
    return {"type": "function",
            "function": {"name": t.name,
                         "description": t.description or t.name,
                         "parameters": params}}


def usage_of(resp):
    """Groq ke jawab se (input tokens, output tokens) nikalta hai."""
    u = getattr(resp, "usage", None)
    return (u.prompt_tokens or 0, u.completion_tokens or 0) if u else (0, 0)


async def ask_agent(question, user_id, role="user"):
    groq = get_client()
    start = time.time()
    tin = tout = 0                                   # total tokens of this question
    transport = StreamableHttpTransport(
        MCP_URL,
        headers={"X-Clinic-Token": make_token(user_id, role)},
    )
    async with Client(transport) as mcp:
        all_tools = await mcp.list_tools()
        tools = [t for t in all_tools if can_use(role, t.name)]     # RBAC: the AI only sees this role's tools
        needs_user = {t.name for t in tools if "user_id" in schema_of(t).get("properties", {})}

        # ---- fixed question? answer straight from the tool, no LLM ----
        d = direct_tool(question, role)
        if d and can_use(role, d[0]):
            tool, title, empty = d
            args = {"user_id": user_id} if tool in needs_user else {}
            result = await mcp.call_tool(tool, args)
            data = json.loads(json.dumps(result.data, default=str))
            logger.info(f"MCP DIRECT | user={user_id} | role={role} | q={question!r} | tool={tool} | tokens=0 | {time.time() - start:.2f}s")
            return {"answer": show(data, title, empty),
                    "tools_used": [{"tool": tool, "args": {}}],
                    "tokens": {"in": 0, "out": 0}}

        groq_tools = [tool_for_ai(t) for t in tools]
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question}]

        resp = groq.chat.completions.create(
            model=MODEL, messages=messages, tools=groq_tools,
            tool_choice="auto", temperature=0.2)
        a, b = usage_of(resp); tin += a; tout += b
        reply = resp.choices[0].message

        if not reply.tool_calls:
            logger.info(f"MCP chat | user={user_id} | role={role} | q={question!r} | tools=none | tokens={tin + tout} | {time.time() - start:.2f}s")
            return {"answer": reply.content, "tools_used": [],
                    "tokens": {"in": tin, "out": tout}}

        messages.append(reply)
        tools_used = []
        for c in reply.tool_calls:
            name = c.function.name
            if not can_use(role, name):       # second lock: even if the AI asks for a tool it was not given
                logger.warning(f"MCP DENIED | user={user_id} | role={role} | tool={name}")
                messages.append({"role": "tool", "tool_call_id": c.id,
                                 "content": json.dumps({"success": False, "message": "Access denied for your role."})})
                continue
            args = json.loads(c.function.arguments)
            if name in needs_user:
                args["user_id"] = user_id          # always from the login session, never from the AI
            result = await mcp.call_tool(name, args)
            messages.append({"role": "tool", "tool_call_id": c.id,
                             "content": json.dumps(result.data, default=str)})
            shown_args = {k: v for k, v in args.items() if k != "user_id"}
            tools_used.append({"tool": name, "args": shown_args})
            logger.info(f"MCP tool | user={user_id} | role={role} | tool={name} | args={shown_args}")

        final = groq.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.2)
        a, b = usage_of(final); tin += a; tout += b
        logger.info(f"MCP chat | user={user_id} | role={role} | q={question!r} | tools={[t['tool'] for t in tools_used]} | tokens={tin + tout} | {time.time() - start:.2f}s")
        return {"answer": final.choices[0].message.content, "tools_used": tools_used,
                "tokens": {"in": tin, "out": tout}}