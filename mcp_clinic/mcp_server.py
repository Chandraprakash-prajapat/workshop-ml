from fastmcp import FastMCP
from chatbot.database import crud
from chatbot.config import SPECIALTIES
import jwt
from fastmcp.server.dependencies import get_http_headers
from mcp_clinic.auth import verify_token

mcp = FastMCP("Sanjeevani Clinic MCP Server")

def who():
    """Request ke token se (user_id, role) nikalta hai. Token galat ho to Unauthorized."""
    token = get_http_headers(include_all=True).get("x-clinic-token", "")
    try:
        return verify_token(token)
    except jwt.PyJWTError:
        raise ValueError("Unauthorized: valid token required.")

@mcp.tool()
def doctor_details(name: str):
    """Get details (name and specialty) of a doctor from the clinic database by doctor name."""
    me = who()
    doctors = crud.find_doctors_by_name(name.strip())
    if not doctors:
        return {"success": False, "message": f"No doctor named '{name}' in our database."}
    return {"success": True, "doctors": doctors}


@mcp.tool()
def available_doctors(specialty: str):
    """List doctors of a given specialty who have free appointment slots."""
    me = who()
    if specialty not in SPECIALTIES:
        return {"success": False, "message": f"Unknown specialty. Choose from {SPECIALTIES}"}
    doctors = crud.get_available_doctors(specialty)
    if not doctors:
        return {"success": False, "message": f"No free slots for {specialty} right now."}
    return {"success": True, "doctors": doctors}


@mcp.tool()
def my_appointments(user_id: int, patient_id: int = 0):
    """Show appointments of a patient. user_id is the logged-in patient and is filled in by the system. Set patient_id only if the user mentions a patient id."""
    me = who()
    if patient_id and patient_id != user_id:
        return {"success": False, "message": "Access denied. You can only view your own appointments."}
    appts = crud.get_user_appointments(user_id)
    if not appts:
        return {"success": False, "message": "You have no appointments yet."}
    return {"success": True, "appointments": appts}


@mcp.tool()
def list_patients():
    """ADMIN ONLY: list all registered patients (id, name, email)."""
    me = who()
    if me["role"] != "super_admin":
        return {"success": False, "message": "Access denied. Admin only."}
    return {"success": True, "patients": crud.list_all_patients()}


@mcp.tool()
def my_prescriptions(user_id: int):
    """Show the logged-in patient's own prescriptions (medicine, dosage, doctor)."""
    me = who()
    user_id = me["user_id"]
    return {"success": True, "prescriptions": crud.get_prescriptions(user_id)}


@mcp.tool()
def my_bills(user_id: int):
    """Show the logged-in patient's own bills (description, amount, pending or paid)."""
    me = who()
    user_id = me["user_id"]
    return {"success": True, "bills": crud.get_bills(user_id)}


@mcp.tool()
def all_appointments():
    """Admin only. Use when staff asks for all appointments of the clinic, appointments of every patient, or the clinic's booking list."""
    me = who()
    if me["role"] != "super_admin":
        return {"success": False, "message": "Access denied. Admin only."}
    return {"success": True, "appointments": crud.all_appointments_admin()}


@mcp.tool()
def pending_bills():
    """Admin only. Use when staff asks for pending, unpaid or outstanding bills of patients, or how much money is due."""    
    me = who()
    if me["role"] != "super_admin":
        return {"success": False, "message": "Access denied. Admin only."}
    return {"success": True, **crud.pending_bills_admin()}


@mcp.tool()
def system_health():
    """System only: checks whether the database is reachable."""
    me = who()
    if me["role"] != "system":
        return {"success": False, "message": "Access denied. System only."}
    return {"success": True, "database": "ok" if crud.db_ping() else "down"}


@mcp.tool()
def system_stats():
    """System only: counts of users, doctors and booked appointments."""
    me = who()
    if me["role"] != "system":
        return {"success": False, "message": "Access denied. System only."}
    return {"success": True, **crud.table_counts()}



if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8003)