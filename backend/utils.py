"""
Utility functions: JWT auth, password hashing, logging, OCR stub.
"""
import jwt
import hashlib
import logging
import datetime
import os
from typing import Optional, Dict, Any

SECRET_KEY = os.environ.get("JWT_SECRET", "learning-saas-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("learning_saas")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hash_str: str) -> bool:
    return hash_password(password) == hash_str

def create_access_token(data: Dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None

def verify_token_dependency(token: str) -> Optional[Dict]:
    """Dependency: extract and validate token from Authorization header"""
    if token.startswith("Bearer "):
        token = token[7:]
    return decode_access_token(token)

def calc_week_over_week(current: float, previous: float) -> float:
    """\u5468\u73af\u6bd4\u589e\u957f\u7387"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 2)

def calc_accuracy(correct: int, total: int) -> float:
    if total == 0: return 0.0
    return round(correct / total, 4)

def is_high_risk(recent_results: list) -> bool:
    """\u8fde\u7eed3\u6b21\u6b63\u786e\u7387<50%\u5219\u4e3a\u9ad8\u5371"""
    if len(recent_results) < 3: return False
    recent = recent_results[-3:]
    correct = sum(1 for r in recent if r)
    return correct / 3 < 0.5

def is_mastered(recent_results: list) -> bool:
    """\u8fde\u7eed5\u6b21\u6b63\u786e\u7387>=90%\u5219\u8fbe\u6807"""
    if len(recent_results) < 5: return False
    recent = recent_results[-5:]
    correct = sum(1 for r in recent if r)
    return correct / 5 >= 0.9

def memory_decay_risk(days_since_review: int, threshold: int = 5) -> bool:
    """\u8d85\u8fc7threshold\u5929\u672a\u590d\u4e60\u5219\u89e6\u53d1\u63d0\u9192"""
    return days_since_review >= threshold