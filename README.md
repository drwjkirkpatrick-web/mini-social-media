# 🔥 mini-social-media

Welcome to the coziest corner of the internet — a **privacy-first, friends-only
social media platform** built for people who value genuine connection over
algorithmic chaos. No ads. No tracking. No public posts. Just you, your people,
and a space that actually feels like home.

Think of it as your living room online: warm, secure, and yours to customize.
Whether you're sharing a photo from last weekend, organizing a potluck, or just
checking in on friends, this is a place built for *real* community.

Now containerized, real-time, installable on your phone, and hardened against
the quantum computing revolution. Because the future is coming — and your data
should be ready.

---

## What Makes It Sparkle

### Core (v0.1.0)
- **Friends-Only by Default** — Every post visible only to accepted friends.
- **Blockchain Audit Log** — SHA-256 hash chain. Tamper-evident. Try to edit
  the database behind the scenes? The chain breaks and we know.
- **Agent Moderation** — Automated keyword + pattern filter. Clean posts pass.
  Flagged ones hit a human review queue. Toxic content never reaches your feed.
- **Hermes Agent Bridge** — Connect your Hermes agent via secure webhook.
  Moderate, notify, summarize. Your AI assistant helps run the community.

### Deep Social (v0.2.0)
- **Events & RSVPs** — Plan gatherings with date, location, attendee tracking.
- **Polls** — Ask questions, vote, see results. Democracy in microcosm.
- **Friend Circles** — Create custom groups (Family, Work, Hobby) and share
  posts with exactly the right people.
- **Emoji Reactions** — Heart ❤️, laugh 😂, wow 😮, sad 😢, fire 🔥.
- **Bookmarks** — Save posts to revisit later.
- **@Mentions** — Tag friends in posts and comments.
- **Direct Messages** — Friends-only chat. Block-aware.
- **Notifications Center** — Badge counts, mark read, filter by type.
- **Search** — Users, posts, pages. Fast and local.
- **Hashtags** — Discover conversations around topics.
- **Discover & Mutual Friends** — Meet people through mutual connections.
- **Post Analytics** — Author-only views, reactions, comments, shares.
- **Content Warnings** — Spoiler tags with click-to-reveal.
- **Onboarding, Help Center, Password Reset, Theme, Export, Deactivation**

### Infrastructure & Future-Proofing (v0.3.0)
- **Docker Ready** — Multi-stage Dockerfile + `docker-compose.yml`. Non-root
  user, `uv` for fast installs, health checks, `gunicorn` with 4 workers.
  `docker compose up` and you're live.
- **WebSocket Real-Time** — `flask-socketio` with `threading` async mode.
  Live DM delivery with typing indicators. Real-time notification pushes.
  Reactions update instantly for all viewers. New posts appear at feed top
  live. Auth-gated connections only.
- **Progressive Web App (PWA)** — `manifest.json`, `service-worker.js` with
  cache-first static + network-first API strategy. Offline fallback page.
  Push notification permission. Install prompt support. Theme-aware splash
  screen. Works offline when network drops.
- **Quantum-Safe Passwords** — Argon2id (memory-hard, 65 MB per hash, 3
  iterations, parallelism=1). Transparently migrates PBKDF2 hashes on next
  login. Because post-quantum security starts with the passwords you store
  today.

---

## Quick Start

### Local (development)
```bash
git clone https://github.com/drwjkirkpatrick-web/mini-social-media.git
cd mini-social-media
uv venv
uv pip install -r requirements.txt
.venv/bin/python app.py
# Open http://127.0.0.1:9197
```

### Docker (production)
```bash
docker compose up --build
# Open http://localhost:9197
```

**First time?** Click "First time here?" on the login page for a guided tour.

**Default admin creation** (via Python shell):
```python
from database import create_user
from auth import hash_password
create_user("admin", "admin@example.com", hash_password("changeme"), role="admin")
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask + Werkzeug + Gunicorn |
| Real-Time | Flask-SocketIO (threading async) |
| Database | SQLite (WAL mode, foreign keys) |
| Auth | PBKDF2 (legacy) + Argon2id (default, quantum-safe) |
| Photos | Werkzeug secure_filename + timestamp prefix |
| Moderation | Configurable keyword + regex scoring |
| Audit | SHA-256 hash chain with nonce |
| Deployment | Docker + Docker Compose |
| PWA | Web App Manifest + Service Worker |
| Tests | pytest (106 tests, all passing) |

---

## Architecture

```
mini-social-media/
├── app.py                 # Flask app + SocketIO + 80+ routes
├── database.py            # SQLite schema (20+ tables) + CRUD
├── blockchain.py          # Tamper-evident audit hash chain
├── auth.py                # PBKDF2 + Argon2id hashing
├── config.py              # Environment-based configuration
├── feed.py                # Privacy-aware feed engine (3 sort modes)
├── uploads.py             # Multi-format photo upload handler
├── moderation.py          # Agent moderation scoring
├── templates/              # 27 Jinja2 HTML templates
├── static/
│   ├── uploads/            # User photo storage
│   └── sw.js               # PWA service worker
├── Dockerfile              # Multi-stage build
├── docker-compose.yml      # Compose stack
├── gunicorn.conf.py        # Production server config
├── requirements.txt
├── PROMPTS.md              # 30 original prompts
├── PROMPTS_v2.md           # 30 v0.2.0 prompts
├── PROMPTS_v3.md           # 30 v0.3.0 prompts
├── tests/                  # 53 pytest test files
└── README.md
```

---

## Configuration

All settings load from environment variables with sensible defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MINI_SOCIAL_DB` | `data/social.db` | SQLite path |
| `MINI_SOCIAL_SECRET` | random 32 bytes | Flask session key |
| `MINI_SOCIAL_HERMES_SECRET` | `change-me-in-production` | Webhook auth |
| `MINI_SOCIAL_MAX_FILE_MB` | `10` | Photo upload limit |
| `MINI_SOCIAL_MOD_KEYWORDS` | `spam,scam,hate,...` | Moderation keywords |
| `PORT` | `9197` | Server port |
| `FLASK_DEBUG` | `0` | Debug mode (never in prod) |

---

## Running Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

106 tests covering:
- Database schema, connection layer, CRUD
- Password hashing (PBKDF2 + Argon2id) + transparent migration
- Session management + rate limiting
- Signup / login / logout / onboarding
- Post creation (text, link, photo) + content warnings
- Feed engine (3 sort modes: newest, oldest, engaged)
- Friend requests (send, accept, reject, unfriend)
- Likes + emoji reactions
- Comments + @mentions
- Photo uploads (multi-format)
- Personal pages
- Events + RSVPs
- Polls + voting
- Friend circles
- Bookmarks
- Direct messages
- Hashtags + trending
- Search (users, posts, pages)
- Discover + mutual friends
- Blockchain audit log
- Agent moderation scoring
- Human review queue
- Hermes webhook bridge
- Admin dashboard
- Privacy model
- Password reset
- Theme customization
- Data export
- Account deactivation
- Invite links
- Health check + password hash audit
- PWA manifest + service worker
- Docker file presence
- Full end-to-end integration flow

---

## Privacy Model

| Feature | Default | Override |
|---------|---------|----------|
| Post visibility | Friends only | Per-post: "Only me" |
| Personal page visibility | Friends only | Per-page: Public |
| Profile viewing | Friends only | — |
| DM access | Friends only | — |
| Data storage | Local server only | — |
| Analytics | None (author-only stats) | — |
| Password hashes | Argon2id (quantum-safe) | Auto-migrated from PBKDF2 |

No cookies from third parties. No tracking pixels. No external APIs
unless you configure them.

---

## Quantum-Safe Passwords

We use **Argon2id** (memory-hard, 65 MB per hash) instead of PBKDF2.
Why does this matter for quantum safety? Shor's algorithm and Grover's
algorithm threaten *public-key* and *fast hash* systems. Argon2id's
memory hardness cannot be shortcut by quantum parallelism. Even when
quantum computers crack RSA and ECC, your Argon2id hashes remain
computationally expensive to reverse.

Legacy PBKDF2 hashes are transparently re-hashed to Argon2id on next login.
No user action required. Check migration progress at the admin-only
`/health/passwords` endpoint.

---

## Hermes Agent Bridge

Send a signed POST to `/hermes/webhook`:

```bash
curl -X POST http://localhost:9197/hermes/webhook \\
  -H "X-Hermes-Secret: $MINI_SOCIAL_HERMES_SECRET" \\
  -d '{"action":"notify","user_id":1,"text":"Hello from Hermes!"}'
```

Supported actions: `moderate`, `notify`, `summarize`.

---

## Docker

```bash
# Build and run
docker compose up --build

# Scale workers (edit gunicorn.conf.py)
docker compose restart

# Check health
curl http://localhost:9197/health
```

The Dockerfile uses a non-root `appuser`, multi-stage build with `uv`,
and a health check that polls the `/health` endpoint every 30 seconds.

---

## PWA: Install on Your Phone

1. Open the site in Chrome / Safari / Firefox
2. Tap "Add to Home Screen" (or accept the prompt banner)
3. The app launches standalone — no browser chrome
4. Works offline: cached pages, offline fallback, sync on reconnect

---

## WebSocket Real-Time

Connect to `ws://localhost:9197/socket.io/` with auth session. Events:
- `new_message` — incoming DM
- `new_like` — someone liked your post
- `new_comment` — someone commented on your post
- `new_post` — friend published a new post
- `reaction_update` — reaction count changed on a post you're viewing

---

## Version History

| Version | Highlights |
|---------|-----------|
| **v0.1.0** | Core platform: auth, posts, feed, friends, likes, comments, photos, pages, blockchain, moderation, dashboard, Hermes bridge |
| **v0.2.0** | 30 new modules: events, polls, circles, reactions, bookmarks, mentions, DMs, notifications, search, hashtags, discover, mutual friends, analytics, content warnings, export, deactivation, theme, invite links, onboarding, help center, password reset, engaged sort |
| **v0.3.0** | Docker, WebSocket real-time, PWA, quantum-safe Argon2id passwords, health checks, service worker, offline support |

---

## Roadmap

- [ ] PostgreSQL backend for >100 users
- [ ] WebSocket push notifications to background PWA
- [ ] End-to-end encrypted DMs
- [ ] 2FA with TOTP
- [ ] Federation protocol (ActivityPub)
- [ ] Voice messages (still no video!)

---

## License

MIT — use it, fork it, run it for your community.

Built with care for small communities who deserve better than surveillance
social media. Your data. Your friends. Your rules.

*"Privacy isn't hiding. It's choosing who sees your light."*
