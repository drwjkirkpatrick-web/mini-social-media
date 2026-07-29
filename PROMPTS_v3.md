# mini-social-media — 30 New Module Prompts (v0.3.0)

> Docker, WebSocket real-time, mobile PWA, quantum-safe passwords, and
> infrastructure hardening.

---

## Infrastructure & Deployment

01. **Dockerfile** — Multi-stage Docker image for Python 3.11+Flask+SQLite.
    Lightweight, non-root user, `uv` for fast installs, `EXPOSE 9197`.

02. **docker-compose.yml** — Single service with volume mounts for `data/` and
    `static/uploads/`. Health check via HTTP `GET /`. Restart policy `unless-stopped`.

03. **.dockerignore** — Exclude venv, __pycache__, .git, tests, .db files.

04. **Production gunicorn runner** — `gunicorn -w 4 -b 0.0.0.0:9197` with
    `preload_app` for faster startup. Graceful worker timeout.

05. **Environment config validation** — On startup, assert required env vars
    present. Warn if `FLASK_DEBUG=1` in production. Print config summary.

06. **Health check endpoint** — `GET /health` returns JSON `{"status":"ok", "db":"connected", "version":"0.3.0"}`.
    Used by Docker `HEALTHCHECK` and monitoring.

07. **SQLite WAL mode in Docker** — Ensure WAL journal_mode in containerized
    environment. WAL works fine on bind mounts.

08. **Docker build test** — Verify `docker build` succeeds and container starts
    within 30 seconds.

---

## WebSocket Real-Time (Flask-SocketIO)

09. **SocketIO server setup** — Install `flask-socketio`. Integrate into app.py
    without breaking existing Flask routes. Monkey-patch eventlet/gevent only
    if needed; fallback to threading async_mode.

10. **Real-time notifications** — When a post gets a like, comment, mention,
    share, or friend request, emit `notification` event to recipient's SocketIO
    room (room = `user_{id}`).

11. **Live DM chat** — `message_thread.html` upgrades to SocketIO: typing
    indicators, live message delivery, read receipts update in real time.

12. **Live reaction updates** — When someone reacts to a post, all viewers of
    that post see the reaction count update instantly via `reaction_update` event.

13. **Live feed injection** — New approved posts from friends appear at top of
    feed in real time via `new_post` event. Badge counter increments.

14. **SocketIO auth middleware** — Only authenticated users connect. Reject
    anonymous connections. Rooms scoped by user_id.

15. **SocketIO rate limiting** — Max 50 emits per minute per socket. Disconnect
    spammers. Log to blockchain.

---

## Mobile Progressive Web App (PWA)

16. **Web App Manifest** — `manifest.json`: name, short_name, icons, theme_color,
    background_color, display `standalone`, start_url `/feed`.

17. **Service Worker** — `sw.js`: cache-first strategy for static assets,
    network-first for API calls. Offline fallback page.

18. **Install prompt support** — `beforeinstallprompt` event capture. Custom
    "Add to Home Screen" banner in base template.

19. **Mobile-responsive CSS overhaul** — Touch-friendly buttons (>=44px tap
    targets), bottom navigation bar on mobile, swipe gestures for feed,
    pull-to-refresh, safe-area-inset support for notches.

20. **Offline page** — `offline.html`: cached in service worker. Shows cached
    feed posts when network unavailable. Sync indicator.

21. **Push notifications** — Use the Notifications API (non-SocketIO fallback).
    Browser asks permission. Shows native notification on new friend request
    or mention when PWA is backgrounded.

22. **Theme-aware splash screen** — Use `theme-color` meta tag + manifest
    background color so iOS/Android show correct color on launch.

23. **PWA Lighthouse audit** — Verify 90+ score on PWA, Accessibility, Best
    Practices categories.

---

## Quantum-Safe Passwords

24. **Argon2id hashing option** — Install `argon2-cffi`. Support both PBKDF2
    (legacy) and Argon2id (modern, memory-hard, quantum-safe). Auto-detect
    hash prefix (`$argon2id$` vs `pbkdf2:sha256:`) at verify time.

25. **Argon2id migration prompt** — On login, if password hash uses PBKDF2,
    transparently re-hash to Argon2id and update DB. User never notices.

26. **Quantum-safe rationale docs** — Comment in `auth.py` explaining why
    Argon2id is post-quantum resilient (relies on symmetric hashing + memory
    hardness, not public-key crypto vulnerable to Shor's algorithm).

27. **Argon2id parameter tuning** — Time cost=3, memory cost=65536 KiB,
    parallelism=1. Suitable for Jetson / small servers.

28. **Hash strength audit endpoint** — `GET /health/passwords` (admin only)
    returns count of PBKDF2 vs Argon2id hashes. Tracks migration progress.

---

## Cross-Cutting

29. **WebSocket + PWA integration** — Service worker connects to SocketIO
    when online. Offline queue stores unsent DMs; syncs on reconnect.

30. **End-to-end smoke test** — Docker build → container up → WebSocket
    connection → PWA manifest loads → Argon2id signup → real-time notification
    → offline page cached. One script validates the full stack.
