"""
mini-social-media database layer.
NOTE: Uses sqlite3.Row for dict-like row access.
WHY: Dict-like access makes template rendering and JSON serialization easier.
"""

import sqlite3
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# NOTE: Import config here creates a dependency; we avoid circular imports
# by only using get_config() at call sites, not at module init.
DATABASE_PATH = os.environ.get("MINI_SOCIAL_DB", "data/social.db")


def get_connection() -> sqlite3.Connection:
    """Return a configured SQLite connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_database():
    """Create all tables and seed if empty."""
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            bio TEXT DEFAULT '',
            avatar_url TEXT,
            cover_url TEXT,
            pronouns TEXT,
            location TEXT,
            role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Posts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content_type TEXT NOT NULL CHECK(content_type IN ('text', 'link', 'photo')),
            text_content TEXT,
            link_url TEXT,
            photo_url TEXT,
            visibility TEXT DEFAULT 'friends' CHECK(visibility IN ('friends', 'only_me')),
            moderation_status TEXT DEFAULT 'pending' CHECK(moderation_status IN ('pending', 'approved', 'rejected')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Friendships
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            addressee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(requester_id, addressee_id)
        )
    """)

    # Post likes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, post_id)
        )
    """)

    # Post comments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Blocks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, target_id)
        )
    """)

    # Personal pages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            slug TEXT NOT NULL,
            content_json TEXT NOT NULL DEFAULT '{}',
            is_public INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, slug)
        )
    """)

    # Audit log (blockchain-linked)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            action TEXT NOT NULL,
            user_id INTEGER,
            details TEXT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            prev_hash TEXT DEFAULT '',
            block_hash TEXT NOT NULL,
            nonce INTEGER DEFAULT 0
        )
    """)

    # Notifications (for friend requests, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            reference_id INTEGER,
            text TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Migrations: add missing columns if upgrading
    cursor.execute("PRAGMA table_info(users)")
    existing = {r[1] for r in cursor.fetchall()}
    for col, ddl in [
        ("pronouns", "ALTER TABLE users ADD COLUMN pronouns TEXT"),
        ("location", "ALTER TABLE users ADD COLUMN location TEXT"),
        ("avatar_url", "ALTER TABLE users ADD COLUMN avatar_url TEXT"),
        ("cover_url", "ALTER TABLE users ADD COLUMN cover_url TEXT"),
    ]:
        if col not in existing:
            cursor.execute(ddl)

    conn.commit()
    conn.close()
    print("Database initialized.")


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def create_user(username: str, email: str, password_hash: str, display_name: str = "", role: str = "user") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, display_name, role) VALUES (?, ?, ?, ?, ?)",
        (username, email, password_hash, display_name or username, role),
    )
    conn.commit()
    uid = cursor.lastrowid
    conn.close()
    return uid


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user(user_id: int, **fields) -> bool:
    """Update user with column whitelist. Only these fields may be changed."""
    allowed = {"display_name", "bio", "avatar_url", "cover_url", "pronouns", "location"}
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        return False
    conn = get_connection()
    set_clause = ", ".join(f"{k} = ?" for k in safe)
    values = list(safe.values()) + [user_id]
    conn.execute(f"UPDATE users SET {set_clause}, updated_at = datetime('now') WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def list_users(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT id, username, display_name, avatar_url, created_at FROM users LIMIT ? OFFSET ?",
                        (limit, offset)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Post CRUD
# ---------------------------------------------------------------------------

def create_post(user_id: int, content_type: str, text_content: Optional[str] = None,
                link_url: Optional[str] = None, photo_url: Optional[str] = None,
                visibility: str = "friends") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO posts (user_id, content_type, text_content, link_url, photo_url, visibility)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, content_type, text_content, link_url, photo_url, visibility),
    )
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id


def get_post(post_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_posts_by_user(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (user_id, limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Friendship CRUD
# ---------------------------------------------------------------------------

def send_friend_request(requester_id: int, addressee_id: int) -> int:
    if requester_id == addressee_id:
        raise ValueError("Cannot friend yourself.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO friendships (requester_id, addressee_id, status)
           VALUES (?, ?, 'pending')
           ON CONFLICT(requester_id, addressee_id) DO UPDATE SET updated_at=datetime('now')
           RETURNING id""",
        (requester_id, addressee_id),
    )
    row = cursor.fetchone()
    if row is None:
        # Already existed; fetch existing
        row = conn.execute(
            "SELECT id FROM friendships WHERE requester_id=? AND addressee_id=?",
            (requester_id, addressee_id),
        ).fetchone()
    fid = row["id"] if row else 0
    conn.commit()
    conn.close()
    return fid


def get_friendship(user_a: int, user_b: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute(
        """SELECT * FROM friendships
           WHERE (requester_id=? AND addressee_id=?)
              OR (requester_id=? AND addressee_id=?)""",
        (user_a, user_b, user_b, user_a),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def accept_friend_request(friendship_id: int) -> bool:
    conn = get_connection()
    conn.execute("UPDATE friendships SET status='accepted', updated_at=datetime('now') WHERE id=?", (friendship_id,))
    conn.commit()
    conn.close()
    return True


def reject_friend_request(friendship_id: int) -> bool:
    conn = get_connection()
    conn.execute("UPDATE friendships SET status='rejected', updated_at=datetime('now') WHERE id=?", (friendship_id,))
    conn.commit()
    conn.close()
    return True


def delete_friendship(friendship_id: int) -> bool:
    conn = get_connection()
    conn.execute("DELETE FROM friendships WHERE id=?", (friendship_id,))
    conn.commit()
    conn.close()
    return True


def list_friends(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT u.id, u.username, u.display_name, u.avatar_url, f.status, f.id as friendship_id
           FROM friendships f
           JOIN users u ON (u.id = f.requester_id OR u.id = f.addressee_id)
           WHERE (f.requester_id=? OR f.addressee_id=?)
             AND f.status='accepted'
             AND u.id != ?""",
        (user_id, user_id, user_id),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_pending_requests(user_id: int, direction: str = "received") -> List[Dict[str, Any]]:
    """direction: 'received' (others sent to me) or 'sent' (I sent to others)."""
    conn = get_connection()
    if direction == "received":
        rows = conn.execute(
            """SELECT f.*, u.username, u.display_name, u.avatar_url
               FROM friendships f
               JOIN users u ON u.id = f.requester_id
               WHERE f.addressee_id=? AND f.status='pending'""",
            (user_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT f.*, u.username, u.display_name, u.avatar_url
               FROM friendships f
               JOIN users u ON u.id = f.addressee_id
               WHERE f.requester_id=? AND f.status='pending'""",
            (user_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Like CRUD
# ---------------------------------------------------------------------------

def like_post(user_id: int, post_id: int) -> bool:
    """Toggle like. Returns True if post is now liked, False if unliked."""
    conn = get_connection()
    cursor = conn.cursor()
    existing = conn.execute(
        "SELECT id FROM post_likes WHERE user_id=? AND post_id=?", (user_id, post_id)
    ).fetchone()
    if existing:
        cursor.execute("DELETE FROM post_likes WHERE user_id=? AND post_id=?", (user_id, post_id))
        liked = False
    else:
        cursor.execute("INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        liked = True
    conn.commit()
    conn.close()
    return liked


def count_likes(post_id: int) -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as c FROM post_likes WHERE post_id=?", (post_id,)).fetchone()
    conn.close()
    return row["c"] if row else 0


# ---------------------------------------------------------------------------
# Comment CRUD
# ---------------------------------------------------------------------------

def add_comment(user_id: int, post_id: int, text: str) -> int:
    if len(text) > 1000:
        raise ValueError("Comment too long (max 1000 chars).")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO post_comments (user_id, post_id, text) VALUES (?, ?, ?)",
        (user_id, post_id, text),
    )
    cid = cursor.lastrowid
    conn.commit()
    conn.close()
    return cid


def get_comments(post_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT c.*, u.username, u.display_name, u.avatar_url
           FROM post_comments c
           JOIN users u ON u.id = c.user_id
           WHERE c.post_id = ?
           ORDER BY c.created_at ASC""",
        (post_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_comments(post_id: int) -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as c FROM post_comments WHERE post_id=?", (post_id,)).fetchone()
    conn.close()
    return row["c"] if row else 0


# ---------------------------------------------------------------------------
# Block CRUD
# ---------------------------------------------------------------------------

def block_user(user_id: int, target_id: int) -> bool:
    if user_id == target_id:
        raise ValueError("Cannot block yourself.")
    conn = get_connection()
    conn.execute(
        "INSERT INTO blocks (user_id, target_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (user_id, target_id),
    )
    conn.commit()
    conn.close()
    return True


def unblock_user(user_id: int, target_id: int) -> bool:
    conn = get_connection()
    conn.execute("DELETE FROM blocks WHERE user_id=? AND target_id=?", (user_id, target_id))
    conn.commit()
    conn.close()
    return True


def list_blocked(user_id: int) -> List[int]:
    conn = get_connection()
    rows = conn.execute("SELECT target_id FROM blocks WHERE user_id=?", (user_id,)).fetchall()
    conn.close()
    return [r["target_id"] for r in rows]


# ---------------------------------------------------------------------------
# Page CRUD
# ---------------------------------------------------------------------------

def create_page(user_id: int, title: str, slug: str, content_json: str, is_public: int = 0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pages (user_id, title, slug, content_json, is_public) VALUES (?, ?, ?, ?, ?)",
        (user_id, title, slug, content_json, is_public),
    )
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_page(user_id: int, slug: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM pages WHERE user_id=? AND slug=?", (user_id, slug)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_page(page_id: int, **fields) -> bool:
    allowed = {"title", "content_json", "is_public"}
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        return False
    conn = get_connection()
    set_clause = ", ".join(f"{k} = ?" for k in safe)
    values = list(safe.values()) + [page_id]
    conn.execute(f"UPDATE pages SET {set_clause}, updated_at = datetime('now') WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# Notification CRUD
# ---------------------------------------------------------------------------

def create_notification(user_id: int, type: str, reference_id: int, text: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notifications (user_id, type, reference_id, text) VALUES (?, ?, ?, ?)",
        (user_id, type, reference_id, text),
    )
    nid = cursor.lastrowid
    conn.commit()
    conn.close()
    return nid


def get_unread_notifications(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE user_id=? AND is_read=0 ORDER BY created_at DESC LIMIT 20",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_notification_read(notification_id: int) -> bool:
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,))
    conn.commit()
    conn.close()
    return True
