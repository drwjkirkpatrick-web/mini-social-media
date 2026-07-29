# Project State: mini-social-media

> **Last updated:** 2026-07-28
> **Current phase:** maintenance
> **Overall health:** green

---

## 1. Goal (1–2 sentences)
A privacy-first, friends-only social media platform for ~100 users. Built as a
local Flask app with agent moderation, blockchain audit logging, and a Hermes
agent bridge.

## 2. Current Status
### Done
- [x] v0.1.0: Core platform (database, auth, posts, feed, friends, likes, comments, photos, pages, blockchain, moderation, dashboard, Hermes bridge)
- [x] v0.2.0: 30 new modules (events, polls, circles, reactions, bookmarks, mentions, DMs, notifications, search, hashtags, discover, mutual friends, analytics, content warnings, export, deactivation, theme, invite links, engaged sort, onboarding, help center, password reset, dark mode, accessibility)
- [x] 95 pytest tests, all passing
- [x] GitHub repo created and pushed

### In Progress
- [ ] —

### Not Started
- [ ] Docker containerization
- [ ] PostgreSQL backend
- [ ] WebSocket real-time notifications
- [ ] Mobile PWA

## 3. Architecture & Key Decisions
| Decision | Rationale | Date |
|---|---|---|
| Flask + SQLite | Local-first, single-machine, zero external deps | 2026-07-28 |
| Werkzeug PBKDF2 | Salted password hashing, industry standard | 2026-07-28 |
| Blockchain hash chain | Tamper-evident audit log for all posts | 2026-07-28 |
| Agent moderation | Keyword + pattern filter, human review queue | 2026-07-28 |
| Friends-only default | Privacy first — no public post option | 2026-07-28 |
| Multi-format photos | jpg, png, gif, webp, heic support | 2026-07-28 |
| Context processor for current_user | Enables theme and nav personalization | 2026-07-28 |

## 4. Blockers & Risks
- None currently.

## 5. Next Step (only ONE)

> **Next:** Commit v0.2.0 and push to GitHub `origin main`.

## 6. Environment & Tooling Notes
- Runtime: Python 3.11, Flask, Werkzeug, SQLite
- Local hosting: `127.0.0.1:9197`
- GitHub: `drwjkirkpatrick-web/mini-social-media`
- Tests: `95 passed` via `.venv/bin/python -m pytest tests/ -v`

## 7. Recent Session Log
- 2026-07-28: v0.1.0 built and pushed (60 files, 68 tests)
- 2026-07-28: v0.2.0 — 30 new modules coded, 22 new test files, 95 tests passing
- 2026-07-28: Dark mode, onboarding, help center, password reset, engaged sort added
- 2026-07-28: README rewritten with Phosphorus personality

## 8. References
- Prompts v1: `PROMPTS.md` (30 original prompts)
- Prompts v2: `PROMPTS_v2.md` (30 new module prompts)
- Repo: https://github.com/drwjkirkpatrick-web/mini-social-media
