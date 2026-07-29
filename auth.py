"""
Authentication utilities.
NOTE: Uses Werkzeug PBKDF2 — not raw SHA-256.
WHY: Salted hashing is the industry standard for password storage.
"""

import time
from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash

# In-memory rate limiter: {ip: [timestamp, ...]}
_rate_limit_store = {}


def hash_password(plain: str) -> str:
    return generate_password_hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return check_password_hash(hashed, plain)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Permission denied.", "error")
            return redirect(url_for("feed"))
        return f(*args, **kwargs)
    return decorated


def check_rate_limit(ip: str, max_attempts: int = 10, window: int = 300) -> bool:
    """Return True if allowed, False if rate limited."""
    now = time.time()
    attempts = _rate_limit_store.get(ip, [])
    attempts = [t for t in attempts if now - t < window]
    if len(attempts) >= max_attempts:
        return False
    attempts.append(now)
    _rate_limit_store[ip] = attempts
    return True
