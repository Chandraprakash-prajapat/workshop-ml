import os
import sqlite3
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))          # project root, taaki `src` import ho
try:
    from src.logger import get_logger          # local: project ka logger
except ImportError:                            # Vercel: src folder nahi hota
    import logging
    logging.basicConfig(level=logging.INFO)
    get_logger = logging.getLogger

logger = get_logger(__name__)

# Vercel par sirf /tmp me likh sakte hain (wo bhi temporary)
DATA_DIR = "/tmp" if os.getenv("VERCEL") else BASE_DIR
DB_PATH = os.path.join(DATA_DIR, "cafe.db")
CAPACITY = {"breakfast": 20, "lunch": 30, "dinner": 30}      # har meal ki seats


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """ create booking table if not available """
    conn = connect()
    conn.execute("""CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT, date TEXT, meal TEXT, members INTEGER, created_at TEXT)""")
    conn.commit()
    conn.close()


def check_availability(date, meal, members):
    """Check availability.  date format: YYYY-MM-DD,  meal: breakfast / lunch / dinner"""
    if members < 1:
        return {"available": False, "seats_left": 0, "message": "Members must be at least 1"}
    if meal not in CAPACITY:
        return {"available": False, "seats_left": 0, "message": "Meal must be breakfast, lunch or dinner"}
    conn = connect()
    booked = conn.execute("SELECT COALESCE(SUM(members), 0) FROM bookings WHERE date = ? AND meal = ?",
                          (date, meal)).fetchone()[0]
    conn.close()
    seats_left = CAPACITY[meal] - booked
    result = {"available": seats_left >= members, "seats_left": seats_left}
    logger.info(f"check_availability | {date} {meal} members={members} -> {result}")
    return result


def create_booking(date, meal, members, name="Guest"):
    """If seats available the create booking."""
    check = check_availability(date, meal, members)
    if not check["available"]:
        return {"status": "not_available", "seats_left": check["seats_left"]}
    conn = connect()
    cur = conn.execute("INSERT INTO bookings (name, date, meal, members, created_at) VALUES (?, ?, ?, ?, ?)",
                       (name, date, meal, members, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    booking_id = cur.lastrowid
    conn.close()
    logger.info(f"create_booking | CONFIRMED id={booking_id} {date} {meal} members={members} name={name}")
    return {"status": "confirmed", "booking_id": booking_id, "date": date, "meal": meal,
            "members": members, "name": name}