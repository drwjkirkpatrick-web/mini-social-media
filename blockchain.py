"""
Blockchain-style audit log for tamper-evident record keeping.
NOTE: Every audit entry links to the previous entry via prev_hash.
WHY: If anyone edits a row in the DB, the hash chain breaks and we detect it.
"""

import hashlib
import sqlite3
from database import get_connection


def _hash_block(prev_hash: str, table_name: str, record_id: int, action: str,
                user_id: int, details: str, timestamp: str, nonce: int) -> str:
    """Compute SHA-256 hash of block contents."""
    payload = f"{prev_hash}|{table_name}|{record_id}|{action}|{user_id}|{details}|{timestamp}|{nonce}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_last_block_hash(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        "SELECT block_hash FROM audit_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return row["block_hash"] if row else "0" * 64


def add_block_within_conn(conn: sqlite3.Connection, table_name: str, record_id: int,
                          action: str, user_id: int = None, details: str = "") -> int:
    """Add audit block atomically within an existing transaction."""
    prev = get_last_block_hash(conn)
    timestamp = conn.execute("SELECT datetime('now')").fetchone()[0]
    nonce = 0
    while True:
        block_hash = _hash_block(prev, table_name, record_id, action, user_id or 0, details, timestamp, nonce)
        # Difficulty: first 4 chars must be 'a' for demo purposes (adjustable)
        if block_hash.startswith("a") or nonce > 100000:
            break
        nonce += 1
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO audit_log (table_name, record_id, action, user_id, details, timestamp, prev_hash, block_hash, nonce)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (table_name, record_id, action, user_id, details, timestamp, prev, block_hash, nonce),
    )
    return cursor.lastrowid


def verify_chain() -> dict:
    """Walk the chain and report any tampered blocks."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM audit_log ORDER BY id ASC").fetchall()
    issues = []
    prev_hash = "0" * 64
    for row in rows:
        expected = _hash_block(
            row["prev_hash"], row["table_name"], row["record_id"],
            row["action"], row["user_id"] or 0, row["details"] or "",
            row["timestamp"], row["nonce"],
        )
        if expected != row["block_hash"]:
            issues.append({
                "id": row["id"],
                "expected": expected,
                "actual": row["block_hash"],
                "action": row["action"],
            })
        prev_hash = row["block_hash"]
    conn.close()
    return {
        "total": len(rows),
        "issues": issues,
        "clean": len(issues) == 0,
    }
