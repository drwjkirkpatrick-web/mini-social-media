# Project State: mini-social-media

> **Last updated:** 2026-07-28
> **Current phase:** maintenance
> **Overall health:** green

---

## 1. Goal (1–2 sentences)
A privacy-first, friends-only social media platform for ~100 users. Built as a
local Flask app with agent moderation, blockchain audit logging, Hermes agent
bridge, Docker deployment, WebSocket real-time, PWA, and quantum-safe passwords.

## 2. Current Status
### Done
- [x] v0.1.0: Core platform (database, auth, posts, feed, friends, likes, comments, photos, pages, blockchain, moderation, dashboard, Hermes bridge) — 68 tests
- [x] v0.2.0: 30 new modules — events, polls, circles, reactions, bookmarks, mentions, DMs, notifications, search, hashtags, discover, mutual friends, analytics, content warnings, export, deactivation, theme, invite links, onboarding, help center, password reset, engaged sort — 95 tests
- [x] v0.3.0: Docker (Dockerfile + docker-compose + gunicorn), WebSocket real-time (flask-socketio, live DMs, reactions, notifications), PWA (manifest, service worker, offline page, install prompt), quantum-safe Argon2id passwords with transparent PBKDF2 migration — 106 tests
- [x] GitHub repo created and pushed

### In Progress
- [ ] —

### Not Started
- [ ] PostgreSQL backend for >100 users
- [ ] WebSocket push notifications to background PWA
- [ ] End-to-end encrypted DMs
- [ ] 2FA with TOTP
- [ ] Federation protocol (ActivityPub)
- [ ] Voice messages (no video)

## 3. Architecture & Key Decisions
| Decision | Rationale | Date |
|---|---|---|
| Flask + SQLite | Local-first, single-machine, zero external deps | 2026-07-28 |
| PBKDF2 → Argon2id | Quantum-safe password hashing with transparent migration | 2026-07-28 |
| Blockchain hash chain | Tamper-evident audit log for all posts | 2026-07-28 |
| Agent moderation | Keyword + pattern filter, human review queue | 2026-07-28 |
| Friends-only default | Privacy first — no public post option | 2026-07-28 |
| SocketIO threading async | Avoids eventlet/gevent dependency; works everywhere | 2026-07-28 |
| PWA service worker | Cache-first static + network-first API + offline fallback | 2026-07-28 |
| Docker multi-stage | Non-root user, `uv` for fast install, health checks | 2026-07-28 |

## 4. Blockers & Risks
- None currently.

## 5. Next Step (only ONE)

> **Next:** Commit v0.3.0 and push to GitHub `origin main`.

## 6. Environment & Tooling Notes
- Runtime: Python 3.11, Flask, Werkzeug, SQLite, flask-socketio, argon2-cffi, gunicorn
- Local hosting: `127.0.0.1:9197`
- Docker: `docker compose up --build`
- GitHub: `drwjkirkpatrick-web/mini-social-media`
- Tests: `106 passed` via `.venv/bin/python -m pytest tests/ -v`

## 7. Recent Session Log
- 2026-07-28: v0.1.0 built and pushed (60 files, 68 tests)
- 2026-07-28: v0.2.0 — 30 new modules coded, 22 new test files, 95 tests passing
- 2026-07-28: v0.3.0 — Docker, WebSocket, PWA, Argon2id, 11 new test files, 106 tests passing

## 8. References
- Prompts v1: `PROMPTS.md` (30 original prompts)
- Prompts v2: `PROMPTS_v2.md` (30 v0.2.0 prompts)
- Prompts v3: `PROMPTS_v3.md` (30 v0.3.0 prompts)
- Repo: https://github.com/drwjkirkpatrick-web/mini-social-media
