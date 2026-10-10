"""Clinic staff page (/admin): add prescriptions, bills and medical records for a patient.

Staff = users whose email is listed in ADMIN_EMAILS in .env (comma separated).
Patients can only READ these items on their profile page.
"""
import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from chatbot.database import crud

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def is_staff(user_id):
    allowed = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]
    user = crud.get_user(user_id)
    return bool(user and user["email"].lower() in allowed)


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    u = request.session.get("user")
    ok = bool(u and is_staff(u["id"]))
    return templates.TemplateResponse(request, "admin.html", {"allowed": ok, "logged_in": bool(u),
                                                              "doctors": crud.list_doctor_names() if ok else []})


class Item(BaseModel):
    patient_email: str
    doctor: str = ""
    medicine: str = ""; dosage: str = ""; notes: str = ""          # prescription
    description: str = ""; amount: float = 0; status: str = "pending"   # bill
    title: str = ""; record_type: str = ""; summary: str = ""      # medical record


@router.post("/admin/add/{kind}")
async def add_item(kind: str, body: Item, request: Request):
    u = request.session.get("user")
    if not u or not is_staff(u["id"]):
        raise HTTPException(403, "Only clinic staff can do this")
    patient = crud.get_user_by_email(body.patient_email.strip().lower())
    if not patient:
        raise HTTPException(404, "No patient with that email")
    if kind == "prescription" and body.medicine.strip():
        crud.add_prescription(patient["id"], body.doctor, body.medicine.strip()[:150], body.dosage[:150], body.notes[:300])
    elif kind == "bill" and body.description.strip() and body.amount > 0:
        crud.add_bill(patient["id"], body.description.strip()[:200], body.amount, "paid" if body.status == "paid" else "pending")
    elif kind == "record" and body.title.strip():
        crud.add_record(patient["id"], body.doctor, body.title.strip()[:150], body.record_type[:40], body.summary[:500])
    else:
        raise HTTPException(400, "Please fill in the required fields")
    return {"ok": True, "patient": patient["name"]}
