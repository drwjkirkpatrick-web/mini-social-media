# 🔥 mini-social-media

Welcome to the coziest corner of the internet — a **privacy-first, friends-only
social media platform** built for people who value genuine connection over
algorithmic chaos. No ads. No tracking. No public posts. Just you, your people,
and a space that actually feels like home.

Think of it as your living room online: warm, secure, and yours to customize.
Whether you're sharing a photo from last weekend, organizing a potluck, or just
checking in on friends, this is a place built for *real* community.

---

## What Makes It Sparkle

- **Friends-Only by Default** — Every post is visible only to accepted friends.
  No public option. No algorithmic amplification. Just human connection, the
  way it was meant to be.
- **Emoji Reactions** — Heart, laugh, wow, sad, fire. Express yourself beyond
  the like button.
- **Events & RSVPs** — Plan gatherings, send invites, track who's coming.
  Your community calendar, built right in.
- **Friend Circles** — Create custom groups (Family, Work, Hobby) and share
  posts with exactly the right people.
- **Polls** — Ask questions, get votes, see results. Democracy in action.
- **Bookmarks** — Save posts to revisit later. Your personal highlights reel.
- **@Mentions** — Tag friends in posts and comments. They'll know you thought of them.
- **Direct Messages** — Chat one-on-one with friends. Simple, private, no noise.
- **Notifications Center** — Stay in the loop without getting overwhelmed.
  Mark read, dismiss, filter by type.
- **Search** — Find people, posts, and pages across the platform. Fast and local.
- **Hashtags** — Discover conversations around topics. Click to explore.
- **Discover & Suggested Friends** — Meet new people through mutual connections.
  Spot the newcomers with the "Recently Joined" spotlight.
- **Mutual Friends** — See how you're connected before reaching out. Builds trust.
- **Post Analytics** — Authors see views, reactions, comments, and shares on
  their own content. Knowledge is power.
- **Content Warnings** — Add spoiler/sensitive tags. Viewers choose to reveal.
  Respectful sharing.
- **Pinned Posts** — Pin your best post to the top of your profile.
  Make your first impression count.
- **Post Sharing / Reposting** — Amplify friends' posts with attribution.
  Spread the good stuff.
- **Drafts** — Auto-save as you write. Never lose a thought.
- **Post Scheduling** — Write now, publish later. Plan your content calendar.

### Safety & Trust

- **Agent Moderation** — An automated keyword + pattern filter scores every
  post. Clean posts flow through. Flagged ones land in a human review queue.
  Toxic content never reaches your feed.
- **Blockchain Audit Log** — Every post, like, comment, and moderation action
  is recorded in a tamper-evident hash chain. If anyone tries to edit the
  database behind the scenes, the chain breaks and we know.
- **Hermes Agent Bridge** — Connect your Hermes agent to moderate, notify,
  or summarize activity via a secure webhook. Your AI assistant can help
  run the community.

### Power Features

- **Dark Mode** — Toggle between light and dark themes. Easy on the eyes,
  day or night. Customize your accent color too.
- **Accessibility First** — Skip links, ARIA labels, focus-visible outlines,
  and keyboard navigation throughout. Everyone is welcome.
- **Welcome / Onboarding Flow** — New users get a 4-step wizard: upload avatar,
  write bio, find friends, create first post. Skip anytime.
- **Help Center** — Comprehensive FAQ covering Getting Started, Privacy,
  Moderation, and Account management.
- **Password Reset** — Secure token-based reset. Tokens expire in 1 hour.
- **Theme Customization** — Pick your mode (light/dark) and accent color.
  Your platform, your style.
- **Export Data** — Download all your data as JSON. Portability is a right.
- **Account Deactivation** — Soft-delete anonymizes posts and hides your profile.
  Reactivate anytime by logging back in.
- **Invite Links** — Generate token-based invites with usage limits. Grow your
  community securely.
- **Feed Sort: Most Engaged** — New algorithmic sort that surfaces the posts
  your friends are talking about most. Engagement + recency = relevance.

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
| Backend | Flask + Werkzeug |
| Database | SQLite (WAL mode, foreign keys) |
| Auth | PBKDF2 salted password hashing |
| Photos | Werkzeug secure_filename + timestamp prefix |
| Moderation | Configurable keyword + regex scoring |
| Audit | SHA-256 hash chain with nonce |
| Tests | pytest (95 tests, all passing) |

---

## Architecture

```
mini-social-media/
├── app.py                 # Flask app: routes, auth, uploads, moderation
├── database.py            # SQLite schema (20+ tables) + CRUD functions
├── blockchain.py          # Tamper-evident audit hash chain
├── auth.py                # Password hashing + login decorators
├── config.py              # Environment-based configuration
├── feed.py                # Privacy-aware feed engine (3 sort modes)
├── uploads.py             # Multi-format photo upload handler
├── moderation.py          # Agent moderation scoring
├── templates/              # 25+ Jinja2 HTML templates
├── static/uploads/         # User photo storage
├── tests/                  # 50 pytest test files
├── requirements.txt
├── PROMPTS.md              # 30 original build prompts
├── PROMPTS_v2.md           # 30 new module prompts
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

95 tests covering:
- Database schema, connection layer, CRUD
- Password hashing (PBKDF2)
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

No cookies from third parties. No tracking pixels. No external APIs
unless you configure them.

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

## What's New in v0.2.0

- 30 new modules: Events, Polls, Circles, Reactions, Bookmarks, Mentions,
  DMs, Notifications, Search, Hashtags, Discover, Mutual Friends, Analytics,
  Content Warnings, Export, Deactivation, Theme, Invite Links, and more.
- Dark mode + accent color customization
- Accessibility improvements (skip links, ARIA, focus-visible)
- 4-step welcome onboarding for new users
- Comprehensive Help Center
- Password reset flow
- Engaged feed sort algorithm
- 95 total tests (up from 68)

---

## Roadmap

- [ ] Docker containerization
- [ ] PostgreSQL backend for >100 users
- [ ] WebSocket real-time notifications
- [ ] Mobile-responsive PWA
- [ ] Federation protocol (ActivityPub)
- [ ] End-to-end encrypted DMs
- [ ] 2FA with TOTP
- [ ] Voice messages (no video!)

---

## License

MIT — use it, fork it, run it for your community.

Built with care for small communities who deserve better than surveillance
social media. Your data. Your friends. Your rules.

*"Privacy isn't hiding. It's choosing who sees your light."*
