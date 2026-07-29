# 🔥 mini-social-media

A **privacy-first, friends-only social media platform** built for small
communities of up to ~100 people. No ads. No tracking. No public posts.
Just you, your friends, and a cozy little corner of the internet.

Think of it as your living room online: invite-only, agent-moderated,
blockchain-audited, and yours to customize.

---

## What Makes It Special

- **Friends-Only by Default** — Every post is visible only to accepted
  friends. No public option. No algorithmic amplification. Just human
  connection.
- **Agent Moderation** — An automated keyword + pattern filter scores every
  post. Clean posts flow through. Flagged ones land in a human review queue.
  Toxic content never reaches your feed.
- **Blockchain Audit Log** — Every post, like, comment, and moderation action
  is recorded in a tamper-evident hash chain. If anyone tries to edit the
  database behind the scenes, the chain breaks and we know.
- **Hermes Agent Bridge** — Connect your Hermes agent to moderate, notify,
  or summarize activity via a secure webhook. Your AI assistant can help
  run the community.
- **Customizable Personal Pages** — Create rich-text profile pages with
  photos, links, and bios. Set them friends-only or public, page by page.
- **Multi-Format Photos** — Upload JPG, PNG, GIF, WebP, and HEIC. Files are
  stored locally, organized per user, with safe filename handling.
- **Local Hosting** — Runs on your own machine. SQLite database. No cloud
  dependencies. Your data never leaves the server unless you want it to.

---

## Quick Start

```bash
git clone https://github.com/drwjkirkpatrick-web/mini-social-media.git
cd mini-social-media

# Create a virtual environment
uv venv
uv pip install -r requirements.txt

# Run the server
.venv/bin/python app.py
```

Then open `http://127.0.0.1:9197` in your browser.

Default admin creation (via Python shell):
```python
from database import create_user
from auth import hash_password
create_user("admin", "admin@example.com", hash_password("changeme"), role="admin")
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask + Werkzeug |
| Database | SQLite (WAL mode, foreign keys) |
| Auth | PBKDF2 salted password hashing |
| Photos | Werkzeug secure_filename + timestamp prefix |
| Moderation | Configurable keyword + regex scoring |
| Audit | SHA-256 hash chain with nonce |
| Tests | pytest (68 tests, all passing) |

---

## Architecture

```
mini-social-media/
├── app.py                 # Flask app: routes, auth, uploads, moderation
├── database.py            # SQLite schema + CRUD functions
├── blockchain.py          # Tamper-evident audit hash chain
├── auth.py                # Password hashing + login decorators
├── config.py              # Environment-based configuration
├── feed.py                # Privacy-aware feed engine
├── uploads.py              # Multi-format photo upload handler
├── moderation.py           # Agent moderation scoring
├── templates/              # Jinja2 HTML templates
├── static/uploads/         # User photo storage
├── tests/                  # 68 pytest test files
├── requirements.txt
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

68 tests covering:
- Database schema, connection layer, CRUD
- Password hashing (PBKDF2)
- Session management + rate limiting
- Signup / login / logout
- Post creation (text, link, photo)
- Feed engine (friends-only privacy)
- Friend requests (send, accept, reject, unfriend)
- Likes + comments
- Photo uploads (multi-format)
- Personal pages
- Blockchain audit log
- Agent moderation scoring
- Human review queue
- Hermes webhook bridge
- Admin dashboard
- Privacy model
- Full end-to-end integration flow

---

## Privacy Model

| Feature | Default | Override |
|---------|---------|----------|
| Post visibility | Friends only | Per-post: "Only me" |
| Personal page visibility | Friends only | Per-page: Public |
| Profile viewing | Friends only | — |
| Data storage | Local server only | — |
| Analytics | None | — |

No cookies from third parties. No tracking pixels. No external APIs
unless you configure them.

---

## Hermes Agent Bridge

Send a signed POST to `/hermes/webhook`:

```bash
curl -X POST http://localhost:9197/hermes/webhook \
  -H "X-Hermes-Secret: $MINI_SOCIAL_HERMES_SECRET" \
  -d '{"action":"notify","user_id":1,"text":"Hello from Hermes!"}'
```

Supported actions: `moderate`, `notify`, `summarize`.

---

## Roadmap

- [ ] Docker containerization
- [ ] PostgreSQL backend for >100 users
- [ ] WebSocket real-time notifications
- [ ] Mobile-responsive PWA
- [ ] Federation protocol (ActivityPub)
- [ ] End-to-end encrypted DMs

---

## License

MIT — use it, fork it, run it for your community.

Built with care for small communities who deserve better than surveillance
social media.
