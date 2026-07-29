"""
mini-social-media — privacy-first friends-only social media platform.
NOTE: Built for ~100 users. Local-first. No data leaves the server.
WHY: Small communities deserve privacy without surveillance capitalism.
"""

import os
import json
import re
from datetime import datetime, timezone
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, abort, jsonify, send_from_directory,
)
from flask_socketio import SocketIO, emit, join_room, leave_room

# Local modules
import database
import blockchain
from config import get_config
from auth import hash_password, verify_password, login_required, admin_required, check_rate_limit
from uploads import save_photo, allowed_file
from moderation import moderate_text, status_from_score
from feed import get_feed

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.config["SECRET_KEY"] = get_config().secret_key
app.config["MAX_CONTENT_LENGTH"] = get_config().max_file_size_mb * 1024 * 1024

# SocketIO — async_mode='threading' avoids eventlet/gevent dependency
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# Ensure DB exists before first request
@app.before_request
def _ensure_db():
    database.init_database()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _current_user() -> dict:
    uid = session.get("user_id")
    return database.get_user(uid) if uid else None


@app.context_processor
def inject_globals():
    cfg = get_config()
    return {
        "current_user": _current_user(),
        "site_logo_url": cfg.site_logo_url,
        "site_motto": cfg.site_motto,
    }


def _slugify(text: str) -> str:
    return re.sub(r"[^\w-]+", "-", text.lower()).strip("-")


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Wave 1: Deep Social Interaction Routes
# ---------------------------------------------------------------------------

@app.route("/events")
@login_required
def events():
    me = _current_user()
    evs = database.list_events(limit=50)
    return render_template("events.html", events=evs)


@app.route("/event/new", methods=["GET", "POST"])
@login_required
def new_event():
    user = _current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        start_time = request.form.get("start_time", "").strip()
        end_time = request.form.get("end_time", "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("new_event.html"), 400
        eid = database.create_event(user["id"], title, description, location, start_time or None, end_time or None)
        flash("Event created!", "success")
        return redirect(url_for("event_detail", event_id=eid))
    return render_template("new_event.html")


@app.route("/event/<int:event_id>")
@login_required
def event_detail(event_id):
    event = database.get_event(event_id)
    if not event:
        abort(404)
    rsvps = database.get_event_rsvps(event_id)
    return render_template("event_detail.html", event=event, rsvps=rsvps)


@app.route("/event/<int:event_id>/rsvp", methods=["POST"])
@login_required
def event_rsvp(event_id):
    me = _current_user()
    status = request.form.get("status", "going")
    database.rsvp_event(event_id, me["id"], status)
    flash("RSVP updated.", "success")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/bookmarks")
@login_required
def bookmarks():
    me = _current_user()
    posts = database.get_bookmarks(me["id"])
    return render_template("bookmarks.html", posts=posts)


@app.route("/post/<int:post_id>/bookmark", methods=["POST"])
@login_required
def toggle_bookmark(post_id):
    me = _current_user()
    added = database.toggle_bookmark(me["id"], post_id)
    flash("Saved!" if added else "Removed.", "success")
    return redirect(url_for("feed"))


@app.route("/post/<int:post_id>/react", methods=["POST"])
@login_required
def react_to_post(post_id):
    me = _current_user()
    reaction = request.form.get("reaction", "heart")
    database.add_reaction(post_id, me["id"], reaction)
    return redirect(url_for("feed"))


@app.route("/messages")
@login_required
def messages():
    me = _current_user()
    conversations = database.get_conversation_list(me["id"])
    return render_template("messages.html", conversations=conversations)


@app.route("/messages/<int:user_id>", methods=["GET", "POST"])
@login_required
def message_thread(user_id):
    me = _current_user()
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            # Enforce friends-only DMs
            friendship = database.get_friendship(me["id"], user_id)
            blocked = database.list_blocked(user_id)
            if me["id"] in blocked:
                flash("You have been blocked.", "error")
                return redirect(url_for("message_thread", user_id=user_id))
            if not (friendship and friendship["status"] == "accepted"):
                flash("You can only message friends.", "error")
                return redirect(url_for("message_thread", user_id=user_id))
            database.send_message(me["id"], user_id, content)
        return redirect(url_for("message_thread", user_id=user_id))
    msgs = database.get_messages_between(me["id"], user_id)
    database.mark_messages_read(me["id"], user_id)
    other = database.get_user(user_id)
    return render_template("message_thread.html", messages=msgs, other=other)


@app.route("/notifications")
@login_required
def notifications():
    me = _current_user()
    notes = database.get_unread_notifications(me["id"])
    # Also get read ones for context
    conn = database.get_connection()
    all_notes = conn.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
        (me["id"],),
    ).fetchall()
    conn.close()
    return render_template("notifications.html", notifications=[dict(r) for r in all_notes])


@app.route("/notifications/<int:note_id>/read", methods=["POST"])
@login_required
def mark_notification_read_route(note_id):
    database.mark_notification_read(note_id)
    return redirect(url_for("notifications"))


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    tab = request.args.get("tab", "posts")
    users = []
    posts = []
    pages = []
    if q:
        conn = database.get_connection()
        if tab == "users":
            rows = conn.execute(
                "SELECT id, username, display_name, avatar_url FROM users WHERE (username LIKE ? OR display_name LIKE ?) AND is_active=1 LIMIT 20",
                (f"%{q}%", f"%{q}%"),
            ).fetchall()
            users = [dict(r) for r in rows]
        elif tab == "posts":
            rows = conn.execute(
                """SELECT p.*, u.username, u.display_name, u.avatar_url
                   FROM posts p JOIN users u ON u.id = p.user_id
                   WHERE p.text_content LIKE ? AND p.moderation_status='approved' AND p.is_draft=0 AND p.is_scheduled=0
                   ORDER BY p.created_at DESC LIMIT 20""",
                (f"%{q}%",),
            ).fetchall()
            posts = [dict(r) for r in rows]
        elif tab == "pages":
            rows = conn.execute(
                "SELECT * FROM pages WHERE title LIKE ? AND is_public=1 LIMIT 20",
                (f"%{q}%",),
            ).fetchall()
            pages = [dict(r) for r in rows]
        conn.close()
    return render_template("search.html", q=q, tab=tab, users=users, posts=posts, pages=pages)


@app.route("/tag/<tag>")
def tag_posts(tag):
    posts = database.get_posts_by_hashtag(tag, limit=50)
    return render_template("tag.html", tag=tag, posts=posts)


@app.route("/discover")
@login_required
def discover():
    conn = database.get_connection()
    # Recently joined users
    rows = conn.execute(
        "SELECT id, username, display_name, avatar_url, bio, created_at FROM users WHERE is_active=1 ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    new_users = [dict(r) for r in rows]
    # Suggested: users with mutual friends
    me = _current_user()
    my_friends = database.list_friends(me["id"])
    my_friend_ids = {f["id"] for f in my_friends}
    suggestions = []
    if my_friend_ids:
        placeholders = ",".join("?" for _ in my_friend_ids)
        rows = conn.execute(
            f"""SELECT DISTINCT u.id, u.username, u.display_name, u.avatar_url,
                       (SELECT COUNT(*) FROM friendships f2 WHERE f2.status='accepted'
                        AND ((f2.requester_id=u.id AND f2.addressee_id IN ({placeholders}))
                             OR (f2.addressee_id=u.id AND f2.requester_id IN ({placeholders})))) as mutuals
               FROM friendships f1
               JOIN users u ON (u.id = f1.requester_id OR u.id = f1.addressee_id)
               WHERE u.id != ? AND u.is_active=1
                 AND (f1.requester_id IN ({placeholders}) OR f1.addressee_id IN ({placeholders}))
                 AND u.id NOT IN ({placeholders})
               ORDER BY mutuals DESC
               LIMIT 10""",
            list(my_friend_ids) + [me["id"]] + list(my_friend_ids)*3,
        ).fetchall()
        suggestions = [dict(r) for r in rows]
    conn.close()
    return render_template("discover.html", new_users=new_users, suggestions=suggestions)


@app.route("/mutual/<int:user_id>")
@login_required
def mutual_friends(user_id):
    me = _current_user()
    my_friends = database.list_friends(me["id"])
    their_friends = database.list_friends(user_id)
    my_ids = {f["id"] for f in my_friends}
    their_ids = {f["id"] for f in their_friends}
    mutual = my_ids & their_ids
    conn = database.get_connection()
    users = []
    if mutual:
        placeholders = ",".join("?" for _ in mutual)
        rows = conn.execute(
            f"SELECT id, username, display_name, avatar_url FROM users WHERE id IN ({placeholders})",
            list(mutual),
        ).fetchall()
        users = [dict(r) for r in rows]
    conn.close()
    return render_template("mutual.html", users=users, count=len(users))


# ---------------------------------------------------------------------------
# Wave 2: Polish, Onboarding & Power Features
# ---------------------------------------------------------------------------

@app.route("/welcome")
@login_required
def welcome():
    user = _current_user()
    if user.get("has_onboarded"):
        return redirect(url_for("feed"))
    return render_template("welcome.html", step=int(request.args.get("step", 1)))


@app.route("/welcome", methods=["POST"])
@login_required
def welcome_post():
    user = _current_user()
    step = int(request.form.get("step", 1))
    if step == 1:
        # Avatar upload
        if "avatar" in request.files:
            file = request.files["avatar"]
            if file and file.filename and allowed_file(file.filename):
                try:
                    url = save_photo(file, user["id"])
                    database.update_user(user["id"], avatar_url=url)
                except ValueError:
                    pass
    elif step == 2:
        bio = request.form.get("bio", "").strip()
        if bio:
            database.update_user(user["id"], bio=bio)
    elif step == 3:
        pass  # Friend discovery shown as page
    elif step == 4:
        pass  # First post prompt
    if step >= 4:
        conn = database.get_connection()
        conn.execute("UPDATE users SET has_onboarded=1 WHERE id=?", (user["id"],))
        conn.commit()
        conn.close()
        flash("Welcome aboard! Your profile is ready.", "success")
        return redirect(url_for("feed"))
    return redirect(url_for("welcome", step=step + 1))


@app.route("/help")
def help_center():
    return render_template("help.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = database.get_user_by_email(email)
        if user:
            import secrets
            from datetime import datetime, timezone, timedelta
            token = secrets.token_urlsafe(24)
            expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            conn = database.get_connection()
            conn.execute("UPDATE users SET reset_token=?, reset_expires=? WHERE id=?", (token, expires, user["id"]))
            conn.commit()
            conn.close()
            # In production, send email. For demo, show token on screen.
            flash(f"Reset token (demo only): {token}", "success")
        else:
            flash("If that email exists, a reset link was sent.", "info")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = database.get_connection()
    row = conn.execute("SELECT * FROM users WHERE reset_token=?", (token,)).fetchone()
    if not row:
        conn.close()
        flash("Invalid or expired token.", "error")
        return redirect(url_for("login"))
    from datetime import datetime, timezone
    if row["reset_expires"] and datetime.fromisoformat(row["reset_expires"]) < datetime.now(timezone.utc):
        conn.close()
        flash("Token expired.", "error")
        return redirect(url_for("login"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("reset_password.html", token=token)
        conn.execute("UPDATE users SET password_hash=?, reset_token=NULL, reset_expires=NULL WHERE id=?",
                     (hash_password(password), row["id"]))
        conn.commit()
        conn.close()
        flash("Password reset successfully!", "success")
        return redirect(url_for("login"))
    conn.close()
    return render_template("reset_password.html", token=token)


@app.route("/settings/theme", methods=["POST"])
@login_required
def save_theme():
    user = _current_user()
    theme = request.form.get("theme", "light")
    accent = request.form.get("accent_color", "#4a90d9")
    conn = database.get_connection()
    conn.execute("UPDATE users SET theme=?, accent_color=? WHERE id=?", (theme, accent, user["id"]))
    conn.commit()
    conn.close()
    flash("Theme saved!", "success")
    return redirect(url_for("profile"))


@app.route("/settings/export")
@login_required
def export_data():
    import json
    user = _current_user()
    conn = database.get_connection()
    data = {
        "user": dict(conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()),
        "posts": [dict(r) for r in conn.execute("SELECT * FROM posts WHERE user_id=?", (user["id"],)).fetchall()],
        "likes": [dict(r) for r in conn.execute("SELECT * FROM post_likes WHERE user_id=?", (user["id"],)).fetchall()],
        "comments": [dict(r) for r in conn.execute("SELECT * FROM post_comments WHERE user_id=?", (user["id"],)).fetchall()],
        "friends": [dict(r) for r in conn.execute("""
            SELECT * FROM friendships WHERE requester_id=? OR addressee_id=?""", (user["id"], user["id"])).fetchall()],
        "bookmarks": [dict(r) for r in conn.execute("SELECT * FROM bookmarks WHERE user_id=?", (user["id"],)).fetchall()],
        "messages": [dict(r) for r in conn.execute(
            "SELECT * FROM messages WHERE sender_id=? OR recipient_id=?", (user["id"], user["id"])).fetchall()],
    }
    conn.close()
    response = jsonify(data)
    response.headers["Content-Disposition"] = f'attachment; filename="export_{user["username"]}.json"'
    return response


@app.route("/settings/deactivate", methods=["POST"])
@login_required
def deactivate_account():
    user = _current_user()
    conn = database.get_connection()
    conn.execute("UPDATE users SET is_active=0, username='deleted_user_' || id, display_name='[deleted user]', bio='', avatar_url=NULL, cover_url=NULL WHERE id=?", (user["id"],))
    conn.execute("UPDATE posts SET text_content='[deleted]', link_url=NULL, photo_url=NULL, text_content='[deleted]' WHERE user_id=?", (user["id"],))
    conn.commit()
    conn.close()
    session.clear()
    flash("Account deactivated.", "info")
    return redirect(url_for("login"))


@app.route("/post/<int:post_id>/pin", methods=["POST"])
@login_required
def pin_post(post_id):
    user = _current_user()
    conn = database.get_connection()
    # Unpin any existing pinned post by this user
    conn.execute("UPDATE posts SET is_pinned=0 WHERE user_id=? AND is_pinned=1", (user["id"],))
    conn.execute("UPDATE posts SET is_pinned=1 WHERE id=? AND user_id=?", (post_id, user["id"]))
    conn.commit()
    conn.close()
    flash("Post pinned to your profile.", "success")
    return redirect(url_for("profile"))


@app.route("/post/<int:post_id>/share", methods=["POST"])
@login_required
def share_post(post_id):
    user = _current_user()
    comment = request.form.get("share_comment", "").strip()
    original = database.get_post(post_id)
    if not original:
        abort(404)
    pid = database.create_post(
        user["id"], original["content_type"],
        text_content=original["text_content"],
        link_url=original["link_url"],
        photo_url=original["photo_url"],
    )
    conn = database.get_connection()
    conn.execute("UPDATE posts SET original_post_id=?, share_comment=? WHERE id=?", (post_id, comment, pid))
    conn.commit()
    conn.close()
    database.create_notification(original["user_id"], "share", pid, f"{user['display_name'] or user['username']} shared your post.")
    flash("Post shared!", "success")
    return redirect(url_for("feed"))


@app.route("/drafts")
@login_required
def drafts():
    user = _current_user()
    conn = database.get_connection()
    rows = conn.execute(
        """SELECT * FROM posts WHERE user_id=? AND is_draft=1 ORDER BY updated_at DESC""",
        (user["id"],),
    ).fetchall()
    conn.close()
    return render_template("drafts.html", posts=[dict(r) for r in rows])


@app.route("/post/<int:post_id>/stats")
@login_required
def post_stats(post_id):
    post = database.get_post(post_id)
    user = _current_user()
    if not post or post["user_id"] != user["id"]:
        abort(403)
    reactions = database.get_reactions(post_id)
    likes = database.count_likes(post_id)
    comments = database.count_comments(post_id)
    conn = database.get_connection()
    shares = conn.execute("SELECT COUNT(*) as c FROM posts WHERE original_post_id=?", (post_id,)).fetchone()["c"]
    views = conn.execute("SELECT COUNT(*) as c FROM audit_log WHERE table_name='posts' AND record_id=? AND action='view'", (post_id,)).fetchone()["c"]
    conn.close()
    return render_template("post_stats.html", post=post, reactions=reactions, likes=likes, comments=comments, shares=shares, views=views)


@app.route("/circles")
@login_required
def circles():
    user = _current_user()
    circles = database.list_user_circles(user["id"])
    friends = database.list_friends(user["id"])
    return render_template("circles.html", circles=circles, friends=friends)


@app.route("/circle/new", methods=["POST"])
@login_required
def new_circle():
    user = _current_user()
    name = request.form.get("name", "").strip()
    if not name:
        flash("Circle name required.", "error")
        return redirect(url_for("circles"))
    cid = database.create_circle(user["id"], name)
    # Add selected members
    for mid in request.form.getlist("members"):
        database.add_circle_member(cid, int(mid))
    flash("Circle created!", "success")
    return redirect(url_for("circles"))


@app.route("/post/<int:original_id>/repost", methods=["POST"])
@login_required
def repost(original_id):
    return share_post(original_id)


# ---------------------------------------------------------------------------
# Wave 3: Content Warnings, Settings, Onboarding Helpers
# ---------------------------------------------------------------------------

@app.route("/mentions")
@login_required
def mentions():
    me = _current_user()
    conn = database.get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name, u.avatar_url
           FROM posts p
           JOIN users u ON u.id = p.user_id
           WHERE p.text_content LIKE ? AND p.moderation_status='approved'
           ORDER BY p.created_at DESC LIMIT 50""",
        (f"%@{me['username']}%",),
    ).fetchall()
    conn.close()
    return render_template("mentions.html", posts=[dict(r) for r in rows])


@app.route("/activity")
@login_required
def activity_log():
    user = _current_user()
    conn = database.get_connection()
    posts = [dict(r) for r in conn.execute(
        "SELECT * FROM posts WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (user["id"],)).fetchall()]
    likes = [dict(r) for r in conn.execute(
        """SELECT pl.*, p.text_content, p.content_type
           FROM post_likes pl JOIN posts p ON p.id = pl.post_id
           WHERE pl.user_id=? ORDER BY pl.created_at DESC LIMIT 10""", (user["id"],)).fetchall()]
    comments = [dict(r) for r in conn.execute(
        """SELECT pc.*, p.text_content, p.content_type
           FROM post_comments pc JOIN posts p ON p.id = pc.post_id
           WHERE pc.user_id=? ORDER BY pc.created_at DESC LIMIT 10""", (user["id"],)).fetchall()]
    conn.close()
    return render_template("activity.html", posts=posts, likes=likes, comments=comments)


@app.route("/settings")
@login_required
def settings():
    user = _current_user()
    invites = database.list_invite_tokens(user["id"])
    return render_template("settings.html", user=user, invites=invites)


@app.route("/settings/invite", methods=["POST"])
@login_required
def create_invite():
    user = _current_user()
    max_uses = int(request.form.get("max_uses", 1))
    token = database.create_invite_token(user["id"], max_uses)
    flash(f"Invite link created: /signup?invite={token}", "success")
    return redirect(url_for("settings"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    # Check for invite token
    invite_token = request.args.get("invite") or request.form.get("invite", "")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        display_name = request.form.get("display_name", "").strip()

        errors = []
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", username):
            errors.append("Username: 3-30 alphanumeric/underscore characters.")
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != password2:
            errors.append("Passwords do not match.")
        if database.get_user_by_username(username):
            errors.append("Username already taken.")
        if database.get_user_by_email(email):
            errors.append("Email already registered.")

        # Validate invite token if provided
        if invite_token and not database.validate_invite_token(invite_token):
            errors.append("Invalid or expired invite token.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("signup.html", username=username, email=email, display_name=display_name, invite=invite_token), 400

        pw_hash = hash_password(password)
        uid = database.create_user(username, email, pw_hash, display_name or username)
        session.clear()
        session["user_id"] = uid
        session["role"] = "user"
        flash("Welcome! Your account has been created.", "success")
        return redirect(url_for("welcome"))
    return render_template("signup.html", invite=invite_token)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        ip = request.remote_addr or "unknown"

        if not check_rate_limit(ip):
            flash("Too many login attempts. Please wait 5 minutes.", "error")
            return render_template("login.html"), 429

        user = database.get_user_by_username(identifier) or database.get_user_by_email(identifier)
        if user and verify_password(password, user["password_hash"]):
            # Transparent migration to Argon2id if still on PBKDF2
            from auth import needs_rehash
            if needs_rehash(user["password_hash"]):
                conn = database.get_connection()
                from auth import hash_password
                conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(password), user["id"]))
                conn.commit()
                conn.close()
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['display_name'] or user['username']}!", "success")
            return redirect(url_for("feed"))
        flash("Invalid credentials. Please try again.", "error")
        return render_template("login.html"), 401
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Profile routes
# ---------------------------------------------------------------------------

@app.route("/profile")
@login_required
def profile():
    user = _current_user()
    posts = database.list_posts_by_user(user["id"], limit=20)
    friends = database.list_friends(user["id"])
    return render_template("profile.html", user=user, posts=posts, friends=friends)


@app.route("/user/<int:user_id>")
@login_required
def user_profile(user_id):
    target = database.get_user(user_id)
    if not target:
        abort(404)
    me = _current_user()
    # Check friendship
    friendship = database.get_friendship(me["id"], user_id)
    is_friend = friendship and friendship["status"] == "accepted"
    is_self = me["id"] == user_id
    posts = database.list_posts_by_user(user_id, limit=20)
    return render_template("user_profile.html", target=target, is_friend=is_friend,
                           is_self=is_self, posts=posts, friendship=friendship)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    user = _current_user()
    if request.method == "POST":
        updates = {}
        for field in ["display_name", "bio", "pronouns", "location"]:
            val = request.form.get(field, "").strip()
            if val:
                updates[field] = val
        # Birthday fields
        bmonth = request.form.get("birthday_month", "").strip()
        bday = request.form.get("birthday_day", "").strip()
        if bmonth:
            updates["birthday_month"] = int(bmonth)
        if bday:
            updates["birthday_day"] = int(bday)
        # Handle avatar upload
        if "avatar" in request.files:
            file = request.files["avatar"]
            if file and file.filename and allowed_file(file.filename):
                try:
                    url = save_photo(file, user["id"])
                    updates["avatar_url"] = url
                except ValueError as e:
                    flash(str(e), "error")
        # Handle cover upload
        if "cover" in request.files:
            file = request.files["cover"]
            if file and file.filename and allowed_file(file.filename):
                try:
                    url = save_photo(file, user["id"])
                    updates["cover_url"] = url
                except ValueError as e:
                    flash(str(e), "error")
        if updates:
            database.update_user(user["id"], **updates)
            flash("Profile updated.", "success")
            database.check_and_award_achievements(user["id"])
        return redirect(url_for("profile"))
    return render_template("profile_edit.html", user=user)


# ---------------------------------------------------------------------------
# Feed routes
# ---------------------------------------------------------------------------

@app.route("/feed")
@login_required
def feed():
    me = _current_user()
    sort = request.args.get("sort", "newest")
    offset = int(request.args.get("offset", 0))
    limit = get_config().feed_default_limit
    posts = get_feed(me["id"], sort=sort, limit=limit, offset=offset)
    return render_template("feed.html", posts=posts, sort=sort, offset=offset, limit=limit)


# ---------------------------------------------------------------------------
# Post routes
# ---------------------------------------------------------------------------

@app.route("/post/new", methods=["GET", "POST"])
@login_required
def create_post():
    user = _current_user()
    if request.method == "POST":
        content_type = request.form.get("content_type", "text")
        text_content = request.form.get("text_content", "").strip()
        link_url = request.form.get("link_url", "").strip()
        visibility = request.form.get("visibility", "friends")
        if visibility not in ("friends", "only_me"):
            visibility = "friends"

        photo_url = None
        video_url = None
        voice_url = None
        if "photo" in request.files:
            file = request.files["photo"]
            if file and file.filename and allowed_file(file.filename):
                try:
                    photo_url = save_photo(file, user["id"])
                except ValueError as e:
                    flash(str(e), "error")
                    return render_template("create_post.html"), 400
        if "video" in request.files:
            file = request.files["video"]
            if file and file.filename:
                from uploads import allowed_video_file, save_video
                if allowed_video_file(file.filename):
                    try:
                        video_url = save_video(file, user["id"])
                    except ValueError as e:
                        flash(str(e), "error")
                        return render_template("create_post.html"), 400
        if "voice" in request.files:
            file = request.files["voice"]
            if file and file.filename:
                from uploads import allowed_voice_file, save_voice
                if allowed_voice_file(file.filename):
                    try:
                        voice_url = save_voice(file, user["id"])
                    except ValueError as e:
                        flash(str(e), "error")
                        return render_template("create_post.html"), 400

        # Validate content_type
        if content_type == "text":
            if not text_content or len(text_content) > 2000:
                flash("Text must be 1-2000 characters.", "error")
                return render_template("create_post.html"), 400
            post_text = text_content
            link_url = None
            photo_url = None
        elif content_type == "link":
            if not link_url or not link_url.startswith(("http://", "https://")):
                flash("Please enter a valid URL starting with http:// or https://", "error")
                return render_template("create_post.html"), 400
            post_text = None
            photo_url = None
        elif content_type == "photo":
            if not photo_url:
                flash("Please upload a photo.", "error")
                return render_template("create_post.html"), 400
            post_text = request.form.get("caption", "").strip() or None
            link_url = None
        elif content_type == "video":
            if not video_url:
                flash("Please upload a video (≤29 seconds, mp4/webm/mov).", "error")
                return render_template("create_post.html"), 400
            post_text = text_content or None
            link_url = None
        elif content_type == "voice":
            if not voice_url:
                flash("Please upload a voice message.", "error")
                return render_template("create_post.html"), 400
            post_text = text_content or None
            link_url = None
        else:
            flash("Invalid content type.", "error")
            return render_template("create_post.html"), 400

        # Moderation
        mod_score, mod_reason = moderate_text(post_text or link_url or "")
        mod_status = status_from_score(mod_score)

        # Content warning
        content_warning = request.form.get("content_warning", "").strip()

        # Create post
        post_id = database.create_post(
            user["id"], content_type, text_content=post_text,
            link_url=link_url, photo_url=photo_url, visibility=visibility,
        )

        # Store video/voice URLs
        conn = database.get_connection()
        if video_url:
            conn.execute("UPDATE posts SET video_url = ? WHERE id = ?", (video_url, post_id))
        if voice_url:
            conn.execute("UPDATE posts SET voice_url = ? WHERE id = ?", (voice_url, post_id))
        conn.commit()
        conn.close()

        # Update moderation status if auto-approved or auto-rejected
        conn = database.get_connection()
        conn.execute("UPDATE posts SET moderation_status=? WHERE id=?", (mod_status, post_id))
        if content_warning:
            conn.execute("UPDATE posts SET content_warning=? WHERE id=?", (content_warning, post_id))
        # Extract and store hashtags
        database.store_hashtags(post_id, post_text or "")
        conn.commit()

        # Blockchain audit
        blockchain.add_block_within_conn(
            conn, "posts", post_id, "create",
            user["id"], f"type={content_type}; mod_score={mod_score}; reason={mod_reason}",
        )
        conn.commit()
        conn.close()

        if mod_status == "rejected":
            flash("Your post was rejected by automated moderation. Contact an admin if you believe this is an error.", "error")
            return redirect(url_for("feed"))
        if mod_status == "pending":
            flash("Your post is pending human review.", "info")
        else:
            flash("Post created!", "success")
        return redirect(url_for("feed"))
    return render_template("create_post.html")


@app.route("/post/<int:post_id>/like", methods=["POST"])
@login_required
def like_post_route(post_id):
    user = _current_user()
    database.like_post(user["id"], post_id)
    # Real-time notification to post author
    post = database.get_post(post_id)
    if post and post["user_id"] != user["id"]:
        _emit_notification(post["user_id"], "new_like", {"post_id": post_id, "liker_name": user["display_name"] or user["username"]})
    return redirect(url_for("feed"))


@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def comment_route(post_id):
    user = _current_user()
    text = request.form.get("text", "").strip()
    if not text:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("feed"))
    # Check reply control permissions
    post = database.get_post(post_id)
    if not post:
        abort(404)
    # Post author can always comment on their own post
    if post["user_id"] != user["id"]:
        friendship = database.get_friendship(user["id"], post["user_id"])
        is_friend = bool(friendship and friendship["status"] == "accepted")
        is_mentioned = database.is_word_muted(post["user_id"], f"@{user['username']}")
        if not database.can_reply(post_id, user["id"], is_friend, is_mentioned):
            flash("Replies are not allowed for this post.", "error")
            return redirect(url_for("feed"))
    try:
        database.add_comment(user["id"], post_id, text)
        # Real-time notification to post author
        if post and post["user_id"] != user["id"]:
            _emit_notification(post["user_id"], "new_comment", {"post_id": post_id, "commenter_name": user["display_name"] or user["username"]})
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("feed"))


# ---------------------------------------------------------------------------
# Friendship routes
# ---------------------------------------------------------------------------

@app.route("/friend/request/<int:user_id>", methods=["POST"])
@login_required
def friend_request(user_id):
    me = _current_user()
    try:
        fid = database.send_friend_request(me["id"], user_id)
        database.create_notification(user_id, "friend_request", fid,
                                     f"{me['display_name'] or me['username']} sent you a friend request.")
        flash("Friend request sent.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("user_profile", user_id=user_id))


@app.route("/friend/accept/<int:request_id>", methods=["POST"])
@login_required
def accept_request(request_id):
    database.accept_friend_request(request_id)
    flash("Friend request accepted.", "success")
    return redirect(url_for("friends"))


@app.route("/friend/reject/<int:request_id>", methods=["POST"])
@login_required
def reject_request(request_id):
    database.reject_friend_request(request_id)
    flash("Friend request rejected.", "info")
    return redirect(url_for("friends"))


@app.route("/friend/remove/<int:friendship_id>", methods=["POST"])
@login_required
def remove_friend(friendship_id):
    database.delete_friendship(friendship_id)
    flash("Friend removed.", "info")
    return redirect(url_for("friends"))


@app.route("/friends")
@login_required
def friends():
    me = _current_user()
    accepted = database.list_friends(me["id"])
    received = database.list_pending_requests(me["id"], "received")
    sent = database.list_pending_requests(me["id"], "sent")
    return render_template("friends.html", friends=accepted, received=received, sent=sent)


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/page/new", methods=["GET", "POST"])
@login_required
def new_page():
    user = _current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        slug = _slugify(request.form.get("slug", title).strip()) or _slugify(title)
        bio = request.form.get("bio", "").strip()
        links = request.form.get("links", "").strip()
        featured = request.form.get("featured_photos", "").strip()
        is_public = 1 if request.form.get("is_public") else 0
        content = json.dumps({
            "bio": bio,
            "links": [l.strip() for l in links.split("\n") if l.strip()],
            "featured_photos": [p.strip() for p in featured.split(",") if p.strip()],
        })
        if not title or not slug:
            flash("Title and slug are required.", "error")
            return render_template("new_page.html"), 400
        try:
            pid = database.create_page(user["id"], title, slug, content, is_public)
            flash("Page created.", "success")
            return redirect(url_for("page_view", user_id=user["id"], slug=slug))
        except sqlite3.IntegrityError:
            flash("A page with that slug already exists.", "error")
            return render_template("new_page.html"), 400
    return render_template("new_page.html")


@app.route("/page/<int:user_id>/<slug>")
def page_view(user_id, slug):
    page = database.get_page(user_id, slug)
    if not page:
        abort(404)
    owner = database.get_user(user_id)
    me = _current_user()
    # Privacy check
    if not page["is_public"]:
        if not me:
            abort(401)
        if me["id"] != user_id:
            friendship = database.get_friendship(me["id"], user_id)
            if not (friendship and friendship["status"] == "accepted"):
                abort(403)
    content = json.loads(page["content_json"])
    return render_template("page_view.html", page=page, owner=owner, content=content, is_owner=me and me["id"] == user_id)


# ---------------------------------------------------------------------------
# Photo gallery
# ---------------------------------------------------------------------------

@app.route("/photos/<int:user_id>")
@login_required
def photos(user_id):
    target = database.get_user(user_id)
    if not target:
        abort(404)
    rows = database.list_posts_by_user(user_id, limit=200)
    photos_only = [r for r in rows if r["content_type"] == "photo" and r["photo_url"]]
    return render_template("photos.html", target=target, photos=photos_only)


# ---------------------------------------------------------------------------
# Moderation admin
# ---------------------------------------------------------------------------

@app.route("/admin/moderation")
@login_required
@admin_required
def moderation_queue():
    conn = database.get_connection()
    rows = conn.execute(
        """SELECT p.*, u.username, u.display_name
           FROM posts p
           JOIN users u ON u.id = p.user_id
           WHERE p.moderation_status = 'pending'
           ORDER BY p.created_at DESC"""
    ).fetchall()
    conn.close()
    return render_template("moderation_queue.html", posts=[dict(r) for r in rows])


@app.route("/admin/moderation/<int:post_id>/<action>", methods=["POST"])
@login_required
@admin_required
def moderation_action(post_id, action):
    if action not in ("approve", "reject"):
        abort(400)
    conn = database.get_connection()
    conn.execute("UPDATE posts SET moderation_status=? WHERE id=?", (action + "d", post_id))
    blockchain.add_block_within_conn(
        conn, "posts", post_id, f"moderator_{action}",
        session.get("user_id"), f"manual {action} by admin",
    )
    conn.commit()
    conn.close()
    flash(f"Post {action}d.", "success")
    return redirect(url_for("moderation_queue"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/admin/dashboard")
@login_required
@admin_required
def dashboard():
    conn = database.get_connection()
    stats = {}
    # Users
    row = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()
    stats["total_users"] = row["c"]
    # Posts today
    row = conn.execute(
        "SELECT COUNT(*) as c FROM posts WHERE date(created_at) = date('now')"
    ).fetchone()
    stats["posts_today"] = row["c"]
    # Pending friends
    row = conn.execute("SELECT COUNT(*) as c FROM friendships WHERE status='pending'").fetchone()
    stats["pending_friends"] = row["c"]
    # Pending moderation
    row = conn.execute("SELECT COUNT(*) as c FROM posts WHERE moderation_status='pending'").fetchone()
    stats["pending_mod"] = row["c"]
    # Total posts
    row = conn.execute("SELECT COUNT(*) as c FROM posts").fetchone()
    stats["total_posts"] = row["c"]
    # Recent audit log
    audit_rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT 20"
    ).fetchall()
    stats["recent_audit"] = [dict(r) for r in audit_rows]
    # Posts per day (last 14 days)
    day_rows = conn.execute(
        """SELECT date(created_at) as day, COUNT(*) as c
           FROM posts WHERE created_at > datetime('now', '-14 days')
           GROUP BY day ORDER BY day"""
    ).fetchall()
    stats["posts_by_day"] = [dict(r) for r in day_rows]
    conn.close()
    return render_template("dashboard.html", stats=stats)


# ---------------------------------------------------------------------------
# Hermes Bridge
# ---------------------------------------------------------------------------

@app.route("/hermes/webhook", methods=["POST"])
def hermes_webhook():
    """Receive actions from a Hermes agent for moderation, notification, or summary."""
    secret = request.headers.get("X-Hermes-Secret", "")
    if secret != get_config().hermes_webhook_secret:
        return jsonify({"error": "Invalid secret"}), 403
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action")
    user_id = data.get("user_id")
    post_id = data.get("post_id")
    text = data.get("text", "")

    result = {"action": action, "ok": True}
    if action == "moderate":
        if post_id:
            post = database.get_post(post_id)
            if post:
                score, reason = moderate_text(post["text_content"] or "")
                status = status_from_score(score)
                conn = database.get_connection()
                conn.execute("UPDATE posts SET moderation_status=? WHERE id=?", (status, post_id))
                blockchain.add_block_within_conn(
                    conn, "posts", post_id, "hermes_moderate",
                    user_id, f"score={score}; reason={reason}",
                )
                conn.commit()
                conn.close()
                result["status"] = status
                result["score"] = score
                result["reason"] = reason
    elif action == "notify":
        if user_id and text:
            database.create_notification(user_id, "hermes", 0, text)
            result["notified"] = user_id
    elif action == "summarize":
        # Return feed summary for a user
        if user_id:
            posts = get_feed(user_id, limit=10)
            result["summary"] = f"{len(posts)} recent posts in your feed."
    else:
        result["ok"] = False
        result["error"] = f"Unknown action: {action}"
    return jsonify(result)


@app.route("/health")
def health():
    db_ok = True
    try:
        conn = database.get_connection()
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return jsonify({
        "status": "ok" if db_ok else "error",
        "db": "connected" if db_ok else "disconnected",
        "version": "0.3.0",
    }), status


@app.route("/health/passwords")
@admin_required
def health_passwords():
    conn = database.get_connection()
    pbkdf2 = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE password_hash LIKE 'pbkdf2:%'"
    ).fetchone()["c"]
    argon = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE password_hash LIKE '$argon2id%'"
    ).fetchone()["c"]
    conn.close()
    return jsonify({"pbkdf2": pbkdf2, "argon2id": argon, "recommendation": "Continue migration to Argon2id"})


# ---------------------------------------------------------------------------
# PWA
# ---------------------------------------------------------------------------

@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "mini-social-media",
        "short_name": "MiniSocial",
        "start_url": "/feed",
        "display": "standalone",
        "background_color": "#f5f7fa",
        "theme_color": "#4a90d9",
        "icons": [
            {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    })


@app.route("/sw.js")
def service_worker():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "sw.js", mimetype="application/javascript")


@app.route("/offline")
def offline_page():
    return render_template("offline.html")


# ---------------------------------------------------------------------------
# WebSocket (SocketIO)
# ---------------------------------------------------------------------------

@socketio.on("connect")
def handle_connect():
    uid = session.get("user_id")
    if not uid:
        return False  # reject anonymous
    join_room(f"user_{uid}")
    emit("connected", {"room": f"user_{uid}"})


@socketio.on("disconnect")
def handle_disconnect():
    uid = session.get("user_id")
    if uid:
        leave_room(f"user_{uid}")


@socketio.on("send_message")
def handle_send_message(data):
    uid = session.get("user_id")
    if not uid:
        return
    recipient_id = data.get("recipient_id")
    content = data.get("content", "").strip()
    if not recipient_id or not content:
        return
    # Validate friendship
    friendship = database.get_friendship(uid, recipient_id)
    if not (friendship and friendship["status"] == "accepted"):
        emit("error", {"text": "You can only message friends."})
        return
    mid = database.send_message(uid, recipient_id, content)
    # Notify recipient in real time
    emit("new_message", {"id": mid, "sender_id": uid, "content": content}, room=f"user_{recipient_id}")
    # Also notify sender for confirmation
    emit("message_sent", {"id": mid}, room=f"user_{uid}")


# ---------------------------------------------------------------------------
# Helper: real-time notification emitter
# ---------------------------------------------------------------------------

def _emit_notification(user_id: int, event: str, data: dict):
    try:
        socketio.emit(event, data, room=f"user_{user_id}")
    except Exception:
        pass  # SocketIO not connected, silently ignore


# ---------------------------------------------------------------------------
# v0.4.0: Stories
# ---------------------------------------------------------------------------

@app.route("/stories")
@login_required
def stories():
    me = _current_user()
    stories_list = database.get_active_stories(me["id"])
    # Group by user
    from collections import defaultdict
    grouped = defaultdict(list)
    for s in stories_list:
        grouped[s["user_id"]].append(s)
    return render_template("stories.html", grouped=grouped)


@app.route("/story/new", methods=["POST"])
@login_required
def create_story():
    user = _current_user()
    content_type = request.form.get("content_type", "text")
    text_content = request.form.get("text_content", "").strip()
    photo_url = None
    video_url = None
    if "photo" in request.files:
        file = request.files["photo"]
        if file and file.filename and allowed_file(file.filename):
            photo_url = save_photo(file, user["id"])
    if "video" in request.files:
        file = request.files["video"]
        if file and file.filename:
            from uploads import allowed_video_file, save_video
            if allowed_video_file(file.filename):
                video_url = save_video(file, user["id"])
    sid = database.create_story(user["id"], content_type, text_content, photo_url, video_url)
    flash("Story posted! It will disappear in 24 hours.", "success")
    return redirect(url_for("feed"))


# ---------------------------------------------------------------------------
# v0.4.0: Albums (Photographer Tools)
# ---------------------------------------------------------------------------

@app.route("/albums")
@login_required
def albums():
    me = _current_user()
    my_albums = database.list_user_albums(me["id"])
    return render_template("albums.html", albums=my_albums)


@app.route("/album/new", methods=["GET", "POST"])
@login_required
def new_album():
    user = _current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("new_album.html"), 400
        aid = database.create_album(user["id"], title, description)
        flash("Album created!", "success")
        return redirect(url_for("album_detail", album_id=aid))
    return render_template("new_album.html")


@app.route("/album/<int:album_id>")
def album_detail(album_id):
    album = database.get_album(album_id)
    if not album:
        abort(404)
    photos = database.get_album_photos(album_id)
    return render_template("album_detail.html", album=album, photos=photos)


@app.route("/album/<int:album_id>/add", methods=["POST"])
@login_required
def add_album_photo(album_id):
    user = _current_user()
    album = database.get_album(album_id)
    if not album or album["user_id"] != user["id"]:
        abort(403)
    if "photo" in request.files:
        file = request.files["photo"]
        if file and file.filename and allowed_file(file.filename):
            url = save_photo(file, user["id"])
            caption = request.form.get("caption", "").strip()
            # Simple EXIF extraction
            exif_data = None
            try:
                from PIL import Image
                from PIL.ExifTags import TAGS
                img = Image.open(file.stream)
                exif = img._getexif()
                if exif:
                    exif_dict = {TAGS.get(k, k): str(v)[:100] for k, v in exif.items()}
                    exif_data = str(exif_dict)[:500]
            except Exception:
                pass
            database.add_photo_to_album(album_id, url, caption, exif_data=exif_data)
            flash("Photo added!", "success")
    return redirect(url_for("album_detail", album_id=album_id))


# ---------------------------------------------------------------------------
# v0.4.0: Daily Prompts
# ---------------------------------------------------------------------------

@app.route("/daily-prompt")
def daily_prompt():
    prompt = database.get_daily_prompt()
    return render_template("daily_prompt.html", prompt=prompt)


@app.route("/admin/daily-prompt", methods=["POST"])
@login_required
@admin_required
def admin_daily_prompt():
    text = request.form.get("prompt_text", "").strip()
    if text:
        user = _current_user()
        database.create_daily_prompt(text, user["id"])
        flash("Daily prompt set!", "success")
    return redirect(url_for("feed"))


# ---------------------------------------------------------------------------
# v0.4.0: Ice Breakers
# ---------------------------------------------------------------------------

@app.route("/ice-breaker")
@login_required
def ice_breaker():
    question = database.get_random_ice_breaker()
    return render_template("ice_breaker.html", question=question)


# ---------------------------------------------------------------------------
# v0.4.0: Reading List
# ---------------------------------------------------------------------------

@app.route("/reading-list")
@login_required
def reading_list():
    me = _current_user()
    items = database.get_reading_list(me["id"])
    return render_template("reading_list.html", items=items)


@app.route("/reading-list/add", methods=["POST"])
@login_required
def add_reading():
    me = _current_user()
    url = request.form.get("url", "").strip()
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip()
    if not url:
        flash("URL is required.", "error")
        return redirect(url_for("reading_list"))
    database.add_to_reading_list(me["id"], url, title, notes)
    flash("Added to reading list!", "success")
    return redirect(url_for("reading_list"))


# ---------------------------------------------------------------------------
# v0.4.0: Wishlist
# ---------------------------------------------------------------------------

@app.route("/wishlist/<int:user_id>")
@login_required
def wishlist(user_id):
    items = database.get_wishlist(user_id)
    owner = database.get_user(user_id)
    return render_template("wishlist.html", items=items, owner=owner)


@app.route("/wishlist/add", methods=["POST"])
@login_required
def add_wishlist():
    me = _current_user()
    name = request.form.get("item_name", "").strip()
    link = request.form.get("item_link", "").strip()
    price = request.form.get("price", "").strip()
    if not name:
        flash("Item name is required.", "error")
        return redirect(url_for("profile"))
    database.add_wishlist_item(me["id"], name, link, price)
    flash("Added to wishlist!", "success")
    return redirect(url_for("profile"))


@app.route("/wishlist/<int:item_id>/claim", methods=["POST"])
@login_required
def claim_wishlist(item_id):
    me = _current_user()
    database.claim_wishlist_item(item_id, me["id"])
    flash("Item claimed! The user won't know until later.", "success")
    return redirect(url_for("feed"))


# ---------------------------------------------------------------------------
# v0.4.0: Notes
# ---------------------------------------------------------------------------

@app.route("/notes")
@login_required
def notes():
    me = _current_user()
    items = database.list_notes(me["id"])
    return render_template("notes.html", notes=items)


@app.route("/note/new", methods=["GET", "POST"])
@login_required
def new_note():
    if request.method == "POST":
        me = _current_user()
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        circle_id = request.form.get("circle_id", None)
        if not title or not content:
            flash("Title and content are required.", "error")
            return render_template("new_note.html"), 400
        nid = database.create_note(me["id"], title, content, circle_id)
        flash("Note created!", "success")
        return redirect(url_for("note_detail", note_id=nid))
    return render_template("new_note.html")


@app.route("/note/<int:note_id>")
@login_required
def note_detail(note_id):
    note = database.get_note(note_id)
    if not note:
        abort(404)
    return render_template("note_detail.html", note=note)


@app.route("/note/<int:note_id>/edit", methods=["POST"])
@login_required
def edit_note(note_id):
    me = _current_user()
    content = request.form.get("content", "").strip()
    if content:
        database.update_note(note_id, content, me["id"])
        flash("Note updated!", "success")
    return redirect(url_for("note_detail", note_id=note_id))


# ---------------------------------------------------------------------------
# v0.4.0: Message Groups
# ---------------------------------------------------------------------------

@app.route("/groups")
@login_required
def groups():
    me = _current_user()
    conn = database.get_connection()
    rows = conn.execute(
        """SELECT g.* FROM message_groups g
           JOIN group_members gm ON gm.group_id = g.id
           WHERE gm.user_id = ?""",
        (me["id"],),
    ).fetchall()
    conn.close()
    return render_template("groups.html", groups=[dict(r) for r in rows])


@app.route("/group/new", methods=["POST"])
@login_required
def new_group():
    me = _current_user()
    name = request.form.get("name", "").strip()
    members = request.form.getlist("members")
    if not name:
        flash("Group name is required.", "error")
        return redirect(url_for("friends"))
    gid = database.create_message_group(name, me["id"])
    for mid in members:
        database.add_to_group(gid, int(mid))
    flash("Group created!", "success")
    return redirect(url_for("group_chat", group_id=gid))


@app.route("/group/<int:group_id>")
@login_required
def group_chat(group_id):
    msgs = database.get_group_messages(group_id)
    return render_template("group_chat.html", messages=msgs, group_id=group_id)


# ---------------------------------------------------------------------------
# v0.4.0: Hermes Prompts (Connection Encouragement)
# ---------------------------------------------------------------------------

@app.route("/hermes/prompts")
@login_required
def hermes_prompts():
    me = _current_user()
    prompts = database.get_hermes_prompts(me["id"])
    return render_template("hermes_prompts.html", prompts=prompts)


@app.route("/hermes/prompt/<int:prompt_id>/dismiss", methods=["POST"])
@login_required
def dismiss_hermes_prompt_route(prompt_id):
    database.dismiss_hermes_prompt(prompt_id)
    return redirect(url_for("hermes_prompts"))


# ---------------------------------------------------------------------------
# v0.4.0: Birthdays
# ---------------------------------------------------------------------------

@app.route("/birthdays")
@login_required
def birthdays():
    me = _current_user()
    upcoming = database.get_upcoming_birthdays(me["id"], days_ahead=30)
    return render_template("birthdays.html", birthdays=upcoming)


# ---------------------------------------------------------------------------
# v0.4.0: Mood
# ---------------------------------------------------------------------------

@app.route("/mood", methods=["POST"])
@login_required
def set_mood():
    me = _current_user()
    mood = request.form.get("mood", "").strip()
    conn = database.get_connection()
    conn.execute("UPDATE users SET mood = ? WHERE id = ?", (mood, me["id"]))
    conn.commit()
    conn.close()
    flash("Mood updated!", "success")
    return redirect(url_for("profile"))


# ---------------------------------------------------------------------------
# v0.5.0: Admin Disk Usage
# ---------------------------------------------------------------------------

@app.route("/admin/disk")
@login_required
def admin_disk():
    if g.current_user.get("role") != "admin":
        abort(403)
    import subprocess
    db_size = os.path.getsize(os.path.join(BASE_DIR, DATABASE_PATH)) if os.path.exists(os.path.join(BASE_DIR, DATABASE_PATH)) else 0
    uploads_dir = os.path.join(BASE_DIR, "static", "uploads")
    uploads_size = 0
    uploads_count = 0
    if os.path.isdir(uploads_dir):
        for root, dirs, files in os.walk(uploads_dir):
            uploads_count += len(files)
            for f in files:
                fp = os.path.join(root, f)
                uploads_size += os.path.getsize(fp)
    conn = database.get_connection()
    stats = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM users) as user_count,
            (SELECT COUNT(*) FROM posts) as post_count,
            (SELECT COUNT(*) FROM posts WHERE photo_url IS NOT NULL) as photo_count,
            (SELECT COUNT(*) FROM posts WHERE video_url IS NOT NULL) as video_count,
            (SELECT COUNT(*) FROM posts WHERE voice_url IS NOT NULL) as voice_count
    """).fetchone()
    conn.close()
    return render_template("admin_disk.html", db_size=db_size, uploads_size=uploads_size,
                           uploads_count=uploads_count, stats=stats)


# ---------------------------------------------------------------------------
# v0.5.0: Achievements
# ---------------------------------------------------------------------------

@app.route("/achievements")
@login_required
def achievements():
    all_ach = database.get_achievements()
    user_ach = {a["achievement_id"]: a for a in database.get_user_achievements(g.current_user["id"])}
    return render_template("achievements.html", achievements=all_ach, user_achievements=user_ach)


@app.route("/achievements/mark_seen", methods=["POST"])
@login_required
def mark_achievements_seen():
    conn = database.get_connection()
    conn.execute(
        "UPDATE user_achievements SET is_seen = 1 WHERE user_id = ?",
        (g.current_user["id"],),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# v0.5.0: Community Guidelines
# ---------------------------------------------------------------------------

@app.route("/guidelines")
def guidelines():
    return render_template("guidelines.html")


@app.route("/guidelines/accept", methods=["POST"])
@login_required
def accept_guidelines():
    database.update_user(g.current_user["id"], {
        "accepted_guidelines_at": datetime.now(timezone.utc).isoformat()
    })
    flash("Community guidelines accepted.", "success")
    return redirect(url_for("feed"))


# ---------------------------------------------------------------------------
# v0.5.0: Stripe Donations (optional)
# ---------------------------------------------------------------------------

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")

@app.route("/donate")
def donate():
    return render_template("donate.html", enabled=bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID))


@app.route("/donate/checkout", methods=["POST"])
def donate_checkout():
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        abort(404)
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    checkout_session = stripe.checkout.Session.create(
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        mode="payment",
        success_url=request.host_url + "donate/success",
        cancel_url=request.host_url + "donate/cancel",
    )
    return redirect(checkout_session.url, code=303)


@app.route("/donate/success")
def donate_success():
    return render_template("donate_result.html", success=True)


@app.route("/donate/cancel")
def donate_cancel():
    return render_template("donate_result.html", success=False)


# ---------------------------------------------------------------------------
# v0.5.0: Backup
# ---------------------------------------------------------------------------

import shutil
import tarfile

@app.route("/admin/backup", methods=["GET", "POST"])
@login_required
def admin_backup():
    if g.current_user.get("role") != "admin":
        abort(403)
    if request.method == "POST":
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(BASE_DIR, "backups", timestamp)
        os.makedirs(backup_dir, exist_ok=True)
        # SQLite dump
        db_path = os.path.join(BASE_DIR, DATABASE_PATH)
        dump_path = os.path.join(backup_dir, "social.sql")
        conn = sqlite3.connect(db_path)
        with open(dump_path, "w") as f:
            for line in conn.iterdump():
                f.write(line + "\n")
        conn.close()
        # Uploads tar
        uploads_dir = os.path.join(BASE_DIR, "static", "uploads")
        tar_path = os.path.join(backup_dir, "uploads.tar.gz")
        if os.path.isdir(uploads_dir):
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(uploads_dir, arcname="uploads")
        # Final tar
        final_tar = os.path.join(BASE_DIR, "backups", f"backup_{timestamp}.tar.gz")
        with tarfile.open(final_tar, "w:gz") as tar:
            tar.add(backup_dir, arcname=timestamp)
        size = os.path.getsize(final_tar)
        database.log_backup(os.path.basename(final_tar), size, g.current_user["id"])
        # Cleanup old backups (keep last 7)
        backups = sorted([
            f for f in os.listdir(os.path.join(BASE_DIR, "backups"))
            if f.startswith("backup_") and f.endswith(".tar.gz")
        ])
        for old in backups[:-7]:
            os.remove(os.path.join(BASE_DIR, "backups", old))
        flash("Backup created successfully.", "success")
        return redirect(url_for("admin_backup"))
    backups = database.list_backups()
    return render_template("admin_backup.html", backups=backups)


# ---------------------------------------------------------------------------
# v0.5.0: Post Series
# ---------------------------------------------------------------------------

@app.route("/series/new", methods=["GET", "POST"])
@login_required
def new_series():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("Title is required.", "danger")
            return redirect(url_for("new_series"))
        sid = database.create_series(g.current_user["id"], title, description)
        flash("Series created!", "success")
        return redirect(url_for("view_series", series_id=sid))
    return render_template("new_series.html")


@app.route("/series/<int:series_id>")
@login_required
def view_series(series_id):
    conn = database.get_connection()
    series = conn.execute("SELECT * FROM post_series WHERE id = ?", (series_id,)).fetchone()
    conn.close()
    if not series:
        abort(404)
    posts = database.get_series_posts(series_id)
    return render_template("series.html", series=dict(series), posts=posts)


# ---------------------------------------------------------------------------
# v0.6.0: Content Labels
# ---------------------------------------------------------------------------

@app.route("/settings/labels")
@login_required
def label_settings():
    user = _current_user()
    prefs = database.get_user_label_prefs(user["id"])
    label_types = database.VALID_LABEL_TYPES
    return render_template("label_settings.html", prefs=prefs, label_types=label_types)


@app.route("/settings/labels", methods=["POST"])
@login_required
def label_settings_update():
    user = _current_user()
    for lt in database.VALID_LABEL_TYPES:
        action = request.form.get(lt, "warn")
        if action in ('show', 'warn', 'hide'):
            database.set_user_label_pref(user["id"], lt, action)
    flash("Content label preferences saved.", "success")
    return redirect(url_for("label_settings"))


@app.route("/post/<int:post_id>/label", methods=["POST"])
@login_required
def add_post_label_route(post_id):
    label_type = request.form.get("label_type", "").strip()
    post = database.get_post(post_id)
    if not post:
        abort(404)
    try:
        database.add_post_label(post_id, label_type)
    except ValueError:
        flash("Invalid label type.", "error")
        return redirect(url_for("feed"))
    flash("Label added.", "success")
    return redirect(url_for("feed"))


@app.route("/settings/muted-words")
@login_required
def muted_words():
    """Render the user's muted words management page."""
    me = _current_user()
    words = database.list_muted_words(me["id"])
    return render_template("muted_words.html", words=words)


@app.route("/settings/muted-words/add", methods=["POST"])
@login_required
def add_muted_word():
    """Add a new muted word from the form."""
    me = _current_user()
    word = request.form.get("word", "").strip()
    if not word:
        flash("Word cannot be empty.", "error")
        return redirect(url_for("muted_words"))
    database.add_muted_word(me["id"], word)
    flash(f"Muted word '{word}' added.", "success")
    return redirect(url_for("muted_words"))


@app.route("/settings/muted-words/<int:word_id>/remove", methods=["POST"])
@login_required
def remove_muted_word(word_id):
    """Remove a muted word by its row id."""
    me = _current_user()
    conn = database.get_connection()
    row = conn.execute(
        "SELECT * FROM muted_words WHERE id = ? AND user_id = ?",
        (word_id, me["id"]),
    ).fetchone()
    word = row["word"] if row else None
    conn.close()
    if not row:
        flash("Muted word not found.", "error")
        return redirect(url_for("muted_words"))
    database.remove_muted_word(me["id"], row["word"])
    flash(f"Muted word '{word}' removed.", "success")
    return redirect(url_for("muted_words"))


# ---------------------------------------------------------------------------
# Static uploads serving
# ---------------------------------------------------------------------------

@app.route("/modlists")
@login_required
def mod_lists():
    me = _current_user()
    mod_lists_all = database.list_mod_lists(limit=50)
    my_subs = {s["mod_list_id"] for s in database.get_subscribed_mod_lists(me["id"])}
    return render_template("mod_lists.html", mod_lists=mod_lists_all, my_subs=my_subs)


@app.route("/modlist/new", methods=["GET", "POST"])
@login_required
def new_mod_list():
    user = _current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        list_type = request.form.get("list_type", "block")
        if list_type not in ("block", "mute"):
            list_type = "block"
        if not name:
            flash("Name is required.", "error")
            return redirect(url_for("new_mod_list"))
        lid = database.create_mod_list(user["id"], name, description, list_type)
        flash("Moderation list created!", "success")
        return redirect(url_for("mod_list_detail", list_id=lid))
    return render_template("new_mod_list.html")


@app.route("/modlist/<int:list_id>")
@login_required
def mod_list_detail(list_id):
    mod_list = database.get_mod_list(list_id)
    if not mod_list:
        abort(404)
    members = database.get_mod_list_members(list_id)
    me = _current_user()
    my_subs = {s["mod_list_id"] for s in database.get_subscribed_mod_lists(me["id"])}
    return render_template("mod_list_detail.html", mod_list=mod_list, members=members, my_subs=my_subs)


@app.route("/modlist/<int:list_id>/add", methods=["POST"])
@login_required
def mod_list_add_member(list_id):
    mod_list = database.get_mod_list(list_id)
    if not mod_list:
        abort(404)
    target_user_id = request.form.get("target_user_id", "").strip()
    if not target_user_id:
        flash("User ID is required.", "error")
        return redirect(url_for("mod_list_detail", list_id=list_id))
    try:
        target_user_id = int(target_user_id)
    except (TypeError, ValueError):
        flash("Invalid user ID.", "error")
        return redirect(url_for("mod_list_detail", list_id=list_id))
    target = database.get_user(target_user_id)
    if not target:
        flash("User not found.", "error")
        return redirect(url_for("mod_list_detail", list_id=list_id))
    try:
        database.add_to_mod_list(list_id, target_user_id)
        flash(f"Added {target['username']} to list.", "success")
    except Exception:
        flash("User is already on this list.", "error")
    return redirect(url_for("mod_list_detail", list_id=list_id))


@app.route("/modlist/<int:list_id>/remove", methods=["POST"])
@login_required
def mod_list_remove_member(list_id):
    mod_list = database.get_mod_list(list_id)
    if not mod_list:
        abort(404)
    target_user_id = request.form.get("target_user_id", "").strip()
    try:
        target_user_id = int(target_user_id)
    except (TypeError, ValueError):
        flash("Invalid user ID.", "error")
        return redirect(url_for("mod_list_detail", list_id=list_id))
    database.remove_from_mod_list(list_id, target_user_id)
    flash("Removed from list.", "success")
    return redirect(url_for("mod_list_detail", list_id=list_id))


@app.route("/modlist/<int:list_id>/subscribe", methods=["POST"])
@login_required
def mod_list_subscribe(list_id):
    me = _current_user()
    mod_list = database.get_mod_list(list_id)
    if not mod_list:
        abort(404)
    try:
        database.subscribe_mod_list(me["id"], list_id)
        flash("Subscribed to list.", "success")
    except Exception:
        flash("Already subscribed.", "error")
    return redirect(url_for("mod_lists"))


@app.route("/modlist/<int:list_id>/unsubscribe", methods=["POST"])
@login_required
def mod_list_unsubscribe(list_id):
    me = _current_user()
    mod_list = database.get_mod_list(list_id)
    if not mod_list:
        abort(404)
    database.unsubscribe_mod_list(me["id"], list_id)
    flash("Unsubscribed from list.", "success")
    return redirect(url_for("mod_lists"))


# ---------------------------------------------------------------------------
# v0.6.0: Custom Feeds
# ---------------------------------------------------------------------------

@app.route("/custom-feeds")
@login_required
def custom_feeds():
    me = _current_user()
    feeds = database.list_custom_feeds(me["id"])
    return render_template("custom_feeds.html", feeds=feeds)


@app.route("/custom-feed/new", methods=["GET", "POST"])
@login_required
def new_custom_feed():
    me = _current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        filter_type = request.form.get("filter_type", "hashtag").strip()
        filter_value = request.form.get("filter_value", "").strip()
        if not name or not filter_value:
            flash("Name and filter value are required.", "danger")
            return redirect(url_for("new_custom_feed"))
        if filter_type not in database.VALID_FILTER_TYPES:
            flash("Invalid filter type.", "danger")
            return redirect(url_for("new_custom_feed"))
        feed_id = database.create_custom_feed(me["id"], name, filter_type, filter_value)
        flash("Custom feed created!", "success")
        return redirect(url_for("custom_feed_detail", feed_id=feed_id))
    return render_template("custom_feeds.html", feeds=database.list_custom_feeds(me["id"]), creating=True)


@app.route("/custom-feed/<int:feed_id>")
@login_required
def custom_feed_detail(feed_id):
    feed = database.get_custom_feed(feed_id)
    if not feed:
        abort(404)
    posts = database.get_custom_feed_posts(feed_id)
    return render_template("custom_feed_detail.html", feed=feed, posts=posts)


@app.route("/custom-feed/<int:feed_id>/delete", methods=["POST"])
@login_required
def delete_custom_feed(feed_id):
    me = _current_user()
    removed = database.delete_custom_feed(feed_id, me["id"])
    if removed:
        flash("Custom feed deleted.", "success")
    else:
        flash("Feed not found.", "error")
    return redirect(url_for("custom_feeds"))


@app.route("/custom-feed/<int:feed_id>/pin", methods=["POST"])
@login_required
def pin_custom_feed(feed_id):
    me = _current_user()
    pinned = database.toggle_pin_custom_feed(feed_id, me["id"])
    flash("Feed pinned!" if pinned else "Feed unpinned.", "success")
    return redirect(url_for("custom_feeds"))


# ---------------------------------------------------------------------------
# v0.6.0: Reply Controls
# ---------------------------------------------------------------------------

@app.route("/post/<int:post_id>/reply-control", methods=["POST"])
@login_required
def set_reply_control_route(post_id):
    user = _current_user()
    post = database.get_post(post_id)
    if not post:
        abort(404)
    if post["user_id"] != user["id"]:
        flash("You can only change reply settings on your own posts.", "error")
        return redirect(url_for("feed"))
    reply_scope = request.form.get("reply_scope", "friends").strip()
    if reply_scope not in ("everyone", "friends", "mentioned", "nobody"):
        flash("Invalid reply scope.", "error")
        return redirect(url_for("feed"))
    database.set_reply_control(post_id, reply_scope)
    flash("Reply settings updated.", "success")
    return redirect(url_for("feed"))


# ---------------------------------------------------------------------------
# Mute Accounts (private — muted users are not notified)
# ---------------------------------------------------------------------------

@app.route("/user/<int:user_id>/mute", methods=["POST"])
@login_required
def mute_user_route(user_id):
    me = _current_user()
    target = database.get_user(user_id)
    if not target:
        abort(404)
    if user_id == me["id"]:
        flash("You cannot mute yourself.", "error")
        return redirect(request.referrer or url_for("feed"))
    database.mute_user(me["id"], user_id)
    flash(f"You muted {target['display_name'] or target['username']}.", "success")
    return redirect(request.referrer or url_for("feed"))


@app.route("/user/<int:user_id>/unmute", methods=["POST"])
@login_required
def unmute_user_route(user_id):
    me = _current_user()
    target = database.get_user(user_id)
    if not target:
        abort(404)
    database.unmute_user(me["id"], user_id)
    flash(f"You unmuted {target['display_name'] or target['username']}.", "success")
    return redirect(request.referrer or url_for("feed"))


@app.route("/settings/muted")
@login_required
def muted_accounts():
    me = _current_user()
    muted = database.list_muted(me["id"])
    return render_template("muted_accounts.html", muted=muted)


# ---------------------------------------------------------------------------
# v0.6.0: Starter Packs
# ---------------------------------------------------------------------------

@app.route("/packs")
@login_required
def starter_packs():
    packs = database.list_starter_packs()
    return render_template("starter_packs.html", packs=packs)


@app.route("/pack/new", methods=["GET", "POST"])
@login_required
def new_starter_pack():
    user = _current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        if not name:
            flash("Pack name is required.", "error")
            return render_template("starter_pack_new.html"), 400
        pid = database.create_starter_pack(user["id"], name, description)
        flash("Starter pack created!", "success")
        return redirect(url_for("starter_pack_detail", pack_id=pid))
    return render_template("starter_pack_new.html")


@app.route("/pack/<int:pack_id>")
@login_required
def starter_pack_detail(pack_id):
    pack = database.get_starter_pack(pack_id)
    if not pack:
        abort(404)
    members = database.get_starter_pack_members(pack_id)
    return render_template("starter_pack_detail.html", pack=pack, members=members)


@app.route("/pack/<int:pack_id>/add", methods=["POST"])
@login_required
def add_pack_member(pack_id):
    pack = database.get_starter_pack(pack_id)
    if not pack:
        abort(404)
    user_id = request.form.get("user_id", "").strip()
    if not user_id:
        flash("User ID is required.", "error")
        return redirect(url_for("starter_pack_detail", pack_id=pack_id))
    try:
        database.add_to_starter_pack(pack_id, int(user_id))
        flash("Member added to pack.", "success")
    except Exception:
        flash("Could not add member (already in pack?).", "error")
    return redirect(url_for("starter_pack_detail", pack_id=pack_id))


@app.route("/pack/<int:pack_id>/remove", methods=["POST"])
@login_required
def remove_pack_member(pack_id):
    user_id = request.form.get("user_id", "").strip()
    if not user_id:
        flash("User ID is required.", "error")
        return redirect(url_for("starter_pack_detail", pack_id=pack_id))
    database.remove_from_starter_pack(pack_id, int(user_id))
    flash("Member removed from pack.", "info")
    return redirect(url_for("starter_pack_detail", pack_id=pack_id))


@app.route("/pack/<int:pack_id>/follow-all", methods=["POST"])
@login_required
def follow_all_pack_members(pack_id):
    me = _current_user()
    pack = database.get_starter_pack(pack_id)
    if not pack:
        abort(404)
    count = database.follow_all_in_pack(me["id"], pack_id)
    if count:
        flash(f"Sent {count} friend request(s) to pack members.", "success")
    else:
        flash("No new friend requests to send (all already friends or pending).", "info")
    return redirect(url_for("starter_pack_detail", pack_id=pack_id))


# ---------------------------------------------------------------------------
# Static uploads serving
# ---------------------------------------------------------------------------

@app.route("/static/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static", "uploads"), filename)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    database.init_database()
    port = int(os.environ.get("PORT", 9197))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    socketio.run(app, host="127.0.0.1", port=port, debug=debug, allow_unsafe_werkzeug=True)
