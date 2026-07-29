# mini-social-media — 30 Testable Build Prompts

> Privacy-first, friends-only social media platform for ~100 users.
> Flask + SQLite. Local hosting. Blockchain audit log. Agent moderation.

---

## Phase 1: Foundation (Prompts 1–8)

### Prompt 01 — Database Schema
Create `database.py` that initializes SQLite with:
- `users` (id, username, display_name, email, password_hash, bio, avatar_url, cover_url, role, created_at)
- `posts` (id, user_id, content_type, text_content, link_url, photo_url, visibility, created_at, updated_at)
- `friendships` (id, requester_id, addressee_id, status, created_at, updated_at)
- `post_likes` (id, user_id, post_id, created_at)
- `post_comments` (id, user_id, post_id, text, created_at)
- `blocks` (id, user_id, target_id, created_at)
- `audit_log` (id, table_name, record_id, action, user_id, timestamp, prev_hash, block_hash)

**Test:** `test_database_schema.py` — assert all tables exist via `PRAGMA table_list` or `SELECT name FROM sqlite_master`.

### Prompt 02 — Connection Layer
In `database.py`, implement `get_connection()` using `sqlite3.Row` factory, `PRAGMA foreign_keys = ON`, and `PRAGMA journal_mode = WAL`.

**Test:** `test_connection.py` — assert row_factory is Row, assert foreign_keys returns 1.

### Prompt 03 — Password Hashing
In `auth.py`, implement `hash_password(plain)` and `verify_password(plain, hashed)` using `werkzeug.security.generate_password_hash` / `check_password_hash` with PBKDF2.

**Test:** `test_password_hashing.py` — hash "test123", verify it passes; verify wrong password fails.

### Prompt 04 — Session Management
In `app.py` (or `auth.py`), implement Flask session config with `SECRET_KEY` from env, `session.clear()` on login, and a `login_required` decorator. Add rate limiting middleware (10 login attempts per 5 min per IP).

**Test:** `test_session.py` — login sets session["user_id"]; logout clears it; `@login_required` redirects anonymous users.

### Prompt 05 — Signup Page
Create route `/signup` (GET/POST) + `templates/signup.html`. Validate: username alphanumeric 3-30 chars, email format, password ≥ 8 chars, passwords match. Check username/email uniqueness before insert.

**Test:** `test_signup.py` — valid signup creates user; duplicate username returns error; short password rejected; mismatched passwords rejected.

### Prompt 06 — Login Page
Create route `/login` (GET/POST) + `templates/login.html`. Authenticate with username/email + password. On success: `session.clear()` then set `user_id`, `role`. Redirect to `/feed`. On failure: show error with generic message (don't leak which field is wrong).

**Test:** `test_login.py` — valid login redirects to feed; wrong password stays on login; nonexistent user stays on login; session has user_id after success.

### Prompt 07 — Logout
Create route `/logout` that clears session completely and redirects to `/login`. Add logout link to base template nav when user is authenticated.

**Test:** `test_logout.py` — authenticated user hits /logout → session empty → redirect to /login.

### Prompt 08 — User Profile CRUD
In `database.py`, add `get_user(id)`, `update_user(id, **fields)` with column whitelist (username, display_name, bio only). Add route `/profile` (self) and `/user/<id>` (public view).

**Test:** `test_user_profile.py` — get_user returns dict; update changes display_name; update ignores password_hash in whitelist.

---

## Phase 2: Core Social (Prompts 9–17)

### Prompt 09 — Post Model
In `database.py`, add `create_post(user_id, content_type, text_content=None, link_url=None, photo_url=None, visibility='friends')`. Content types: `text`, `link`, `photo`. Validate that exactly one content field is populated per type.

**Test:** `test_post_model.py` — create text post returns id; create photo post requires photo_url; create link post validates URL starts with http; empty post rejected.

### Prompt 10 — Create Post Route
Create route `/post/new` (GET/POST) + `templates/create_post.html`. Form has: content_type selector, text textarea (max 2000 chars), link URL input, photo upload input. On POST, create post, redirect to `/feed`. Enforce login_required.

**Test:** `test_create_post.py` — authenticated user can POST text post; anonymous redirected to login; text over 2000 chars rejected.

### Prompt 11 — Feed Engine
In `feed.py`, implement `get_feed(user_id, sort='newest', limit=50, offset=0)` that returns posts from friends only (friendship.status='accepted' in either direction), plus the user's own posts. Exclude posts from blocked users. Support sort by `newest` or `oldest`.

**Test:** `test_feed_engine.py` — user sees own posts; sees friend's posts; does NOT see non-friend's posts; does NOT see blocked user's posts.

### Prompt 12 — Feed Page
Create route `/feed` + `templates/feed.html`. Show paginated feed with post author, timestamp, content, like count, comment count. Infinite scroll or page-number pagination.

**Test:** `test_feed_page.py` — GET /feed returns 200 for authenticated user; HTML contains post content; anonymous user redirected to login.

### Prompt 13 — Friend Request Model
In `database.py`, add `send_friend_request(requester_id, addressee_id)`, `accept_friend_request(id)`, `reject_friend_request(id)`, `get_friendship(user_a, user_b)`. Statuses: `pending`, `accepted`, `rejected`. Prevent duplicate requests between same pair.

**Test:** `test_friendship_model.py` — send request creates pending row; duplicate returns existing id; accept changes status; reject changes status; get_friendship finds bidirectional.

### Prompt 14 — Friend Request Routes
Create routes: `/friend/request/<user_id>` (POST), `/friend/accept/<request_id>` (POST), `/friend/reject/<request_id>` (POST). Add notification area in base template for pending requests.

**Test:** `test_friend_routes.py` — send request creates pending; accept makes friendship; reject removes/deactivates; can't send request to self.

### Prompt 15 — Friend List Page
Create route `/friends` + `templates/friends.html`. Show accepted friends with avatars, display names, and "unfriend" button. Show pending sent requests and pending received requests separately.

**Test:** `test_friends_page.py` — page lists accepted friends; shows pending counts; unfriend removes friendship.

### Prompt 16 — Like System
In `database.py`, add `like_post(user_id, post_id)` and `unlike_post(user_id, post_id)`. Toggle pattern: like if not exists, unlike if exists. Route `/post/<id>/like` (POST).

**Test:** `test_likes.py` — like increments count; second like unlikes; like count correct in feed; can't like own post (optional but nice).

### Prompt 17 — Comment System
In `database.py`, add `add_comment(user_id, post_id, text)` with max 1000 chars. Route `/post/<id>/comment` (POST) and show comments under each post on feed. Include comment count on post card.

**Test:** `test_comments.py` — add comment increases count; text over 1000 chars rejected; comments appear on feed; comment author is correct user.

---

## Phase 3: Media & Personal Pages (Prompts 18–22)

### Prompt 18 — Photo Upload Handler
In `uploads.py`, implement `save_photo(file, user_id)` using `werkzeug.utils.secure_filename`, timestamp prefix, size limit (10 MB), allowed extensions check. Store in `static/uploads/` organized by user_id subfolder. Return relative URL.

**Test:** `test_uploads.py` — valid jpg saves and returns path; oversized file rejected; bad extension rejected; filename is safe (no `../`).

### Prompt 19 — Multi-Format Photo Support
Extend upload handler to accept `jpg`, `jpeg`, `png`, `gif`, `webp`, `heic`. For `heic`, attempt `pillow-heif` conversion to `jpg` if available; if not, reject gracefully. Return standardized extension in stored filename.

**Test:** `test_multi_format.py` — png uploads ok; webp uploads ok; fake extension rejected; heic either converts or rejects gracefully.

### Prompt 20 — Personal Page Creation
Create route `/page/new` and `/page/<id>`. Personal pages are rich-text profiles with: title, bio (markdown-supported), links list, featured photos. Stored in `pages` table (id, user_id, title, slug, content_json, is_public, created_at).

**Test:** `test_pages.py` — create page returns id; slug is URL-safe; page renders title and bio; only owner can edit.

### Prompt 21 — Profile Enhancements
Extend user profile with: avatar upload (crop to 400x400), cover photo upload (max 1200x400), pronouns field, location field. Update `/profile/edit` route and template.

**Test:** `test_profile_enhancements.py` — avatar upload updates avatar_url; cover upload updates cover_url; edit form updates pronouns; profile page shows all fields.

### Prompt 22 — Photo Gallery
Create route `/photos/<user_id>` + `templates/photos.html`. Grid gallery of all photo posts by that user. Click opens lightbox with post details. Support filtering by content type (all photos vs photo posts only).

**Test:** `test_gallery.py` — gallery shows user's photo posts; lightbox data loads via API; empty gallery shows friendly message.

---

## Phase 4: Advanced Features (Prompts 23–27)

### Prompt 23 — Blockchain Audit Log
In `blockchain.py`, implement a hash-chain: each audit_log entry gets `prev_hash` (previous row's `block_hash`) and `block_hash` = SHA-256 of `(prev_hash + table_name + record_id + action + user_id + timestamp + nonce)`. Use `add_block_within_conn(conn, ...)` so block and data insert are atomic. Provide `verify_chain()` that walks all blocks and reports tampered ones.

**Test:** `test_blockchain.py` — creating a post adds audit block; verify_chain passes on clean data; manual tampering of a hash is detected; block links to previous hash.

### Prompt 24 — Agent Automated Moderation
In `moderation.py`, implement keyword + regex pattern filter. Configurable keyword list in `config.py`. Score posts 0-100: < 30 = clean, 30-70 = flagged for review, > 70 = auto-rejected. Log moderation action to audit_log. Route `/moderation/queue` for admin.

**Test:** `test_moderation.py` — clean post passes; flagged post enters queue; rejected post is blocked; keyword match triggers flag.

### Prompt 25 — Human Review Queue
Create route `/admin/moderation` + `templates/moderation_queue.html`. Table of flagged posts with: content preview, score, reason, approve/reject buttons. Admins can override agent decisions. Actions are audit-logged.

**Test:** `test_review_queue.py` — flagged post appears in queue; approve makes it visible in feed; reject hides it; action is in audit log.

### Prompt 26 — Hermes Agent Bridge
In `hermes_bridge.py`, implement a webhook receiver `/hermes/webhook` that accepts JSON: `{action, user_id, post_id, text, timestamp}`. Authenticate with shared secret header `X-Hermes-Secret`. Supported actions: `moderate`, `notify`, `summarize`. The bridge can trigger moderation, send in-app notifications, or generate feed summaries.

**Test:** `test_hermes_bridge.py` — valid secret processes action; invalid secret returns 403; moderate action flags post; notify action creates notification row.

### Prompt 27 — Web Dashboard
Create route `/admin/dashboard` + `templates/dashboard.html`. Show: total users, posts today, pending friend requests, moderation queue size, storage used, recent audit log entries (last 20). Use Chart.js or vanilla JS bar chart for posts-per-day.

**Test:** `test_dashboard.py` — dashboard loads for admin; shows correct user count; shows correct post count; unauthorized user gets 403.

---

## Phase 5: Privacy, Config & Polish (Prompts 28–30)

### Prompt 28 — Privacy-First Model
Implement visibility controls: every post defaults to `friends` (no public option). Users can set per-post visibility: `friends` or `only_me`. Feed engine respects visibility. Profile pages default to friends-only; user can set `pages.is_public = true` for specific pages. No data leaves the server unless explicitly shared.

**Test:** `test_privacy.py` — friends-only post visible to friend, not to non-friend; only_me post visible only to author; public page visible to anonymous; private page requires auth + friendship.

### Prompt 29 — Config Module
Create `config.py` with `Config` dataclass: max_file_size_mb, allowed_photo_extensions, rate_limit_login_attempts, rate_limit_window_seconds, moderation_keywords (list), moderation_regex_patterns (list), hermes_webhook_secret, secret_key, database_path. Load from env vars with sensible defaults. Use `dataclasses.asdict()` for template injection.

**Test:** `test_config.py` — defaults are sensible; env var overrides work; asdict returns all fields; missing required vars raise clear error.

### Prompt 30 — Integration Tests & Packaging
Create `test_integration.py` with a full end-to-end flow:
1. User A signs up and logs in.
2. User B signs up; A sends friend request; B accepts.
3. A creates a text post and a photo post.
4. B sees both in feed.
5. B likes a post and comments.
6. Agent moderation scans — clean posts pass.
7. Blockchain audit log verifies clean.
8. Admin dashboard shows stats.

Add `requirements.txt`, `.gitignore`, `README.md`, and push to GitHub `drwjkirkpatrick-web/mini-social-media` on `main`.

**Test:** `test_integration.py` — full flow passes; `python -m pytest tests/` passes all 30+ test files.

---

## Dependency Table

| Prompt | Depends On | Provides For |
|---|---|---|
| 01 Schema | — | 02, 03, 08, 09, 13, 23 |
| 02 Connection | 01 | 03, 08, 09, 13, 23 |
| 03 Password | — | 05, 06 |
| 04 Session | — | 05, 06, 07, 10, 12 |
| 05 Signup | 01, 02, 03, 04 | 06, 08, 13, 14, 30 |
| 06 Login | 01, 02, 03, 04, 05 | 07, 10, 12, 30 |
| 07 Logout | 04, 06 | — |
| 08 Profile CRUD | 01, 02, 05 | 21 |
| 09 Post Model | 01, 02 | 10, 11, 16, 17, 23, 24 |
| 10 Create Post | 04, 06, 09 | 12, 16, 17, 22, 24, 30 |
| 11 Feed Engine | 01, 02, 09, 13 | 12, 28, 30 |
| 12 Feed Page | 04, 06, 09, 11 | 30 |
| 13 Friend Model | 01, 02 | 11, 14, 15, 28 |
| 14 Friend Routes | 04, 06, 13 | 15, 30 |
| 15 Friends Page | 04, 06, 13, 14 | 30 |
| 16 Likes | 01, 02, 04, 06, 09 | 12, 30 |
| 17 Comments | 01, 02, 04, 06, 09 | 12, 30 |
| 18 Photo Upload | — | 10, 19, 21, 22 |
| 19 Multi-Format | 18 | 10, 22 |
| 20 Personal Page | 01, 02, 04, 06 | 28, 30 |
| 21 Profile Enhance | 08, 18 | 30 |
| 22 Gallery | 04, 06, 09, 18 | 30 |
| 23 Blockchain | 01, 02 | 24, 25, 27, 30 |
| 24 Moderation | 09, 23 | 25, 26, 27, 30 |
| 25 Review Queue | 04, 06, 24 | 30 |
| 26 Hermes Bridge | 04, 06, 24 | 30 |
| 27 Dashboard | 04, 06, 23, 24 | 30 |
| 28 Privacy | 09, 11, 13, 20 | 30 |
| 29 Config | — | ALL (imported everywhere) |
| 30 Integration | ALL | — |

---

## Notes for Builder

- Build Prompt 29 (Config) first — or at least scaffold it — since everything imports it.
- Use atomic blockchain transactions: `add_block_within_conn(conn, ...)` per skill guidance.
- Never use `datetime.utcnow()` — use `datetime.now(timezone.utc)`.
- All user-supplied strings to templates must pass through `html.escape()` or Jinja2 autoescape.
- Photo uploads: `secure_filename` + timestamp prefix + user subfolder.
- Rate limits: in-memory dict with windowed expiry (sufficient for 100 users).
