"""All database operations (Create / Read / Update). No AI code here."""
import random, sys
from datetime import datetime
from chatbot.database.connection import execute, get_connection
from src.exception import CustomException

# ---------- users ----------
def create_user(name, email, password_hash):
    return execute("INSERT INTO users(name,email,password_hash) VALUES(%s,%s,%s)", (name, email, password_hash), commit=True)

def get_user_by_email(email):
    return execute("SELECT * FROM users WHERE email=%s", (email,), one=True)

def find_doctors_by_name(name):
    """Doctors whose name contains the text (e.g. 'anita' finds Dr. Anita Rao)."""
    name = name.lower().replace("dr.", "").replace("dr ", "").strip()
    return execute("SELECT id, name, specialty FROM doctors WHERE name LIKE %s", (f"%{name}%",))


# ---------- doctors & slots ----------
def get_available_doctors(specialty, doctor_id=None, max_doctors=3, max_slots=4):
    sql = """SELECT d.id doctor_id, d.name, d.specialty, s.id slot_id, s.slot_time FROM doctors d
             JOIN slots s ON s.doctor_id=d.id AND s.is_booked=0 AND s.slot_time>NOW() WHERE d.specialty=%s"""
    params = [specialty]
    if doctor_id:
        sql += " AND d.id=%s"; params.append(doctor_id)
    grouped = {}
    for r in execute(sql + " ORDER BY s.slot_time", params):
        g = grouped.setdefault(r["doctor_id"], {"doctor_id": r["doctor_id"], "name": r["name"], "specialty": r["specialty"], "slots": []})
        if len(g["slots"]) < max_slots:
            g["slots"].append({"id": r["slot_id"], "label": r["slot_time"].strftime("%a %d %b, %I:%M %p")})
    docs = list(grouped.values()); random.shuffle(docs)   # random: the AI never picks a "best" doctor
    return docs[:max_doctors]

def get_prior_doctor(user_id, specialty):
    return execute("""SELECT d.id, d.name FROM appointments a JOIN doctors d ON d.id=a.doctor_id
                      WHERE a.user_id=%s AND d.specialty=%s ORDER BY a.id DESC LIMIT 1""", (user_id, specialty), one=True)

# ---------- appointments ----------
def book_slot(user_id, slot_id):
    """Atomic: the UPDATE succeeds only if the slot is still free, so two users can't get the same slot."""
    try:
        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("UPDATE slots SET is_booked=1 WHERE id=%s AND is_booked=0 AND slot_time>NOW()", (slot_id,))
        if cur.rowcount == 0:
            conn.close(); return None
        cur.execute("SELECT s.doctor_id, s.slot_time, d.name FROM slots s JOIN doctors d ON d.id=s.doctor_id WHERE s.id=%s", (slot_id,))
        s = cur.fetchone()
        cur.execute("INSERT INTO appointments(user_id,doctor_id,slot_id) VALUES(%s,%s,%s)", (user_id, s["doctor_id"], slot_id))
        conn.commit(); cur.close(); conn.close()
        return {"doctor_id": s["doctor_id"], "doctor": s["name"], "when": s["slot_time"].strftime("%A, %d %b at %I:%M %p")}
    except Exception as e:
        raise CustomException(e, sys)

def get_user_appointments(user_id):
    rows = execute("""SELECT d.name, d.specialty, s.slot_time FROM appointments a JOIN doctors d ON d.id=a.doctor_id
                      JOIN slots s ON s.id=a.slot_id WHERE a.user_id=%s AND a.status='booked' ORDER BY s.slot_time DESC LIMIT 5""", (user_id,))
    return [{"name": r["name"], "specialty": r["specialty"], "when": r["slot_time"].strftime("%a %d %b, %I:%M %p")} for r in rows]

# ---------- history & summary ----------
def add_history(user_id, doctor_id, problem):
    return execute("INSERT INTO patient_history(user_id,doctor_id,problem) VALUES(%s,%s,%s)", (user_id, doctor_id, problem[:500]), commit=True)

def get_summary(user_id):
    r = execute("SELECT summary FROM summaries WHERE user_id=%s", (user_id,), one=True)
    return r["summary"] if r else ""

def save_summary(user_id, text):
    execute("INSERT INTO summaries(user_id,summary) VALUES(%s,%s) ON DUPLICATE KEY UPDATE summary=VALUES(summary)", (user_id, text), commit=True)


# ---------- profile page ----------
def get_user(user_id):
    return execute("SELECT id,name,email,created_at FROM users WHERE id=%s", (user_id,), one=True)

def list_appointments(user_id):
    """All appointments of a patient with token number (1st booked patient of that doctor that day = token 1)."""
    rows = execute("""SELECT a.id, a.status, d.name doctor, d.specialty, s.slot_time,
                 (SELECT COUNT(*) FROM appointments a2 JOIN slots s2 ON s2.id=a2.slot_id
                   WHERE a2.doctor_id=a.doctor_id AND a2.status='booked'
                     AND DATE(s2.slot_time)=DATE(s.slot_time) AND s2.slot_time<=s.slot_time) token
              FROM appointments a JOIN doctors d ON d.id=a.doctor_id JOIN slots s ON s.id=a.slot_id
              WHERE a.user_id=%s ORDER BY s.slot_time DESC""", (user_id,))
    now = datetime.now()
    out = []
    for r in rows:
        upcoming = r["status"] == "booked" and r["slot_time"] > now
        out.append({"id": r["id"], "doctor": r["doctor"], "specialty": r["specialty"],
                    "date": r["slot_time"].strftime("%a, %d %b %Y"), "time": r["slot_time"].strftime("%I:%M %p"),
                    "day": r["slot_time"].strftime("%Y-%m-%d"),
                    "status": "cancelled" if r["status"] == "cancelled" else ("upcoming" if upcoming else "past"),
                    "token": r["token"] if r["status"] == "booked" else None, "can_cancel": upcoming})
    return out

def cancel_appointment(user_id, appointment_id):
    """Cancel an upcoming appointment of this patient and free its slot. Returns True if cancelled."""
    try:
        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT a.slot_id FROM appointments a JOIN slots s ON s.id=a.slot_id
                       WHERE a.id=%s AND a.user_id=%s AND a.status='booked' AND s.slot_time>NOW()""", (appointment_id, user_id))
        row = cur.fetchone()
        if not row:
            conn.close(); return False
        cur.execute("UPDATE appointments SET status='cancelled' WHERE id=%s", (appointment_id,))
        cur.execute("UPDATE slots SET is_booked=0 WHERE id=%s", (row["slot_id"],))
        conn.commit(); cur.close(); conn.close()
        return True
    except Exception as e:
        raise CustomException(e, sys)

def save_screening(user_id, age, gender, fever, cough, city, result, confidence, source):
    return execute("""INSERT INTO screenings(user_id,age,gender,fever,cough,city,result,confidence,source)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                   (user_id, age, gender, fever, cough, city, result, confidence, source), commit=True)

def list_screenings(user_id, limit=20):
    rows = execute("SELECT * FROM screenings WHERE user_id=%s ORDER BY id DESC LIMIT %s", (user_id, limit))
    return [{"when": r["created_at"].strftime("%d %b %Y, %I:%M %p"), "age": r["age"], "gender": r["gender"],
             "fever": r["fever"], "cough": r["cough"], "city": r["city"], "result": r["result"],
             "confidence": r["confidence"], "source": r["source"]} for r in rows]

def list_history(user_id, limit=10):
    rows = execute("""SELECT d.name doctor, d.specialty, h.problem, h.created_at FROM patient_history h
                      JOIN doctors d ON d.id=h.doctor_id WHERE h.user_id=%s ORDER BY h.id DESC LIMIT %s""", (user_id, limit))
    return [{"doctor": r["doctor"], "specialty": r["specialty"], "problem": r["problem"],
             "when": r["created_at"].strftime("%d %b %Y")} for r in rows]


# ---------- reschedule (same doctor, another free time) ----------
def free_slots_for_appointment(user_id, appointment_id, limit=12):
    """Other free times of the same doctor, used by the Reschedule button."""
    rows = execute("""SELECT s.id, s.slot_time FROM appointments a
                      JOIN slots s ON s.doctor_id=a.doctor_id AND s.is_booked=0 AND s.slot_time>NOW()
                      WHERE a.id=%s AND a.user_id=%s AND a.status='booked' ORDER BY s.slot_time LIMIT %s""",
                   (appointment_id, user_id, limit))
    return [{"id": r["id"], "label": r["slot_time"].strftime("%a %d %b, %I:%M %p")} for r in rows]

def reschedule_appointment(user_id, appointment_id, new_slot_id):
    """Take the new slot first (atomic), then move the appointment and free the old slot."""
    try:
        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT a.slot_id, a.doctor_id FROM appointments a JOIN slots s ON s.id=a.slot_id
                       WHERE a.id=%s AND a.user_id=%s AND a.status='booked' AND s.slot_time>NOW()""", (appointment_id, user_id))
        old = cur.fetchone()
        if not old:
            conn.close(); return None
        cur.execute("UPDATE slots SET is_booked=1 WHERE id=%s AND doctor_id=%s AND is_booked=0 AND slot_time>NOW()",
                    (new_slot_id, old["doctor_id"]))
        if cur.rowcount == 0:
            conn.close(); return None
        cur.execute("UPDATE appointments SET slot_id=%s WHERE id=%s", (new_slot_id, appointment_id))
        cur.execute("UPDATE slots SET is_booked=0 WHERE id=%s", (old["slot_id"],))
        cur.execute("SELECT slot_time FROM slots WHERE id=%s", (new_slot_id,))
        when = cur.fetchone()["slot_time"].strftime("%A, %d %b at %I:%M %p")
        conn.commit(); cur.close(); conn.close()
        return {"when": when}
    except Exception as e:
        raise CustomException(e, sys)

# ---------- assigned doctor ----------
def get_assigned_doctor(user_id):
    """The doctor this patient has booked most often recently, with number of visits."""
    return execute("""SELECT d.name, d.specialty, COUNT(*) visits FROM appointments a JOIN doctors d ON d.id=a.doctor_id
                      WHERE a.user_id=%s AND a.status='booked' GROUP BY d.id, d.name, d.specialty
                      ORDER BY MAX(a.id) DESC LIMIT 1""", (user_id,), one=True)

# ---------- prescriptions, bills, medical records (staff add, patient reads) ----------
def _day(ts):
    return ts.strftime("%d %b %Y")

def list_prescriptions(user_id):
    rows = execute("""SELECT p.medicine, p.dosage, p.notes, p.created_at, d.name doctor FROM prescriptions p
                      LEFT JOIN doctors d ON d.id=p.doctor_id WHERE p.user_id=%s ORDER BY p.id DESC""", (user_id,))
    return [{"medicine": r["medicine"], "dosage": r["dosage"] or "", "notes": r["notes"] or "",
             "doctor": r["doctor"] or "", "date": _day(r["created_at"])} for r in rows]

def list_bills(user_id):
    rows = execute("SELECT id, description, amount, status, created_at FROM bills WHERE user_id=%s ORDER BY id DESC", (user_id,))
    return [{"id": r["id"], "description": r["description"], "amount": float(r["amount"]),
             "status": r["status"], "date": _day(r["created_at"])} for r in rows]

def list_records(user_id):
    rows = execute("""SELECT r.title, r.record_type, r.summary, r.created_at, d.name doctor FROM medical_records r
                      LEFT JOIN doctors d ON d.id=r.doctor_id WHERE r.user_id=%s ORDER BY r.id DESC""", (user_id,))
    return [{"title": r["title"], "type": r["record_type"] or "", "summary": r["summary"] or "",
             "doctor": r["doctor"] or "", "date": _day(r["created_at"])} for r in rows]

def _doctor_id(name):
    row = execute("SELECT id FROM doctors WHERE name=%s", (name,), one=True) if name else None
    return row["id"] if row else None

def add_prescription(user_id, doctor_name, medicine, dosage, notes):
    return execute("INSERT INTO prescriptions(user_id,doctor_id,medicine,dosage,notes) VALUES(%s,%s,%s,%s,%s)",
                   (user_id, _doctor_id(doctor_name), medicine, dosage, notes), commit=True)

def add_bill(user_id, description, amount, status):
    return execute("INSERT INTO bills(user_id,description,amount,status) VALUES(%s,%s,%s,%s)",
                   (user_id, description, amount, status), commit=True)

def add_record(user_id, doctor_name, title, record_type, summary):
    return execute("INSERT INTO medical_records(user_id,doctor_id,title,record_type,summary) VALUES(%s,%s,%s,%s,%s)",
                   (user_id, _doctor_id(doctor_name), title, record_type, summary), commit=True)

def list_doctor_names():
    return [r["name"] for r in execute("SELECT name FROM doctors ORDER BY name")]


# def list_all_patients():
#     """Admin only: all registered patients (never the password hash)."""
#     return execute("SELECT id, name, email FROM users ORDER BY id")


def list_all_patients():
    """Admin only: registered patients. Staff accounts (ADMIN_EMAILS) and password hashes are never included."""
    import os
    staff = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]
    rows = execute("SELECT id, name, email FROM users ORDER BY id")
    return [r for r in rows if r["email"].lower() not in staff]



def _clean(rows):
    """Decimal / datetime ko text bana deta hai, taaki JSON me aaram se jaye."""
    ok = (int, float, str, type(None))
    return [{k: (v if isinstance(v, ok) else str(v)) for k, v in r.items()} for r in rows]


def get_prescriptions(user_id):
    return _clean(execute(
        "SELECT p.id, p.medicine, p.dosage, p.notes, d.name AS doctor, p.created_at "
        "FROM prescriptions p LEFT JOIN doctors d ON d.id = p.doctor_id "
        "WHERE p.user_id = %s ORDER BY p.created_at DESC", (user_id,)))


def get_bills(user_id):
    return _clean(execute(
        "SELECT id, description, amount, status, created_at FROM bills "
        "WHERE user_id = %s ORDER BY created_at DESC", (user_id,)))


def all_appointments_admin():
    return _clean(execute(
        "SELECT a.id, u.name AS patient, d.name AS doctor, s.slot_time, a.status "
        "FROM appointments a "
        "JOIN users u ON u.id = a.user_id "
        "JOIN doctors d ON d.id = a.doctor_id "
        "JOIN slots s ON s.id = a.slot_id "
        "ORDER BY s.slot_time DESC LIMIT 50"))


def pending_bills_admin():
    rows = _clean(execute(
        "SELECT b.id, u.name AS patient, b.description, b.amount, b.created_at "
        "FROM bills b JOIN users u ON u.id = b.user_id "
        "WHERE b.status = 'pending' ORDER BY b.created_at DESC"))
    total = sum(float(r["amount"]) for r in rows)
    return {"bills": rows, "total_pending": total}


def db_ping():
    return execute("SELECT 1 AS ok")[0]["ok"] == 1


def table_counts():
    def n(sql):
        return execute(sql)[0]["n"]
    return {
        "users": n("SELECT COUNT(*) AS n FROM users"),
        "doctors": n("SELECT COUNT(*) AS n FROM doctors"),
        "appointments_booked": n("SELECT COUNT(*) AS n FROM appointments WHERE status = 'booked'"),
    }
    
def log_request(user_id, role, method, path, status_code, tool, tokens_in, tokens_out, latency_ms):
    """Har chat request ka ek record (dashboard isi table se numbers nikalega)."""
    execute(
        "INSERT INTO api_logs (user_id, role, method, path, status_code, tool, "
        "tokens_in, tokens_out, tokens_total, latency_ms) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (user_id, role, method, path, status_code, tool,
         tokens_in, tokens_out, tokens_in + tokens_out, latency_ms),
        commit=True)    


def dashboard_stats():
    """Super admin dashboard ke numbers (api_logs se)."""
    totals = execute(
        "SELECT COUNT(*) AS hits, COALESCE(SUM(tokens_total),0) AS tokens, "
        "COALESCE(SUM(tokens_in),0) AS tin, COALESCE(SUM(tokens_out),0) AS tout "
        "FROM api_logs", one=True)
    codes = execute(
        "SELECT status_code, COUNT(*) AS n FROM api_logs "
        "GROUP BY status_code ORDER BY status_code")
    return {"totals": _clean([totals])[0], "codes": codes}