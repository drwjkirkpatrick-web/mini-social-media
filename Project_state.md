# Project State: mini-social-media

> **Last updated:** 2026-07-28
> **Current phase:** maintenance
> **Overall health:** green

---

## 1. Goal (1–2 sentences)
A privacy-first, friends-only social media platform for ~100 users. Built as a
local Flask app with agent moderation, blockchain audit logging, Hermes agent
bridge, Docker deployment, WebSocket real-time, PWA, quantum-safe passwords,
short video, voice messages, stories, photographer albums, and Hermes AI
integration.

## 2. Current Status
### Done
- [x] v0.1.0: Core platform — 68 tests
- [x] v0.2.0: 30 new modules (events, polls, circles, reactions, etc.) — 95 tests
- [x] v0.3.0: Docker, WebSocket, PWA, Argon2id — 106 tests
- [x] v0.4.0: Video, voice, stories, albums, prompts, ice breakers, reading list,
  wishlist, notes, groups, birthdays, mood, expanded reactions, highlights sort,
  Hermes AI — 119 tests
- [x] GitHub repo created and pushed

### In Progress
- [ ] —

### Not Started
- [ ] PostgreSQL backend for >100 users
- [ ] End-to-end encrypted DMs
- [ ] 2FA with TOTP
- [ ] Federation protocol (ActivityPub)

## 3. Architecture & Key Decisions
| Decision | Rationale | Date |
|---|---|---|
| Flask + SQLite | Local-first, single-machine, zero external deps | 2026-07-28 |
| PBKDF2 → Argon2id | Quantum-safe password hashing | 2026-07-28 |
| Blockchain hash chain | Tamper-evident audit log | 2026-07-28 |
| Agent moderation | Keyword + pattern filter, human review queue | 2026-07-28 |
| Friends-only default | Privacy first — no public post option | 2026-07-28 |
| SocketIO threading async | Avoids eventlet/gevent dependency | 2026-07-28 |
| PWA service worker | Cache-first static + network-first API | 2026-07-28 |
| Docker multi-stage | Non-root user, `uv` for fast install | 2026-07-28 |
| Video ≤29s, voice ≤5min | Small community, local storage | 2026-07-28 |
| Stories 24h expiry | Ephemeral content, auto-purge | 2026-07-28 |

## 4. Blockers & Risks
- None currently.

## 5. Next Step (only ONE)

> **Next:** Commit v0.4.0 and push to GitHub `origin main`.

## 6. Environment & Tooling Notes
- Runtime: Python 3.11, Flask, Werkzeug, SQLite, flask-socketio, argon2-cffi, gunicorn
- Local hosting: `127.0.0.1:9197`
- Docker: `docker compose up --build`
- GitHub: `drwjkirkpatrick-web/mini-social-media`
- Tests: `119 passed` via `.venv/bin/python -m pytest tests/ -v`
- Templates: 42 HTML files
- Database tables: 25+

## 7. Recent Session Log
- 2026-07-28: v0.1.0 built and pushed (68 tests)
- 2026-07-28: v0.2.0 — 30 new modules, 95 tests
- 2026-07-28: v0.3.0 — Docker, WebSocket, PWA, Argon2id, 106 tests
- 2026-07-28: v0.4.0 — Video, voice, stories, albums, expanded reactions,
  highlights sort, Hermes AI, 11 new test files, 119 tests passing

## 8. References
- Prompts v1: `PROMPTS.md` (30 original prompts)
- Prompts v2: `PROMPTS_v2.md` (30 v0.2.0 prompts)
- Prompts v3: `PROMPTS_v3.md` (30 v0.3.0 prompts)
- Prompts v4: `PROMPTS_v4.md` (30 v0.4.0 prompts)
- Repo: https://github.com/drwjkirkpatrick-web/mini-social-media
