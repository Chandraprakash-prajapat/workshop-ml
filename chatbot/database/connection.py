import os
import sys
from datetime import datetime, timedelta
 
import mysql.connector
 
from src.exception import CustomException
from src.logger import get_logger
import chatbot.config  # this import loads the .env file
 
logger = get_logger(__name__)
 
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")
DATABASE_NAME = os.getenv("MYSQL_DATABASE", "clinic")
 
 
def get_connection(use_database=True):
    """Open a connection to MySQL using the values from .env"""
    settings = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
    }
    if use_database:
        settings["database"] = DATABASE_NAME
    return mysql.connector.connect(**settings)
 
 
def execute(sql, params=(), one=False, commit=False):
    """Run one SQL query.
 
    SELECT query  -> returns rows (or one row if one=True)
    INSERT/UPDATE -> use commit=True, returns the id of the new row
    """
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql, params)
 
        if commit:
            connection.commit()
            result = cursor.lastrowid
        elif one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
 
        cursor.close()
        connection.close()
        return result
    except Exception as e:
        raise CustomException(e, sys)
 
 
def read_schema_statements():
    """Read schema.sql and return a list of single SQL statements."""
    with open(SCHEMA_FILE, encoding="utf-8") as file:
        lines = file.readlines()
 
    lines_without_comments = []
    for line in lines:
        line = line.split("--")[0]          # remove SQL comment
        lines_without_comments.append(line)
 
    text = "\n".join(lines_without_comments)
    statements = []
    for statement in text.split(";"):
        cleaned = statement.strip().upper()
        if not cleaned:
            continue
        # init_db() already creates and selects the database, so skip these lines
        # (DROP DATABASE is skipped too, so a mistake in schema.sql can never delete your data)
        if cleaned.startswith(("CREATE DATABASE", "USE ", "DROP DATABASE")):
            continue
        statements.append(statement)
    return statements
 
 
def add_slots(cursor):
    """Add slots for today and the next 3 days (existing slots are skipped)."""
    cursor.execute("SELECT id FROM doctors")
    doctor_ids = [row[0] for row in cursor.fetchall()]
 
    hours = [10, 11, 12, 16, 17]            # 10am, 11am, 12pm, 4pm, 5pm
    today = datetime.now().replace(minute=0, second=0, microsecond=0)
 
    rows = []
    for doctor_id in doctor_ids:
        for day in range(0, 4):
            for hour in hours:
                slot_time = (today + timedelta(days=day)).replace(hour=hour)
                rows.append((doctor_id, slot_time))
 
    cursor.executemany(
        "INSERT IGNORE INTO slots(doctor_id, slot_time) VALUES(%s, %s)", rows
    )
 
 
def add_missing_columns(cursor):
    """Old databases made before this version get the new 'status' column here."""
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema=%s AND table_name='appointments' AND column_name='status'", (DATABASE_NAME,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE appointments ADD COLUMN status VARCHAR(12) NOT NULL DEFAULT 'booked'")


def init_db():
    """Create the database, tables, doctors and slots. Safe to run many times."""
    try:
        connection = get_connection(use_database=False)
        cursor = connection.cursor()
 
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DATABASE_NAME}`")
        cursor.execute(f"USE `{DATABASE_NAME}`")
 
        for statement in read_schema_statements():
            cursor.execute(statement)
 
        add_missing_columns(cursor)
        add_slots(cursor)
 
        connection.commit()
        cursor.close()
        connection.close()
        logger.info("Clinic database ready")
    except Exception as e:
        raise CustomException(e, sys)
 
