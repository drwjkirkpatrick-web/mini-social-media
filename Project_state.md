# Project State: mini-social-media

> **Last updated:** 2026-07-28
> **Current phase:** planning
> **Overall health:** green

---

## 1. Goal (1–2 sentences)
A privacy-first, friends-only social media platform for ~100 users. Built as a
local Flask app with agent moderation, blockchain audit logging, and a Hermes
agent bridge.

## 2. Current Status
### Done
- [x] Project directory created at `~/projects/mini-social-media/`
- [x] 30 testable build prompts drafted in `PROMPTS.md`

### In Progress
- [ ] Phase 1: Foundation (database, auth, signup)

### Not Started
- [ ] Phase 2: Core Social (posts, feed, friends)
- [ ] Phase 3: Media & Pages (photos, personal pages)
- [ ] Phase 4: Advanced (moderation, blockchain, Hermes bridge, dashboard)
- [ ] Phase 5: Polish (tests, README, GitHub repo)

## 3. Architecture & Key Decisions
| Decision | Rationale | Date |
|---|---|---|
| Flask + SQLite | Local-first, single-machine, zero external deps | 2026-07-28 |
| Werkzeug PBKDF2 | Salted password hashing, industry standard | 2026-07-28 |
| Blockchain hash chain | Tamper-evident audit log for all posts | 2026-07-28 |
| Agent moderation | Keyword + pattern filter, human review queue | 2026-07-28 |
| Friends-only default | Privacy first — no public post option | 2026-07-28 |
| Multi-format photos | jpg, png, gif, webp, heic support | 2026-07-28 |

## 4. Blockers & Risks
- **Risk:** Blockchain logging must be atomic with data insert (per skill: add_block_within_conn)
- **Risk:** Photo uploads need secure filename + size limits
- **Risk:** Agent moderation false-positives — needs human review queue

## 5. Next Step (only ONE)

> **Next:** Create `PROMPTS.md` with 30 testable build prompts, then begin Phase 1.

## 6. Environment & Tooling Notes
- Runtime: Python 3.11, Flask, Werkzeug, SQLite
- Local hosting: `127.0.0.1:9197` (next available port after 9196)
- GitHub: `drwjkirkpatrick-web/mini-social-media`

## 7. Recent Session Log
- 2026-07-28: Project conceived; skills loaded; planning phase started.

## 8. References
- Plan: `.hermes/plans/2026-07-28_mini-social-media.md` (TBD)
- Prompts: `PROMPTS.md`
