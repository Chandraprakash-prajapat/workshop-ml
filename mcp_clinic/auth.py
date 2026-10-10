import os
import time
import jwt
from dotenv import load_dotenv

load_dotenv()
SECRET = os.getenv("JWT_SECRET", "")


def make_token(user_id, role):
    """App ye banata hai. 60 second ke liye valid."""
    now = int(time.time())
    payload = {"user_id": user_id, "role": role, "iat": now, "exp": now + 60}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def verify_token(token):
    """MCP server ye check karta hai. Galat ya expire ho to error."""
    return jwt.decode(token, SECRET, algorithms=["HS256"])