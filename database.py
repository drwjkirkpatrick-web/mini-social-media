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

    # Events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            location TEXT DEFAULT '',
            start_time TEXT,
            end_time TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_rsvps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status TEXT DEFAULT 'going' CHECK(status IN ('going', 'maybe', 'not_going')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(event_id, user_id)
        )
    """)

    # Polls
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_option_id INTEGER NOT NULL REFERENCES poll_options(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(poll_option_id, user_id)
        )
    """)

    # Circles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS circles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS circle_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            circle_id INTEGER NOT NULL REFERENCES circles(id) ON DELETE CASCADE,
            member_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(circle_id, member_id)
        )
    """)

    # Reactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reaction_type TEXT NOT NULL CHECK(reaction_type IN ('heart', 'laugh', 'wow', 'sad', 'fire')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(post_id, user_id)
        )
    """)

    # Bookmarks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, post_id)
        )
    """)

    # Messages (DMs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Hashtags
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hashtags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_hashtags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            hashtag_id INTEGER NOT NULL REFERENCES hashtags(id) ON DELETE CASCADE,
            UNIQUE(post_id, hashtag_id)
        )
    """)

    # Invite tokens
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invite_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            expires_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Backup codes for 2FA
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backup_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            code_hash TEXT NOT NULL,
            is_used INTEGER DEFAULT 0,
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
        ("has_onboarded", "ALTER TABLE users ADD COLUMN has_onboarded INTEGER DEFAULT 0"),
        ("reset_token", "ALTER TABLE users ADD COLUMN reset_token TEXT"),
        ("reset_expires", "ALTER TABLE users ADD COLUMN reset_expires TEXT"),
        ("totp_secret", "ALTER TABLE users ADD COLUMN totp_secret TEXT"),
        ("theme", "ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'light'"),
        ("accent_color", "ALTER TABLE users ADD COLUMN accent_color TEXT DEFAULT '#4a90d9'"),
        ("is_active", "ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1"),
    ]:
        if col not in existing:
            cursor.execute(ddl)

    cursor.execute("PRAGMA table_info(posts)")
    existing_posts = {r[1] for r in cursor.fetchall()}
    for col, ddl in [
        ("is_draft", "ALTER TABLE posts ADD COLUMN is_draft INTEGER DEFAULT 0"),
        ("is_scheduled", "ALTER TABLE posts ADD COLUMN is_scheduled INTEGER DEFAULT 0"),
        ("scheduled_at", "ALTER TABLE posts ADD COLUMN scheduled_at TEXT"),
        ("is_pinned", "ALTER TABLE posts ADD COLUMN is_pinned INTEGER DEFAULT 0"),
        ("original_post_id", "ALTER TABLE posts ADD COLUMN original_post_id INTEGER"),
        ("share_comment", "ALTER TABLE posts ADD COLUMN share_comment TEXT"),
        ("content_warning", "ALTER TABLE posts ADD COLUMN content_warning TEXT"),
    ]:
        if col not in existing_posts:
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


# ---------------------------------------------------------------------------
# Events CRUD
# ---------------------------------------------------------------------------

def create_event(user_id: int, title: str, description: str = "", location: str = "", start_time: str = None, end_time: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (user_id, title, description, location, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, title, description, location, start_time, end_time),
    )
    eid = cursor.lastrowid
    conn.commit()
    conn.close()
    return eid


def get_event(event_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_events(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM events ORDER BY start_time DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def rsvp_event(event_id: int, user_id: int, status: str = "going") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO event_rsvps (event_id, user_id, status) VALUES (?, ?, ?)
           ON CONFLICT(event_id, user_id) DO UPDATE SET status=excluded.status, created_at=datetime('now')
           RETURNING id""",
        (event_id, user_id, status),
    )
    row = cursor.fetchone()
    rid = row["id"] if row else 0
    conn.commit()
    conn.close()
    return rid


def get_event_rsvps(event_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT er.*, u.username, u.display_name, u.avatar_url
           FROM event_rsvps er
           JOIN users u ON u.id = er.user_id
           WHERE er.event_id = ? ORDER BY er.created_at""",
        (event_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Polls CRUD
# ---------------------------------------------------------------------------

def create_poll(post_id: int, question: str, options: List[str]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO polls (post_id, question) VALUES (?, ?)", (post_id, question))
    poll_id = cursor.lastrowid
    for idx, opt in enumerate(options):
        cursor.execute("INSERT INTO poll_options (poll_id, text, sort_order) VALUES (?, ?, ?)", (poll_id, opt, idx))
    conn.commit()
    conn.close()
    return poll_id


def get_poll(post_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    poll_row = conn.execute("SELECT * FROM polls WHERE post_id=?", (post_id,)).fetchone()
    if not poll_row:
        conn.close()
        return None
    poll = dict(poll_row)
    opt_rows = conn.execute("SELECT * FROM poll_options WHERE poll_id=? ORDER BY sort_order", (poll["id"],)).fetchall()
    poll["options"] = [dict(r) for r in opt_rows]
    for opt in poll["options"]:
        count = conn.execute("SELECT COUNT(*) as c FROM poll_votes WHERE poll_option_id=?", (opt["id"],)).fetchone()
        opt["vote_count"] = count["c"] if count else 0
    conn.close()
    return poll


def vote_poll(poll_option_id: int, user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO poll_votes (poll_option_id, user_id) VALUES (?, ?)", (poll_option_id, user_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def unvote_poll(poll_option_id: int, user_id: int) -> bool:
    conn = get_connection()
    conn.execute("DELETE FROM poll_votes WHERE poll_option_id=? AND user_id=?", (poll_option_id, user_id))
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# Circles CRUD
# ---------------------------------------------------------------------------

def create_circle(user_id: int, name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO circles (user_id, name) VALUES (?, ?)", (user_id, name))
    cid = cursor.lastrowid
    conn.commit()
    conn.close()
    return cid


def add_circle_member(circle_id: int, member_id: int) -> bool:
    conn = get_connection()
    conn.execute("INSERT INTO circle_members (circle_id, member_id) VALUES (?, ?) ON CONFLICT DO NOTHING", (circle_id, member_id))
    conn.commit()
    conn.close()
    return True


def remove_circle_member(circle_id: int, member_id: int) -> bool:
    conn = get_connection()
    conn.execute("DELETE FROM circle_members WHERE circle_id=? AND member_id=?", (circle_id, member_id))
    conn.commit()
    conn.close()
    return True


def list_user_circles(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM circles WHERE user_id=?", (user_id,)).fetchall()
    circles = [dict(r) for r in rows]
    for c in circles:
        mem_rows = conn.execute(
            """SELECT u.id, u.username, u.display_name, u.avatar_url
               FROM circle_members cm JOIN users u ON u.id = cm.member_id
               WHERE cm.circle_id = ?""",
            (c["id"],),
        ).fetchall()
        c["members"] = [dict(r) for r in mem_rows]
    conn.close()
    return circles


def get_circle_members(circle_id: int) -> List[int]:
    conn = get_connection()
    rows = conn.execute("SELECT member_id FROM circle_members WHERE circle_id=?", (circle_id,)).fetchall()
    conn.close()
    return [r["member_id"] for r in rows]


# ---------------------------------------------------------------------------
# Reactions CRUD
# ---------------------------------------------------------------------------

def add_reaction(post_id: int, user_id: int, reaction_type: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    existing = conn.execute("SELECT id, reaction_type FROM reactions WHERE post_id=? AND user_id=?", (post_id, user_id)).fetchone()
    if existing:
        if existing["reaction_type"] == reaction_type:
            cursor.execute("DELETE FROM reactions WHERE id=?", (existing["id"],))
        else:
            cursor.execute("UPDATE reactions SET reaction_type=? WHERE id=?", (reaction_type, existing["id"]))
    else:
        cursor.execute("INSERT INTO reactions (post_id, user_id, reaction_type) VALUES (?, ?, ?)", (post_id, user_id, reaction_type))
    conn.commit()
    conn.close()
    return True


def get_reactions(post_id: int) -> Dict[str, int]:
    conn = get_connection()
    rows = conn.execute("SELECT reaction_type, COUNT(*) as c FROM reactions WHERE post_id=? GROUP BY reaction_type", (post_id,)).fetchall()
    conn.close()
    return {r["reaction_type"]: r["c"] for r in rows}


def get_user_reaction(post_id: int, user_id: int) -> Optional[str]:
    conn = get_connection()
    row = conn.execute("SELECT reaction_type FROM reactions WHERE post_id=? AND user_id=?", (post_id, user_id)).fetchone()
    conn.close()
    return row["reaction_type"] if row else None


# ---------------------------------------------------------------------------
# Bookmarks CRUD
# ---------------------------------------------------------------------------

def toggle_bookmark(user_id: int, post_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    existing = conn.execute("SELECT id FROM bookmarks WHERE user_id=? AND post_id=?", (user_id, post_id)).fetchone()
    if existing:
        cursor.execute("DELETE FROM bookmarks WHERE id=?", (existing["id"],))
        result = False
    else:
        cursor.execute("INSERT INTO bookmarks (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        result = True
    conn.commit()
    conn.close()
    return result


def get_bookmarks(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_url
           FROM bookmarks b
           JOIN posts p ON p.id = b.post_id
           JOIN users u ON u.id = p.user_id
           WHERE b.user_id = ? ORDER BY b.created_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Messages (DMs) CRUD
# ---------------------------------------------------------------------------

def send_message(sender_id: int, recipient_id: int, content: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)",
        (sender_id, recipient_id, content),
    )
    mid = cursor.lastrowid
    conn.commit()
    conn.close()
    return mid


def get_messages_between(user_a: int, user_b: int, limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, s.username as sender_name, s.display_name as sender_display, s.avatar_url as sender_avatar
           FROM messages m
           JOIN users s ON s.id = m.sender_id
           WHERE (m.sender_id=? AND m.recipient_id=?) OR (m.sender_id=? AND m.recipient_id=?)
           ORDER BY m.created_at DESC LIMIT ?""",
        (user_a, user_b, user_b, user_a, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation_list(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    # Get all unique conversation partners
    rows = conn.execute(
        """SELECT DISTINCT sender_id as partner FROM messages WHERE recipient_id=?
           UNION
           SELECT DISTINCT recipient_id as partner FROM messages WHERE sender_id=?""",
        (user_id, user_id),
    ).fetchall()
    partners = [r["partner"] for r in rows]
    conversations = []
    for pid in partners:
        u = conn.execute("SELECT username, display_name, avatar_url FROM users WHERE id=?", (pid,)).fetchone()
        if not u:
            continue
        unread = conn.execute(
            "SELECT COUNT(*) as c FROM messages WHERE recipient_id=? AND sender_id=? AND is_read=0",
            (user_id, pid),
        ).fetchone()["c"]
        conversations.append({
            "other_id": pid,
            "username": u["username"],
            "display_name": u["display_name"],
            "avatar_url": u["avatar_url"],
            "unread_count": unread,
        })
    conn.close()
    return conversations


def mark_messages_read(recipient_id: int, sender_id: int) -> bool:
    conn = get_connection()
    conn.execute("UPDATE messages SET is_read=1 WHERE recipient_id=? AND sender_id=? AND is_read=0", (recipient_id, sender_id))
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# Hashtags CRUD
# ---------------------------------------------------------------------------

def extract_hashtags(text: str) -> List[str]:
    import re
    return list(set(tag.lower() for tag in re.findall(r'#(\w+)', text or '')))


def store_hashtags(post_id: int, text: str) -> None:
    tags = extract_hashtags(text)
    if not tags:
        return
    conn = get_connection()
    for tag in tags:
        conn.execute("INSERT OR IGNORE INTO hashtags (tag) VALUES (?)", (tag,))
        row = conn.execute("SELECT id FROM hashtags WHERE tag=?", (tag,)).fetchone()
        if row:
            conn.execute("INSERT OR IGNORE INTO post_hashtags (post_id, hashtag_id) VALUES (?, ?)", (post_id, row["id"]))
    conn.commit()
    conn.close()


def get_posts_by_hashtag(tag: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_url
           FROM post_hashtags ph
           JOIN hashtags h ON h.id = ph.hashtag_id
           JOIN posts p ON p.id = ph.post_id
           JOIN users u ON u.id = p.user_id
           WHERE h.tag = ? AND p.moderation_status='approved'
           ORDER BY p.created_at DESC LIMIT ? OFFSET ?""",
        (tag.lower(), limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_trending_hashtags(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT h.tag, COUNT(*) as count
           FROM post_hashtags ph
           JOIN hashtags h ON h.id = ph.hashtag_id
           JOIN posts p ON p.id = ph.post_id
           WHERE p.created_at > datetime('now', '-7 days')
           GROUP BY h.tag ORDER BY count DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Invite Tokens CRUD
# ---------------------------------------------------------------------------

def create_invite_token(created_by: int, max_uses: int = 1, expires_hours: int = 168) -> str:
    import secrets
    from datetime import datetime, timezone, timedelta
    token = secrets.token_urlsafe(16)
    expires = (datetime.now(timezone.utc) + timedelta(hours=expires_hours)).isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO invite_tokens (token, created_by, max_uses, expires_at) VALUES (?, ?, ?, ?)",
        (token, created_by, max_uses, expires),
    )
    conn.commit()
    conn.close()
    return token


def validate_invite_token(token: str) -> bool:
    from datetime import datetime, timezone
    conn = get_connection()
    row = conn.execute("SELECT * FROM invite_tokens WHERE token=?", (token,)).fetchone()
    if not row:
        conn.close()
        return False
    if row["used_count"] >= row["max_uses"]:
        conn.close()
        return False
    if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        conn.close()
        return False
    conn.execute("UPDATE invite_tokens SET used_count = used_count + 1 WHERE id=?", (row["id"],))
    conn.commit()
    conn.close()
    return True


def list_invite_tokens(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM invite_tokens WHERE created_by=? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Backup Codes CRUD
# ---------------------------------------------------------------------------

def create_backup_codes(user_id: int, codes: List[str]) -> None:
    from werkzeug.security import generate_password_hash
    conn = get_connection()
    conn.execute("DELETE FROM backup_codes WHERE user_id=?", (user_id,))
    for code in codes:
        conn.execute(
            "INSERT INTO backup_codes (user_id, code_hash) VALUES (?, ?)",
            (user_id, generate_password_hash(code)),
        )
    conn.commit()
    conn.close()


def verify_backup_code(user_id: int, code: str) -> bool:
    from werkzeug.security import check_password_hash
    conn = get_connection()
    rows = conn.execute("SELECT * FROM backup_codes WHERE user_id=? AND is_used=0", (user_id,)).fetchall()
    for row in rows:
        if check_password_hash(row["code_hash"], code):
            conn.execute("UPDATE backup_codes SET is_used=1 WHERE id=?", (row["id"],))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False
