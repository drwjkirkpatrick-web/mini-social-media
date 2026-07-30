"""
mini-social-media database layer.
NOTE: Uses sqlite3.Row for dict-like row access.
WHY: Dict-like access makes template rendering and JSON serialization easier.
"""

import sqlite3
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set

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
            content_type TEXT NOT NULL,
            text_content TEXT,
            link_url TEXT,
            photo_url TEXT,
            video_url TEXT,
            video_thumb_url TEXT,
            voice_url TEXT,
            photo_urls TEXT,
            template_type TEXT,
            template_data TEXT,
            visibility TEXT DEFAULT 'friends' CHECK(visibility IN ('friends', 'only_me')),
            moderation_status TEXT DEFAULT 'pending' CHECK(moderation_status IN ('pending', 'approved', 'rejected')),
            is_draft INTEGER DEFAULT 0,
            is_scheduled INTEGER DEFAULT 0,
            scheduled_at TEXT,
            is_pinned INTEGER DEFAULT 0,
            original_post_id INTEGER,
            share_comment TEXT,
            content_warning TEXT,
            expires_at TEXT,
            view_count INTEGER DEFAULT 0,
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
            reaction_type TEXT NOT NULL,
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
            group_id INTEGER,
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
        ("birthday_month", "ALTER TABLE users ADD COLUMN birthday_month INTEGER"),
        ("birthday_day", "ALTER TABLE users ADD COLUMN birthday_day INTEGER"),
        ("mood", "ALTER TABLE users ADD COLUMN mood TEXT"),
        ("location_lat", "ALTER TABLE users ADD COLUMN location_lat REAL"),
        ("location_lng", "ALTER TABLE users ADD COLUMN location_lng REAL"),
        ("location_general", "ALTER TABLE users ADD COLUMN location_general TEXT"),
        ("location_precision", "ALTER TABLE users ADD COLUMN location_precision TEXT DEFAULT 'hidden'"),
        ("selfie_url", "ALTER TABLE users ADD COLUMN selfie_url TEXT"),
        ("pattern", "ALTER TABLE users ADD COLUMN pattern TEXT DEFAULT 'none'"),
        ("high_contrast", "ALTER TABLE users ADD COLUMN high_contrast INTEGER DEFAULT 0"),
        ("font_size", "ALTER TABLE users ADD COLUMN font_size INTEGER DEFAULT 16"),
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
        ("video_url", "ALTER TABLE posts ADD COLUMN video_url TEXT"),
        ("video_thumb_url", "ALTER TABLE posts ADD COLUMN video_thumb_url TEXT"),
        ("voice_url", "ALTER TABLE posts ADD COLUMN voice_url TEXT"),
        ("photo_urls", "ALTER TABLE posts ADD COLUMN photo_urls TEXT"),
        ("template_type", "ALTER TABLE posts ADD COLUMN template_type TEXT"),
        ("template_data", "ALTER TABLE posts ADD COLUMN template_data TEXT"),
        ("expires_at", "ALTER TABLE posts ADD COLUMN expires_at TEXT"),
        ("view_count", "ALTER TABLE posts ADD COLUMN view_count INTEGER DEFAULT 0"),
        ("is_local_news", "ALTER TABLE posts ADD COLUMN is_local_news INTEGER DEFAULT 0"),
        ("filter_id", "ALTER TABLE posts ADD COLUMN filter_id INTEGER"),
    ]:
        if col not in existing_posts:
            cursor.execute(ddl)

    # v0.8.0: Meme Filters
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meme_filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            css_filters TEXT NOT NULL DEFAULT '{}',
            overlay_svg TEXT,
            created_by INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # Seed built-in meme filters if empty
    mf_count = cursor.execute("SELECT COUNT(*) as c FROM meme_filters").fetchone()
    if mf_count and mf_count["c"] == 0:
        built_in = [
            ("Vaporwave", "Retro neon aesthetic", '{"brightness":"1.2","contrast":"1.1","saturate":"1.5","hue-rotate":"180deg","sepia":"0.2"}', '', 0),
            ("Deep Fry", "High contrast crunchy look", '{"brightness":"1.4","contrast":"2.0","saturate":"2.0"}', '', 0),
            ("Black & White", "Classic monochrome", '{"grayscale":"1"}', '', 0),
            ("Sepia Vintage", "Old photo warmth", '{"sepia":"0.8","contrast":"0.9","brightness":"1.1"}', '', 0),
            ("Neon Glow", "Electric edge glow", '{"brightness":"1.2","contrast":"1.3","saturate":"2.0"}', '<svg xmlns="http://www.w3.org/2000/svg"><filter id="neon"><feGaussianBlur stdDeviation="3"/></filter></svg>', 0),
            ("Pixelate", "Low-res retro", '{"contrast":"1.2"}', '', 0),
            ("Blur Background", "Dreamy softness", '{"blur":"4px","brightness":"1.1"}', '', 0),
            ("Comic Book", "Bold halftone pop", '{"contrast":"1.5","saturate":"1.3"}', '', 0),
        ]
        cursor.executemany(
            "INSERT INTO meme_filters (name, description, css_filters, overlay_svg, created_by) VALUES (?, ?, ?, ?, ?)",
            built_in
        )

    # v0.4.0: Stories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            text_content TEXT,
            photo_url TEXT,
            video_url TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            view_count INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS story_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            viewer_id INTEGER NOT NULL,
            viewed_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(story_id, viewer_id)
        )
    """)
    # v0.4.0: Daily Prompts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_text TEXT NOT NULL,
            prompt_date TEXT UNIQUE NOT NULL,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.4.0: Reading List
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reading_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            url TEXT NOT NULL,
            notes TEXT,
            is_public INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.4.0: Wishlist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            item_link TEXT,
            price TEXT,
            priority INTEGER DEFAULT 1,
            claimed_by INTEGER,
            is_claimed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.4.0: Notes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            circle_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS note_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            edited_by INTEGER,
            edited_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.4.0: Message Groups
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            is_admin INTEGER DEFAULT 0,
            joined_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(group_id, user_id)
        )
    """)
    # v0.4.0: Hermes Prompts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hermes_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            prompt_type TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            actionable_link TEXT,
            is_dismissed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.4.0: Ice Breakers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ice_breakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.4.0: Friend-versaries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS friend_versaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            friendship_id INTEGER NOT NULL,
            anniversary_date TEXT NOT NULL,
            years INTEGER DEFAULT 1,
            notified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.4.0: Albums
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            cover_photo_url TEXT,
            is_public INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS album_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id INTEGER NOT NULL,
            photo_url TEXT NOT NULL,
            caption TEXT,
            sort_order INTEGER DEFAULT 0,
            exif_data TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # Seed ice breakers if empty
    existing = cursor.execute("SELECT COUNT(*) as c FROM ice_breakers").fetchone()
    if existing and existing["c"] == 0:
        questions = [
            ("What's your favorite childhood memory?", "general"),
            ("If you could learn any skill instantly, what would it be?", "general"),
            ("What's the best meal you've ever had?", "food"),
            ("What's a book that changed your perspective?", "reading"),
            ("If you could visit any place in the world, where would you go?", "travel"),
            ("What's something you're proud of but never get to talk about?", "deep"),
            ("What's your favorite way to spend a rainy day?", "lifestyle"),
            ("What's a hobby you've always wanted to try?", "hobbies"),
            ("What's the most interesting thing you learned recently?", "learning"),
            ("If you had to eat one cuisine for the rest of your life, what would it be?", "food"),
        ]
        cursor.executemany("INSERT INTO ice_breakers (question, category) VALUES (?, ?)", questions)

    # Migrate messages table: add group_id if missing
    cursor.execute("PRAGMA table_info(messages)")
    msg_cols = {r[1] for r in cursor.fetchall()}
    if "group_id" not in msg_cols:
        cursor.execute("ALTER TABLE messages ADD COLUMN group_id INTEGER")

    # v0.5.0: Profile bio
    cursor.execute("PRAGMA table_info(users)")
    user_cols = {r[1] for r in cursor.fetchall()}
    for col, ddl in [
        ("bio", "ALTER TABLE users ADD COLUMN bio TEXT"),
        ("accepted_guidelines_at", "ALTER TABLE users ADD COLUMN accepted_guidelines_at TEXT"),
        ("current_streak", "ALTER TABLE users ADD COLUMN current_streak INTEGER DEFAULT 0"),
        ("longest_streak", "ALTER TABLE users ADD COLUMN longest_streak INTEGER DEFAULT 0"),
        ("last_post_date", "ALTER TABLE users ADD COLUMN last_post_date TEXT"),
    ]:
        if col not in user_cols:
            cursor.execute(ddl)

    # v0.5.0: Achievements
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT,
            category TEXT DEFAULT 'general',
            threshold INTEGER DEFAULT 1
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL,
            unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
            is_seen INTEGER DEFAULT 0,
            UNIQUE(user_id, achievement_id)
        )
    """)
    # v0.5.0: User activity (daily post counts for graph)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_date TEXT NOT NULL,
            post_count INTEGER DEFAULT 0,
            UNIQUE(user_id, activity_date)
        )
    """)
    # v0.5.0: Backups log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size_bytes INTEGER,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.5.0: Post series (grouped posts like chapters)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            sort_order INTEGER DEFAULT 0,
            UNIQUE(series_id, post_id)
        )
    """)
    # v0.6.0: Moderation Lists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mod_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            list_type TEXT NOT NULL DEFAULT 'block' CHECK(list_type IN ('block','mute')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mod_list_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mod_list_id INTEGER NOT NULL REFERENCES mod_lists(id) ON DELETE CASCADE,
            target_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            added_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(mod_list_id, target_user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mod_list_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            mod_list_id INTEGER NOT NULL REFERENCES mod_lists(id) ON DELETE CASCADE,
            subscribed_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, mod_list_id)
        )
    """)
    # v0.6.0: Content Labels
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            label_type TEXT NOT NULL CHECK(label_type IN ('sensitive','nsfw','spoiler','violence','political','ai_generated')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_label_prefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            label_type TEXT NOT NULL,
            action TEXT NOT NULL DEFAULT 'warn' CHECK(action IN ('show','warn','hide')),
            UNIQUE(user_id, label_type)
        )
    """)
    # v0.6.0: Muted Words
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS muted_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            word TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, word)
        )
    """)
    # v0.6.0: Custom Feeds
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            filter_type TEXT NOT NULL DEFAULT 'hashtag',
            filter_value TEXT NOT NULL,
            is_pinned INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # v0.6.0: Post reply controls (who can reply to a post)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_reply_controls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            reply_scope TEXT NOT NULL DEFAULT 'friends' CHECK(reply_scope IN ('everyone','friends','mentioned','nobody')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(post_id)
        )
    """)
    # Mutes (private — unlike blocks which are public)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, target_id)
        )
    """)
    # v0.6.0: Starter Packs (curated lists of users to follow)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS starter_packs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS starter_pack_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id INTEGER NOT NULL REFERENCES starter_packs(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            sort_order INTEGER DEFAULT 0,
            UNIQUE(pack_id, user_id)
        )
    """)
    # Seed achievements if empty
    ach_count = cursor.execute("SELECT COUNT(*) as c FROM achievements").fetchone()
    if ach_count and ach_count["c"] == 0:
        achievements = [
            ("first_steps", "First Steps", "Create your first post.", "🌱", "milestone", 1),
            ("social_butterfly", "Social Butterfly", "Accept 10 friend requests.", "🦋", "connection", 10),
            ("deep_connector", "Deep Connector", "Send 50 direct messages.", "💬", "connection", 50),
            ("healthy_habit", "Healthy Habit", "Post on 7 consecutive days.", "🌿", "wellness", 7),
            ("digital_detox", "Digital Detox Champion", "Take a 3+ day break, then return and post.", "🧘", "wellness", 1),
            ("community_builder", "Community Builder", "Create an event with 5+ RSVPs.", "🏘️", "connection", 1),
            ("thoughtful_responder", "Thoughtful Responder", "Comment on 20 different friends' posts.", "💭", "wellness", 20),
            ("memory_keeper", "Memory Keeper", "Create 3 photo albums.", "📸", "milestone", 3),
            ("storyteller", "Storyteller", "Publish 10 ephemeral stories.", "📖", "milestone", 10),
            ("poll_master", "Poll Master", "Create 5 polls receiving 10+ votes each.", "📊", "milestone", 5),
            ("helper", "Helper", "Answer 10 daily prompts or ice breakers.", "🤝", "wellness", 10),
            ("verified_human", "Verified Human", "Complete your profile.", "✅", "milestone", 1),
            ("long_term_friend", "Long-Term Friend", "Reach a 1-year friend-versary.", "🤝", "connection", 1),
        ]
        cursor.executemany(
            "INSERT INTO achievements (slug, name, description, icon, category, threshold) VALUES (?, ?, ?, ?, ?, ?)",
            achievements
        )

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
    allowed = {"display_name", "bio", "avatar_url", "cover_url", "pronouns", "location", "location_lat", "location_lng", "location_general", "location_precision", "selfie_url", "theme", "pattern", "high_contrast", "font_size"}
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


# ---------------------------------------------------------------------------
# v0.4.0: Stories
# ---------------------------------------------------------------------------

def create_story(user_id: int, content_type: str, text_content: str = None, photo_url: str = None, video_url: str = None) -> int:
    from datetime import datetime, timezone, timedelta
    expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO stories (user_id, content_type, text_content, photo_url, video_url, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, content_type, text_content, photo_url, video_url, expires),
    )
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_active_stories(user_id: int) -> List[Dict[str, Any]]:
    """Get active stories from friends of user_id."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, u.username, u.display_name, u.avatar_url
           FROM stories s
           JOIN users u ON u.id = s.user_id
           WHERE s.expires_at > ?
             AND s.user_id IN (
                 SELECT CASE WHEN requester_id = ? THEN addressee_id ELSE requester_id END
                 FROM friendships WHERE status = 'accepted' AND (requester_id = ? OR addressee_id = ?)
             )
           ORDER BY s.created_at DESC""",
        (now, user_id, user_id, user_id),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def view_story(story_id: int, viewer_id: int) -> bool:
    conn = get_connection()
    conn.execute(
        "INSERT INTO story_views (story_id, viewer_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (story_id, viewer_id),
    )
    conn.execute("UPDATE stories SET view_count = view_count + 1 WHERE id = ?", (story_id,))
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# v0.4.0: Daily Prompts
# ---------------------------------------------------------------------------

def get_daily_prompt(date_str: str = None) -> Optional[Dict[str, Any]]:
    if date_str is None:
        from datetime import datetime, timezone
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = get_connection()
    row = conn.execute("SELECT * FROM daily_prompts WHERE prompt_date = ?", (date_str,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_daily_prompt(prompt_text: str, created_by: int) -> int:
    from datetime import datetime, timezone
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO daily_prompts (prompt_text, prompt_date, created_by) VALUES (?, ?, ?) ON CONFLICT(prompt_date) DO UPDATE SET prompt_text=excluded.prompt_text",
        (prompt_text, date_str, created_by),
    )
    conn.commit()
    pid = cursor.lastrowid or conn.execute("SELECT id FROM daily_prompts WHERE prompt_date = ?", (date_str,)).fetchone()["id"]
    conn.close()
    return pid


# ---------------------------------------------------------------------------
# v0.4.0: Ice Breakers
# ---------------------------------------------------------------------------

def get_random_ice_breaker(category: str = None) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    if category:
        row = conn.execute(
            "SELECT * FROM ice_breakers WHERE category = ? ORDER BY RANDOM() LIMIT 1", (category,)
        ).fetchone()
    else:
        row = conn.execute("SELECT * FROM ice_breakers ORDER BY RANDOM() LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# v0.4.0: Albums (Photographer Tools)
# ---------------------------------------------------------------------------

def create_album(user_id: int, title: str, description: str = "", cover_photo_url: str = None, is_public: bool = False) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO albums (user_id, title, description, cover_photo_url, is_public) VALUES (?, ?, ?, ?, ?)",
        (user_id, title, description, cover_photo_url, int(is_public)),
    )
    aid = cursor.lastrowid
    conn.commit()
    conn.close()
    return aid


def get_album(album_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM albums WHERE id = ?", (album_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_user_albums(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM albums WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_photo_to_album(album_id: int, photo_url: str, caption: str = "", sort_order: int = 0, exif_data: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO album_photos (album_id, photo_url, caption, sort_order, exif_data) VALUES (?, ?, ?, ?, ?)",
        (album_id, photo_url, caption, sort_order, exif_data),
    )
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_album_photos(album_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM album_photos WHERE album_id = ? ORDER BY sort_order, created_at",
        (album_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v0.4.0: Reading List
# ---------------------------------------------------------------------------

def add_to_reading_list(user_id: int, url: str, title: str = "", notes: str = "", is_public: bool = False) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reading_list (user_id, url, title, notes, is_public) VALUES (?, ?, ?, ?, ?)",
        (user_id, url, title, notes, int(is_public)),
    )
    rid = cursor.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_reading_list(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reading_list WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v0.4.0: Wishlist / Gift Registry
# ---------------------------------------------------------------------------

def add_wishlist_item(user_id: int, item_name: str, item_link: str = "", price: str = "", priority: int = 1) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO wishlist (user_id, item_name, item_link, price, priority) VALUES (?, ?, ?, ?, ?)",
        (user_id, item_name, item_link, price, priority),
    )
    wid = cursor.lastrowid
    conn.commit()
    conn.close()
    return wid


def get_wishlist(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM wishlist WHERE user_id = ? ORDER BY priority DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def claim_wishlist_item(item_id: int, claimed_by: int) -> bool:
    conn = get_connection()
    conn.execute(
        "UPDATE wishlist SET claimed_by = ?, is_claimed = 1 WHERE id = ? AND is_claimed = 0",
        (claimed_by, item_id),
    )
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# v0.4.0: Collaborative Notes
# ---------------------------------------------------------------------------

def create_note(user_id: int, title: str, content: str, circle_id: int = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notes (user_id, title, content, circle_id) VALUES (?, ?, ?, ?)",
        (user_id, title, content, circle_id),
    )
    nid = cursor.lastrowid
    conn.commit()
    conn.close()
    return nid


def get_note(note_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_note(note_id: int, content: str, edited_by: int) -> bool:
    conn = get_connection()
    note = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not note:
        conn.close()
        return False
    # Save to history
    conn.execute(
        "INSERT INTO note_history (note_id, content, edited_by) VALUES (?, ?, ?)",
        (note_id, note["content"], edited_by),
    )
    # Update note
    new_version = (note["version"] or 0) + 1
    conn.execute(
        "UPDATE notes SET content = ?, version = ?, updated_at = datetime('now') WHERE id = ?",
        (content, new_version, note_id),
    )
    conn.commit()
    conn.close()
    return True


def list_notes(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT n.* FROM notes n
           LEFT JOIN circle_members cm ON cm.circle_id = n.circle_id
           WHERE n.user_id = ? OR cm.member_id = ?
           GROUP BY n.id
           ORDER BY n.updated_at DESC""",
        (user_id, user_id),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v0.4.0: Message Groups (multi-person DMs)
# ---------------------------------------------------------------------------

def create_message_group(name: str, created_by: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO message_groups (name, created_by) VALUES (?, ?)",
        (name, created_by),
    )
    gid = cursor.lastrowid
    # Creator is admin
    conn.execute("INSERT INTO group_members (group_id, user_id, is_admin) VALUES (?, ?, 1)", (gid, created_by))
    conn.commit()
    conn.close()
    return gid


def add_to_group(group_id: int, user_id: int) -> bool:
    conn = get_connection()
    conn.execute(
        "INSERT INTO group_members (group_id, user_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (group_id, user_id),
    )
    conn.commit()
    conn.close()
    return True


def get_group_messages(group_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, u.username, u.display_name, u.avatar_url
           FROM messages m
           JOIN users u ON u.id = m.sender_id
           WHERE m.group_id = ?
           ORDER BY m.created_at DESC
           LIMIT ?""",
        (group_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def send_group_message(sender_id: int, group_id: int, content: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    # recipient_id set to sender_id for group messages (FK constraint workaround)
    cursor.execute(
        "INSERT INTO messages (sender_id, group_id, content, recipient_id) VALUES (?, ?, ?, ?)",
        (sender_id, group_id, content, sender_id),
    )
    mid = cursor.lastrowid
    conn.commit()
    conn.close()
    return mid


# ---------------------------------------------------------------------------
# v0.4.0: Hermes Prompts (Connection Encouragement)
# ---------------------------------------------------------------------------

def create_hermes_prompt(user_id: int, prompt_type: str, prompt_text: str, actionable_link: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO hermes_prompts (user_id, prompt_type, prompt_text, actionable_link) VALUES (?, ?, ?, ?)",
        (user_id, prompt_type, prompt_text, actionable_link),
    )
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_hermes_prompts(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM hermes_prompts WHERE user_id = ? AND is_dismissed = 0 ORDER BY created_at DESC LIMIT 10",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def dismiss_hermes_prompt(prompt_id: int) -> bool:
    conn = get_connection()
    conn.execute("UPDATE hermes_prompts SET is_dismissed = 1 WHERE id = ?", (prompt_id,))
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# v0.4.0: Birthday / Friend-versary
# ---------------------------------------------------------------------------

def get_upcoming_birthdays(user_id: int, days_ahead: int = 7) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT u.id, u.username, u.display_name, u.avatar_url, u.birthday_month, u.birthday_day,
                  f.id as friendship_id
           FROM users u
           JOIN friendships f ON (
               (f.requester_id = ? AND f.addressee_id = u.id)
               OR (f.addressee_id = ? AND f.requester_id = u.id)
           )
           WHERE f.status = 'accepted'
             AND u.birthday_month IS NOT NULL
             AND u.birthday_day IS NOT NULL
             AND (
                 strftime('%m-%d', printf('2000-%02d-%02d', u.birthday_month, u.birthday_day))
                 BETWEEN strftime('%m-%d', 'now')
                 AND strftime('%m-%d', 'now', '+' || ? || ' days')
             )
           ORDER BY u.birthday_month, u.birthday_day""",
        (user_id, user_id, days_ahead),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v0.5.0: Achievements + Streaks + Activity
# ---------------------------------------------------------------------------

def get_achievements() -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM achievements ORDER BY category, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_achievements(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT a.*, ua.unlocked_at, ua.is_seen
           FROM achievements a
           JOIN user_achievements ua ON ua.achievement_id = a.id
           WHERE ua.user_id = ?
           ORDER BY ua.unlocked_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def award_achievement(user_id: int, slug: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    ach = conn.execute("SELECT id FROM achievements WHERE slug = ?", (slug,)).fetchone()
    if not ach:
        conn.close()
        return False
    existing = conn.execute(
        "SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?",
        (user_id, ach["id"]),
    ).fetchone()
    if existing:
        conn.close()
        return False
    cursor.execute(
        "INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)",
        (user_id, ach["id"]),
    )
    conn.commit()
    conn.close()
    return True


def check_and_award_achievements(user_id: int) -> List[str]:
    """Check all achievement conditions and award any newly earned."""
    conn = get_connection()
    awarded = []
    # First Steps
    post_count = conn.execute("SELECT COUNT(*) as c FROM posts WHERE user_id = ?", (user_id,)).fetchone()["c"]
    if post_count >= 1:
        if award_achievement(user_id, "first_steps"):
            awarded.append("first_steps")
    # Social Butterfly
    friend_count = conn.execute(
        "SELECT COUNT(*) as c FROM friendships WHERE status = 'accepted' AND (requester_id = ? OR addressee_id = ?)",
        (user_id, user_id),
    ).fetchone()["c"]
    if friend_count >= 10:
        if award_achievement(user_id, "social_butterfly"):
            awarded.append("social_butterfly")
    # Deep Connector
    dm_count = conn.execute(
        "SELECT COUNT(*) as c FROM messages WHERE sender_id = ?", (user_id,)
    ).fetchone()["c"]
    if dm_count >= 50:
        if award_achievement(user_id, "deep_connector"):
            awarded.append("deep_connector")
    # Memory Keeper
    album_count = conn.execute("SELECT COUNT(*) as c FROM albums WHERE user_id = ?", (user_id,)).fetchone()["c"]
    if album_count >= 3:
        if award_achievement(user_id, "memory_keeper"):
            awarded.append("memory_keeper")
    # Storyteller
    story_count = conn.execute("SELECT COUNT(*) as c FROM stories WHERE user_id = ?", (user_id,)).fetchone()["c"]
    if story_count >= 10:
        if award_achievement(user_id, "storyteller"):
            awarded.append("storyteller")
    # Verified Human
    user = conn.execute(
        "SELECT has_onboarded, bio, avatar_url, birthday_month, birthday_day FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if user and user["has_onboarded"] and user["bio"] and user["avatar_url"] and user["birthday_month"]:
        if award_achievement(user_id, "verified_human"):
            awarded.append("verified_human")
    conn.close()
    return awarded


def record_user_activity(user_id: int, date_str: str = None) -> None:
    """Increment post count for a given date."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    existing = conn.execute(
        "SELECT id, post_count FROM user_activity WHERE user_id = ? AND activity_date = ?",
        (user_id, date_str),
    ).fetchone()
    if existing:
        cursor.execute(
            "UPDATE user_activity SET post_count = ? WHERE id = ?",
            (existing["post_count"] + 1, existing["id"]),
        )
    else:
        cursor.execute(
            "INSERT INTO user_activity (user_id, activity_date, post_count) VALUES (?, ?, 1)",
            (user_id, date_str),
        )
    conn.commit()
    conn.close()


def get_user_activity(user_id: int, days: int = 365) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM user_activity WHERE user_id = ? AND activity_date >= date('now', '-' || ? || ' days') ORDER BY activity_date",
        (user_id, days),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_streak(user_id: int) -> None:
    """Update posting streak based on last_post_date."""
    conn = get_connection()
    user = conn.execute(
        "SELECT last_post_date, current_streak, longest_streak FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if not user:
        conn.close()
        return
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last = user["last_post_date"]
    current = user["current_streak"] or 0
    longest = user["longest_streak"] or 0
    if last == today:
        conn.close()
        return
    yesterday = (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=1)).strftime("%Y-%m-%d")
    if last == yesterday:
        current += 1
    else:
        current = 1
    if current > longest:
        longest = current
    conn.execute(
        "UPDATE users SET current_streak = ?, longest_streak = ?, last_post_date = ? WHERE id = ?",
        (current, longest, today, user_id),
    )
    conn.commit()
    conn.close()
    # Award healthy habit if streak >= 7
    if current >= 7:
        award_achievement(user_id, "healthy_habit")


# ---------------------------------------------------------------------------
# v0.5.0: Backups
# ---------------------------------------------------------------------------

def log_backup(filename: str, size_bytes: int, created_by: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO backups (filename, size_bytes, created_by) VALUES (?, ?, ?)",
        (filename, size_bytes, created_by),
    )
    bid = cursor.lastrowid
    conn.commit()
    conn.close()
    return bid


def list_backups(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM backups ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v0.5.0: Post Series
# ---------------------------------------------------------------------------

def create_series(user_id: int, title: str, description: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO post_series (user_id, title, description) VALUES (?, ?, ?)",
        (user_id, title, description),
    )
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid


def add_post_to_series(series_id: int, post_id: int, sort_order: int = 0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO series_posts (series_id, post_id, sort_order) VALUES (?, ?, ?)",
        (series_id, post_id, sort_order),
    )
    spid = cursor.lastrowid
    conn.commit()
    conn.close()
    return spid


def get_series_posts(series_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_url, sp.sort_order
           FROM posts p
           JOIN series_posts sp ON sp.post_id = p.id
           JOIN users u ON u.id = p.user_id
           WHERE sp.series_id = ?
           ORDER BY sp.sort_order, p.created_at""",
        (series_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v0.6.0: Content Labels
# ---------------------------------------------------------------------------

VALID_LABEL_TYPES = ('sensitive', 'nsfw', 'spoiler', 'violence', 'political', 'ai_generated')


def add_post_label(post_id: int, label_type: str) -> int:
    """Attach a content label to a post. Returns the label row id."""
    if label_type not in VALID_LABEL_TYPES:
        raise ValueError(f"Invalid label type: {label_type}")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO post_labels (post_id, label_type) VALUES (?, ?)",
        (post_id, label_type),
    )
    label_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return label_id


def get_post_labels(post_id: int) -> List[Dict[str, Any]]:
    """Return all labels attached to a post."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM post_labels WHERE post_id = ? ORDER BY created_at",
        (post_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_label_prefs(user_id: int) -> Dict[str, str]:
    """Return {label_type: action} for the user's label preferences."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT label_type, action FROM user_label_prefs WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return {r["label_type"]: r["action"] for r in rows}


def set_user_label_pref(user_id: int, label_type: str, action: str) -> int:
    """Insert or update a user's preference for a label type. Returns the pref row id."""
    if label_type not in VALID_LABEL_TYPES:
        raise ValueError(f"Invalid label type: {label_type}")
    if action not in ('show', 'warn', 'hide'):
        raise ValueError(f"Invalid action: {action}")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO user_label_prefs (user_id, label_type, action)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id, label_type) DO UPDATE SET action = excluded.action""",
        (user_id, label_type, action),
    )
    pref_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pref_id


def get_visible_posts_with_labels(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Return approved, non-draft, non-scheduled posts filtered by the user's label prefs.

    Posts that carry a label the user has set to 'hide' are excluded. The post's
    labels are attached as a 'labels' list on each returned post dict.
    """
    conn = get_connection()
    # Label types the user wants hidden
    hidden_types = [
        r["label_type"]
        for r in conn.execute(
            "SELECT label_type FROM user_label_prefs WHERE user_id = ? AND action = 'hide'",
            (user_id,),
        ).fetchall()
    ]
    if hidden_types:
        placeholders = ",".join("?" for _ in hidden_types)
        query = f"""
            SELECT p.*, u.username, u.display_name, u.avatar_url
            FROM posts p
            JOIN users u ON u.id = p.user_id
            WHERE p.moderation_status = 'approved'
              AND p.is_draft = 0
              AND p.is_scheduled = 0
              AND p.id NOT IN (
                  SELECT post_id FROM post_labels WHERE label_type IN ({placeholders})
              )
            ORDER BY p.created_at DESC
            LIMIT ?
        """
        rows = conn.execute(query, hidden_types + [limit]).fetchall()
    else:
        rows = conn.execute(
            """SELECT p.*, u.username, u.display_name, u.avatar_url
               FROM posts p
               JOIN users u ON u.id = p.user_id
               WHERE p.moderation_status = 'approved'
                 AND p.is_draft = 0
                 AND p.is_scheduled = 0
               ORDER BY p.created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
    posts = [dict(r) for r in rows]
    # Attach labels to each post
    for post in posts:
        label_rows = conn.execute(
            "SELECT label_type FROM post_labels WHERE post_id = ?", (post["id"],)
        ).fetchall()
        post["labels"] = [r["label_type"] for r in label_rows]
    conn.close()
    return posts


# ---------------------------------------------------------------------------
# v0.6.0: Moderation Lists CRUD
# ---------------------------------------------------------------------------

def create_mod_list(user_id: int, name: str, description: str = "", list_type: str = "block") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mod_lists (user_id, name, description, list_type) VALUES (?, ?, ?, ?)",
        (user_id, name, description, list_type),
    )
    lid = cursor.lastrowid
    conn.commit()
    conn.close()
    return lid


def get_mod_list(list_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute(
        """SELECT ml.*, u.username, u.display_name, u.avatar_url,
                  (SELECT COUNT(*) FROM mod_list_members m WHERE m.mod_list_id = ml.id) AS member_count
           FROM mod_lists ml
           JOIN users u ON u.id = ml.user_id
           WHERE ml.id = ?""",
        (list_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_mod_lists(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT ml.*, u.username, u.display_name, u.avatar_url,
                  (SELECT COUNT(*) FROM mod_list_members m WHERE m.mod_list_id = ml.id) AS member_count
           FROM mod_lists ml
           JOIN users u ON u.id = ml.user_id
           ORDER BY ml.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_my_mod_lists(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT ml.*,
                  (SELECT COUNT(*) FROM mod_list_members m WHERE m.mod_list_id = ml.id) AS member_count
           FROM mod_lists ml
           WHERE ml.user_id = ?
           ORDER BY ml.created_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_to_mod_list(list_id: int, target_user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mod_list_members (mod_list_id, target_user_id) VALUES (?, ?)",
        (list_id, target_user_id),
    )
    mid = cursor.lastrowid
    conn.commit()
    conn.close()
    return mid


def remove_from_mod_list(list_id: int, target_user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM mod_list_members WHERE mod_list_id = ? AND target_user_id = ?",
        (list_id, target_user_id),
    )
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def get_mod_list_members(list_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, u.username, u.display_name, u.avatar_url
           FROM mod_list_members m
           JOIN users u ON u.id = m.target_user_id
           WHERE m.mod_list_id = ?
           ORDER BY m.added_at DESC""",
        (list_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def subscribe_mod_list(user_id: int, list_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mod_list_subscriptions (user_id, mod_list_id) VALUES (?, ?)",
        (user_id, list_id),
    )
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid


def unsubscribe_mod_list(user_id: int, list_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM mod_list_subscriptions WHERE user_id = ? AND mod_list_id = ?",
        (user_id, list_id),
    )
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def get_subscribed_mod_lists(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, ml.name, ml.description, ml.list_type,
                  u.username AS owner_username, u.display_name AS owner_display_name,
                  (SELECT COUNT(*) FROM mod_list_members m WHERE m.mod_list_id = ml.id) AS member_count
           FROM mod_list_subscriptions s
           JOIN mod_lists ml ON ml.id = s.mod_list_id
           JOIN users u ON u.id = ml.user_id
           WHERE s.user_id = ?
           ORDER BY s.subscribed_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_muted_from_subscribed(user_id: int) -> List[int]:
    """Return target user IDs from all mute-type lists the user has subscribed to."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT DISTINCT m.target_user_id
           FROM mod_list_subscriptions s
           JOIN mod_lists ml ON ml.id = s.mod_list_id
           JOIN mod_list_members m ON m.mod_list_id = ml.id
           WHERE s.user_id = ? AND ml.list_type = 'mute'""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [r["target_user_id"] for r in rows]


def get_all_blocked_from_subscribed(user_id: int) -> List[int]:
    """Return target user IDs from all block-type lists the user has subscribed to."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT DISTINCT m.target_user_id
           FROM mod_list_subscriptions s
           JOIN mod_lists ml ON ml.id = s.mod_list_id
           JOIN mod_list_members m ON m.mod_list_id = ml.id
           WHERE s.user_id = ? AND ml.list_type = 'block'""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [r["target_user_id"] for r in rows]


# ---------------------------------------------------------------------------
# v0.6.0: Custom Feeds
# ---------------------------------------------------------------------------

VALID_FILTER_TYPES = ('hashtag', 'user', 'keyword', 'photos')


def create_custom_feed(user_id: int, name: str, filter_type: str, filter_value: str) -> int:
    """Create a custom feed. Returns the new feed id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO custom_feeds (user_id, name, filter_type, filter_value) VALUES (?, ?, ?, ?)",
        (user_id, name, filter_type, filter_value),
    )
    feed_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return feed_id


def list_custom_feeds(user_id: int) -> List[Dict[str, Any]]:
    """Return all custom feeds for a user, pinned first then newest."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM custom_feeds
           WHERE user_id = ?
           ORDER BY is_pinned DESC, created_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_custom_feed(feed_id: int) -> Optional[Dict[str, Any]]:
    """Return a single custom feed by id, or None."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM custom_feeds WHERE id = ?", (feed_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_custom_feed(feed_id: int, user_id: int) -> bool:
    """Delete a custom feed owned by user_id. Returns True if a row was removed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM custom_feeds WHERE id = ? AND user_id = ?",
        (feed_id, user_id),
    )
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def toggle_pin_custom_feed(feed_id: int, user_id: int) -> bool:
    """Toggle the pinned state of a feed owned by user_id.

    Returns True if the feed is now pinned, False if now unpinned, or None
    (falsy) if the feed was not found / not owned by the user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT is_pinned FROM custom_feeds WHERE id = ? AND user_id = ?",
        (feed_id, user_id),
    ).fetchone()
    if not row:
        conn.close()
        return False
    new_state = 0 if row["is_pinned"] else 1
    cursor.execute(
        "UPDATE custom_feeds SET is_pinned = ? WHERE id = ?",
        (new_state, feed_id),
    )
    conn.commit()
    conn.close()
    return bool(new_state)


def get_custom_feed_posts(feed_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Return posts matching a custom feed's filter.

    filter_type determines the join/where:
      - 'hashtag': posts tagged with the hashtag in filter_value
      - 'user':    posts by the user whose username matches filter_value
      - 'keyword': approved posts whose text_content contains filter_value
      - 'photos': approved posts that have a photo_url or photo_urls
    All queries return only approved, non-draft, non-scheduled posts, newest first.
    """
    feed = get_custom_feed(feed_id)
    if not feed:
        return []
    ftype = feed["filter_type"]
    fval = feed["filter_value"]
    conn = get_connection()
    if ftype == 'hashtag':
        rows = conn.execute(
            """SELECT p.*, u.username, u.display_name, u.avatar_url
               FROM post_hashtags ph
               JOIN hashtags h ON h.id = ph.hashtag_id
               JOIN posts p ON p.id = ph.post_id
               JOIN users u ON u.id = p.user_id
               WHERE h.tag = ? AND p.moderation_status = 'approved'
                 AND p.is_draft = 0 AND p.is_scheduled = 0
               ORDER BY p.created_at DESC LIMIT ?""",
            (fval.lower(), limit),
        ).fetchall()
    elif ftype == 'user':
        rows = conn.execute(
            """SELECT p.*, u.username, u.display_name, u.avatar_url
               FROM posts p
               JOIN users u ON u.id = p.user_id
               WHERE u.username = ? AND p.moderation_status = 'approved'
                 AND p.is_draft = 0 AND p.is_scheduled = 0
               ORDER BY p.created_at DESC LIMIT ?""",
            (fval, limit),
        ).fetchall()
    elif ftype == 'keyword':
        rows = conn.execute(
            """SELECT p.*, u.username, u.display_name, u.avatar_url
               FROM posts p
               JOIN users u ON u.id = p.user_id
               WHERE p.text_content LIKE ? AND p.moderation_status = 'approved'
                 AND p.is_draft = 0 AND p.is_scheduled = 0
               ORDER BY p.created_at DESC LIMIT ?""",
            (f"%{fval}%", limit),
        ).fetchall()
    elif ftype == 'photos':
        rows = conn.execute(
            """SELECT p.*, u.username, u.display_name, u.avatar_url
               FROM posts p
               JOIN users u ON u.id = p.user_id
               WHERE p.moderation_status = 'approved'
                 AND p.is_draft = 0 AND p.is_scheduled = 0
                 AND (p.photo_url IS NOT NULL AND p.photo_url != ''
                      OR p.photo_urls IS NOT NULL AND p.photo_urls != '')
               ORDER BY p.created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    else:
        rows = []
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v0.6.0: Muted Words CRUD
# ---------------------------------------------------------------------------

def add_muted_word(user_id: int, word: str) -> int:
    """Add a muted word for the user. Returns the row id.

    NOTE: Words are stored as-is (original case) but matching is case-insensitive.
    Duplicate (user_id, word) pairs are ignored via ON CONFLICT.
    """
    word = word.strip()
    if not word:
        raise ValueError("Word cannot be empty.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO muted_words (user_id, word) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (user_id, word),
    )
    wid = cursor.lastrowid
    conn.commit()
    conn.close()
    return wid


def remove_muted_word(user_id: int, word: str) -> bool:
    """Remove a muted word for the user. Returns True if a row was deleted."""
    word = word.strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM muted_words WHERE user_id = ? AND word = ?",
        (user_id, word),
    )
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def list_muted_words(user_id: int) -> List[Dict[str, Any]]:
    """Return all muted word rows for a user, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM muted_words WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_muted_word_list(user_id: int) -> List[str]:
    """Return just the list of muted word strings for a user (for filtering)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT word FROM muted_words WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [r["word"] for r in rows]


def is_word_muted(user_id: int, text: str) -> bool:
    """Check if any of the user's muted words appears in text (case-insensitive).

    NOTE: Substring matching — a muted word matches if it appears anywhere in
    the text, regardless of surrounding characters.
    """
    if not text:
        return False
    words = get_muted_word_list(user_id)
    if not words:
        return False
    lowered = text.lower()
    return any(w.lower() in lowered for w in words)


# ---------------------------------------------------------------------------
# Mute Accounts CRUD (private — unlike blocks which are public)
# ---------------------------------------------------------------------------

def mute_user(user_id: int, target_id: int) -> int:
    """Mute a user. Returns the mute row id.

    NOTE: Mutes are private — the muted user is not notified. Duplicate
    (user_id, target_id) pairs are ignored via ON CONFLICT.
    """
    if user_id == target_id:
        raise ValueError("Cannot mute yourself.")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mutes (user_id, target_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (user_id, target_id),
    )
    mid = cursor.lastrowid
    conn.commit()
    conn.close()
    return mid


def unmute_user(user_id: int, target_id: int) -> bool:
    """Unmute a user. Returns True if a row was deleted."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM mutes WHERE user_id = ? AND target_id = ?",
        (user_id, target_id),
    )
    removed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return removed


def is_muted(user_id: int, target_id: int) -> bool:
    """Check if user_id has muted target_id."""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM mutes WHERE user_id = ? AND target_id = ?",
        (user_id, target_id),
    ).fetchone()
    conn.close()
    return row is not None


def list_muted(user_id: int) -> List[Dict[str, Any]]:
    """Return muted user rows for a user, newest first.

    Joins users so the template has username/display_name/avatar_url.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.id, m.target_id, m.created_at,
                  u.username, u.display_name, u.avatar_url
           FROM mutes m
           JOIN users u ON u.id = m.target_id
           WHERE m.user_id = ?
           ORDER BY m.created_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_muted_ids(user_id: int) -> Set[int]:
    """Return the set of muted user IDs for efficient feed filtering."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT target_id FROM mutes WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return {r["target_id"] for r in rows}


# ---------------------------------------------------------------------------
# v0.6.0: Reply Controls
# ---------------------------------------------------------------------------

def set_reply_control(post_id: int, reply_scope: str) -> int:
    """Set the reply scope for a post. Returns the row id.

    reply_scope must be one of: 'everyone', 'friends', 'mentioned', 'nobody'.
    Uses INSERT ... ON CONFLICT to upsert (one row per post via UNIQUE(post_id)).
    """
    if reply_scope not in ("everyone", "friends", "mentioned", "nobody"):
        raise ValueError(f"Invalid reply_scope: {reply_scope}")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO post_reply_controls (post_id, reply_scope)
           VALUES (?, ?)
           ON CONFLICT(post_id) DO UPDATE SET reply_scope=excluded.reply_scope""",
        (post_id, reply_scope),
    )
    rcid = cursor.lastrowid
    conn.commit()
    conn.close()
    return rcid


def get_reply_control(post_id: int) -> Optional[str]:
    """Return the reply_scope for a post, or 'friends' if none is set (default)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT reply_scope FROM post_reply_controls WHERE post_id = ?",
        (post_id,),
    ).fetchone()
    conn.close()
    if row:
        return row["reply_scope"]
    return "friends"


def can_reply(post_id: int, user_id: int, is_friend: bool, is_mentioned: bool) -> bool:
    """Check whether a user may reply (comment) on a post.

    - 'everyone'  → always True
    - 'friends'   → True if is_friend
    - 'mentioned' → True if is_mentioned
    - 'nobody'    → always False
    """
    scope = get_reply_control(post_id)
    if scope == "everyone":
        return True
    if scope == "friends":
        return bool(is_friend)
    if scope == "mentioned":
        return bool(is_mentioned)
    if scope == "nobody":
        return False
    return True 


# ---------------------------------------------------------------------------
# v0.6.0: Starter Packs
# ---------------------------------------------------------------------------

def create_starter_pack(user_id: int, name: str, description: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO starter_packs (user_id, name, description) VALUES (?, ?, ?)",
        (user_id, name, description),
    )
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_starter_pack(pack_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM starter_packs WHERE id = ?", (pack_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_starter_packs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT sp.*, u.username, u.display_name,
                  (SELECT COUNT(*) FROM starter_pack_members m WHERE m.pack_id = sp.id) AS member_count
           FROM starter_packs sp
           JOIN users u ON u.id = sp.user_id
           ORDER BY sp.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_to_starter_pack(pack_id: int, user_id: int, sort_order: int = 0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO starter_pack_members (pack_id, user_id, sort_order) VALUES (?, ?, ?)",
        (pack_id, user_id, sort_order),
    )
    mid = cursor.lastrowid
    conn.commit()
    conn.close()
    return mid


def remove_from_starter_pack(pack_id: int, user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM starter_pack_members WHERE pack_id = ? AND user_id = ?",
        (pack_id, user_id),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_starter_pack_members(pack_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT m.*, u.username, u.display_name, u.avatar_url
           FROM starter_pack_members m
           JOIN users u ON u.id = m.user_id
           WHERE m.pack_id = ?
           ORDER BY m.sort_order, u.username""",
        (pack_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def follow_all_in_pack(follower_id: int, pack_id: int) -> int:
    """Send friend requests to all pack members who aren't already friends.

    Returns the count of new friend requests created.
    """
    members = get_starter_pack_members(pack_id)
    count = 0
    for member in members:
        target_id = member["user_id"]
        if target_id == follower_id:
            continue
        friendship = get_friendship(follower_id, target_id)
        if friendship:
            # Already friends or request already pending/rejected
            continue
        send_friend_request(follower_id, target_id)
        create_notification(
            target_id, "friend_request", 0,
            f"You have a new friend request from a starter pack.",
        )
        count += 1
    return count


# ---------------------------------------------------------------------------
# Meme Filters (v0.8.0)
# ---------------------------------------------------------------------------

def create_meme_filter(name: str, description: str, css_filters: str, overlay_svg: str, created_by: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO meme_filters (name, description, css_filters, overlay_svg, created_by) VALUES (?, ?, ?, ?, ?)",
        (name, description, css_filters, overlay_svg, created_by),
    )
    fid = cursor.lastrowid
    conn.commit()
    conn.close()
    return fid


def get_meme_filter(filter_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM meme_filters WHERE id = ?", (filter_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_meme_filters() -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM meme_filters ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_user_meme_filters(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM meme_filters WHERE created_by = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Meme Posts (v0.8.0)
# ---------------------------------------------------------------------------

def create_meme_post(user_id: int, photo_url: str, filter_id: int, text_content: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (user_id, content_type, photo_url, filter_id, text_content, visibility) VALUES (?, 'meme', ?, ?, ?, 'friends')",
        (user_id, photo_url, filter_id, text_content),
    )
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_meme_posts_by_friends(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Return meme posts from accepted friends, ordered newest first."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_url,
                  mf.name as filter_name, mf.css_filters
           FROM posts p
           JOIN users u ON u.id = p.user_id
           LEFT JOIN meme_filters mf ON mf.id = p.filter_id
           WHERE p.content_type = 'meme'
             AND p.user_id IN (
                 SELECT requester_id FROM friendships WHERE addressee_id = ? AND status = 'accepted'
                 UNION
                 SELECT addressee_id FROM friendships WHERE requester_id = ? AND status = 'accepted'
             )
           ORDER BY p.created_at DESC
           LIMIT ?""",
        (user_id, user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Local News / Fun (v0.8.0)
# ---------------------------------------------------------------------------

def get_local_news_posts(viewer_id: int, location_general: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return local-news posts from friends+fof in same general location."""
    conn = get_connection()
    # Friends and friends-of-friends whose location_general matches (case-insensitive)
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_url
           FROM posts p
           JOIN users u ON u.id = p.user_id
           WHERE p.is_local_news = 1
             AND p.moderation_status = 'approved'
             AND (
                 -- direct friends
                 p.user_id IN (
                     SELECT requester_id FROM friendships WHERE addressee_id = ? AND status = 'accepted'
                     UNION
                     SELECT addressee_id FROM friendships WHERE requester_id = ? AND status = 'accepted'
                 )
                 -- or friends-of-friends with matching location
                 OR (
                     p.user_id IN (
                         SELECT f1.requester_id FROM friendships f1
                         JOIN friendships f2 ON (
                             (f2.requester_id = f1.addressee_id OR f2.addressee_id = f1.addressee_id)
                             AND f2.status = 'accepted'
                         )
                         WHERE f1.status = 'accepted' AND (f1.requester_id = ? OR f1.addressee_id = ?)
                     )
                     AND LOWER(u.location_general) = LOWER(?)
                 )
             )
           ORDER BY p.created_at DESC
           LIMIT ?""",
        (viewer_id, viewer_id, viewer_id, viewer_id, location_general, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_local_fun_posts(location_general: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return posts tagged #localfun or #thingstodo."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT DISTINCT p.*, u.username, u.display_name, u.avatar_url
           FROM posts p
           JOIN users u ON u.id = p.user_id
           JOIN post_hashtags ph ON ph.post_id = p.id
           JOIN hashtags h ON h.id = ph.hashtag_id
           WHERE p.moderation_status = 'approved'
             AND (LOWER(h.tag) IN ('localfun','thingstodo'))
             AND (u.location_general IS NOT NULL)
           ORDER BY p.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Location-based friends (v0.8.0)
# ---------------------------------------------------------------------------

def list_friends_by_location(user_id: int, location_general: str) -> List[Dict[str, Any]]:
    """Return accepted friends who share the same general location."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT u.id, u.username, u.display_name, u.avatar_url, u.location_general
           FROM friendships f
           JOIN users u ON (
               (u.id = f.requester_id AND f.addressee_id = ?)
               OR (u.id = f.addressee_id AND f.requester_id = ?)
           )
           WHERE f.status = 'accepted'
             AND LOWER(u.location_general) = LOWER(?)
             AND u.id != ?""",
        (user_id, user_id, location_general, user_id),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_friends_nearby(user_id: int, location_general: str) -> int:
    conn = get_connection()
    row = conn.execute(
        """SELECT COUNT(*) AS c
           FROM friendships f
           JOIN users u ON (
               (u.id = f.requester_id AND f.addressee_id = ?)
               OR (u.id = f.addressee_id AND f.requester_id = ?)
           )
           WHERE f.status = 'accepted'
             AND LOWER(u.location_general) = LOWER(?)
             AND u.id != ?""",
        (user_id, user_id, location_general, user_id),
    ).fetchone()
    conn.close()
    return row["c"] if row else 0


# ---------------------------------------------------------------------------
# Local events fuzzy match (v0.8.0)
# ---------------------------------------------------------------------------

def list_events_by_location(location_general: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return events whose location text contains the user's location_general word(s)."""
    conn = get_connection()
    # Simple fuzzy: any word in location_general appears in event.location
    words = [w.strip() for w in location_general.replace(",", " ").split() if len(w.strip()) > 2]
    if not words:
        conn.close()
        return []
    clauses = " OR ".join(["LOWER(e.location) LIKE ?"] * len(words))
    params = [f"%{w.lower()}%" for w in words] + [limit]
    rows = conn.execute(
        f"""SELECT e.*, u.username, u.display_name,
                  (SELECT COUNT(*) FROM event_rsvps er WHERE er.event_id = e.id) AS rsvp_count
           FROM events e
           JOIN users u ON u.id = e.user_id
           WHERE ({clauses})
           ORDER BY e.start_time ASC
           LIMIT ?""",
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Deterministic pseudo-weather (v0.8.0)
# ---------------------------------------------------------------------------
import hashlib

def get_local_weather(location_general: str, date_str: str = None) -> dict:
    """Return deterministic pseudo-weather based on location hash + day-of-year.
    No external API calls — purely local computation.
    """
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_of_year = datetime.strptime(date_str, "%Y-%m-%d").timetuple().tm_yday
    h = hashlib.md5(f"{location_general.lower().strip()}:{date_str}".encode()).hexdigest()
    conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Rainy", "Snowy", "Clear"]
    condition = conditions[int(h[:2], 16) % len(conditions)]
    # Temperature range: 45-85 F with seasonal swing
    base_temp = 55 + (int(h[2:4], 16) % 30)
    seasonal_offset = int(10 * (1 if day_of_year < 60 or day_of_year > 300 else -1) * (abs(day_of_year - 180) / 180))
    low = base_temp + seasonal_offset - 5
    high = base_temp + seasonal_offset + 8
    return {
        "condition": condition,
        "low": low,
        "high": high,
        "location": location_general,
        "date": date_str,
    }
