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


def _slugify(text: str) -> str:
    return re.sub(r"[^\w-]+", "-", text.lower()).strip("-")


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        display_name = request.form.get("display_name", "").strip()

        # Validation
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

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("signup.html", username=username, email=email, display_name=display_name), 400

        pw_hash = hash_password(password)
        uid = database.create_user(username, email, pw_hash, display_name or username)
        session.clear()
        session["user_id"] = uid
        session["role"] = "user"
        flash("Welcome! Your account has been created.", "success")
        return redirect(url_for("feed"))
    return render_template("signup.html")


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
        if "photo" in request.files:
            file = request.files["photo"]
            if file and file.filename and allowed_file(file.filename):
                try:
                    photo_url = save_photo(file, user["id"])
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
        else:
            flash("Invalid content type.", "error")
            return render_template("create_post.html"), 400

        # Moderation
        mod_score, mod_reason = moderate_text(post_text or link_url or "")
        mod_status = status_from_score(mod_score)

        # Create post
        post_id = database.create_post(
            user["id"], content_type, text_content=post_text,
            link_url=link_url, photo_url=photo_url, visibility=visibility,
        )

        # Update moderation status if auto-approved or auto-rejected
        conn = database.get_connection()
        conn.execute("UPDATE posts SET moderation_status=? WHERE id=?", (mod_status, post_id))
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
    return redirect(url_for("feed"))


@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def comment_route(post_id):
    user = _current_user()
    text = request.form.get("text", "").strip()
    if not text:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("feed"))
    try:
        database.add_comment(user["id"], post_id, text)
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
    app.run(host="127.0.0.1", port=port, debug=debug)
