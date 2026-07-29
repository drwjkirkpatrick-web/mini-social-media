"""
Authentication utilities — now with quantum-safe Argon2id support.
NOTE: Argon2id is memory-hard and resistant to both GPU and (future) quantum
decryption attacks. Unlike PBKDF2, it requires significant RAM per hash,
which quantum algorithms cannot shortcut.
WHY: Post-quantum password security for long-term data protection.
"""

import time
import re
from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash

# Optional Argon2id for quantum-safe hashing
try:
    from argon2 import PasswordHasher
    _ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1, hash_len=32, salt_len=16)
    _argon2_available = True
except ImportError:
    _ph = None
    _argon2_available = False

# In-memory rate limiter: {ip: [timestamp, ...]}
_rate_limit_store = {}


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain: str, algorithm: str = "argon2id") -> str:
    """Hash a password with Argon2id (default) or PBKDF2 (legacy)."""
    if algorithm == "argon2id" and _argon2_available:
        return _ph.hash(plain)
    # Legacy PBKDF2 fallback
    return generate_password_hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against either Argon2id or PBKDF2 hash."""
    if not hashed:
        return False
    if hashed.startswith("$argon2id$") and _argon2_available:
        try:
            _ph.verify(hashed, plain)
            return True
        except Exception:
            return False
    # Legacy PBKDF2
    return check_password_hash(hashed, plain)


def needs_rehash(hashed: str) -> bool:
    """Return True if a non-Argon2id hash should be upgraded."""
    if not _argon2_available:
        return False
    if hashed.startswith("pbkdf2:sha256:") or hashed.startswith("scrypt:"):
        return True
    if hashed.startswith("$argon2id$"):
        try:
            return _ph.check_needs_rehash(hashed)
        except Exception:
            return True
    return False


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

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
