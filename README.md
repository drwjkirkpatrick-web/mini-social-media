# 🦄 mini-social-media

Welcome to the coziest corner of the internet — a **privacy-first, friends-only
social media platform** built for people who value genuine connection over
algorithmic chaos. No ads. No tracking. No public posts. Just you, your people,
and a space that actually feels like home.

Think of it as your living room online: warm, secure, and yours to customize.
Whether you're sharing a photo from last weekend, organizing a potluck, or just
checking in on friends, this is a place built for *real* community.

Now containerized, real-time, installable on your phone, hardened against
the quantum computing revolution, and packed with features that make photographers
smile and friends stay connected. With v0.6.0, we've added Bluesky-inspired
moderation and discovery tools — custom feeds, content labels, moderation lists,
mute accounts, muted words, starter packs, and reply controls. Because the
future is coming — and your data should be ready.

---

## What Makes It Sparkle

### Core (v0.1.0)
- **Friends-Only by Default** — Every post visible only to accepted friends.
- **Blockchain Audit Log** — SHA-256 hash chain. Tamper-evident.
- **Agent Moderation** — Automated keyword + pattern filter. Human review queue.
- **Hermes Agent Bridge** — Connect your Hermes agent via secure webhook.

### Deep Social (v0.2.0)
- **Events & RSVPs** — Plan gatherings with date, location, attendee tracking.
- **Polls** — Ask questions, vote, see results.
- **Friend Circles** — Create custom groups (Family, Work, Hobby).
- **Emoji Reactions** — Heart ❤️, laugh 😂, wow 😮, sad 😢, fire 🔥, party 🥳,
  peach 🍑, floppy 💾, black heart 🖤, clover ☘️, pray 🙏, tada 🎉, unicorn 🦄,
  heart suit ♥️, sparkles ✨, two hearts 💕. 16 total.
- **Bookmarks, @Mentions, DMs, Notifications, Search, Hashtags**
- **Discover & Mutual Friends** — Meet people through mutual connections.
- **Post Analytics, Content Warnings, Pinned Posts, Sharing, Drafts**
- **Onboarding, Help Center, Password Reset, Theme, Export, Deactivation**

### Infrastructure & Future-Proofing (v0.3.0)
- **Docker Ready** — Multi-stage Dockerfile + `docker-compose.yml`.
- **WebSocket Real-Time** — Live DMs, reactions, notifications, feed injection.
- **Progressive Web App (PWA)** — Install on phone, works offline.
- **Quantum-Safe Passwords** — Argon2id with transparent PBKDF2 migration.

### Media & Creative Expression (v0.4.0)
- **Short Video (≤29 seconds)** — mp4, webm, mov. Inline HTML5 player.
- **Voice Messages** — webm, ogg, mp3, m4a, wav. Inline audio player.
- **Stories / Ephemeral Posts** — 24-hour disappearing posts. View count tracked.
- **Professional Photo Albums** — Grid layout, lightbox with prev/next navigation,
  fullscreen mode, keyboard arrow support. EXIF data display.
- **Daily Prompts** — Admin-set conversation starters to encourage posting.
- **Ice Breakers** — Random question generator for new friends.
- **Reading List** — Share links with personal notes.
- **Wishlist / Gift Registry** — Friends can secretly claim items (surprise mode).
- **Collaborative Notes** — Markdown notes shared with circles, version history.
- **Message Groups** — Multi-person DMs with named groups.
- **Birthday Reminders** — 30-day upcoming birthday tracker.
- **Mood Status** — Set a mood (😊😐😢😠🤩) displayed next to your name.
- **"Chronological with Highlights" Feed Sort** — Newest first, but pins one
  most-engaged post per friend to the top. Best of recency + serendipity.

### Hermes AI Integration (v0.4.0)
- **Connection Encouragement** — Hermes suggests reaching out to friends you
  haven't talked to in a while. One-click action links.
- **Mood Companion** — Reads mood statuses and suggests activities.
- **Photo Curator** — Suggests album groupings and "this day last year" collections.
- **Event Planner** — Suggests events based on friend availability.
- **Moderation Assistant** — Nuanced sentiment/toxicity/spam scoring via webhook.
- **Weekly Community Report** — Natural language summary of community health.

### Health, Growth & Operations (v0.5.0)
- **Expanded Reactions** — 🦄 (unicorn), ♥️ (heart suit), ✨ (sparkles), 💕 (two hearts)
  join the existing 12. 16 total emoji reactions.
- **Admin Disk Usage Dashboard** — `/admin/disk` shows DB size, uploads size,
  file counts, user/post/photo/video/voice totals.
- **Profile Improvements** — Cover photo, bio (500 chars), birthday fields,
  activity graph, posting streaks.
- **Healthy Social Media Achievements** — 13 achievements rewarding wellness:
  `First Steps`, `Social Butterfly`, `Deep Connector`, `Healthy Habit` (7-day streak),
  `Digital Detox Champion` (3+ day break, then return), `Community Builder`,
  `Thoughtful Responder`, `Memory Keeper`, `Storyteller`, `Poll Master`,
  `Helper`, `Verified Human`, `Long-Term Friend`.
- **Stripe Donations (Optional)** — `/donate` with Stripe Checkout. Only active
  if `STRIPE_SECRET_KEY` and `STRIPE_PRICE_ID` are configured.
- **Manual + Auto Backup** — SQLite `.dump` + uploads tar. Admin trigger or nightly.
  Keeps last 7 backups.
- **Easy Logo Swap** — `SITE_LOGO_URL` env var. Drop a new image, restart.
- **Optional Site Motto** — `SITE_MOTTO` env var. Displayed in navbar/footer.
- **Photo-First Feed Sort** — `?sort=photos` — visual posts first, then text.
- **Community Guidelines** — `/guidelines` with acceptance tracking. Required
  before first post.
- **Post Series** — Group related posts into themed collections.
- **Code Optimizations** — Thread-local DB connections, request deduplication cache,
  lazy image loading with IntersectionObserver.

### Bluesky-Inspired Moderation & Discovery (v0.6.0)
- **Custom Feeds** — Create named feeds filtered by hashtag, user, keyword, or
  photos. Pin favorites for quick access. `/custom-feeds`
- **Content Labels** — Self-label posts (sensitive, NSFW, spoiler, violence,
  political, AI-generated). Per-user preferences: show, warn, or hide each
  label type. `/settings/labels`
- **Moderation Lists** — Create shareable block or mute lists. Subscribe to
  community-curated lists to apply bulk moderation in one click. `/modlists`
- **Mute Accounts** — Mute users without blocking. Muted accounts' posts are
  hidden from your feed; they don't know they're muted. `/settings/muted`
- **Muted Words** — Filter specific words, phrases, or hashtags from your feed
  and notifications. Case-insensitive matching. `/settings/muted-words`
- **Starter Packs** — Curated bundles of recommended users. New members can
  follow everyone in a pack with one click — perfect for onboarding. `/packs`
- **Reply Controls** — Post authors choose who can reply: everyone, friends,
  mentioned only, or nobody. Default is `friends`, consistent with the
  friends-only philosophy.

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
| Database | SQLite (WAL mode, 54 tables) |
| Auth | PBKDF2 (legacy) + Argon2id (default, quantum-safe) |
| Photos | Werkzeug secure_filename + timestamp prefix |
| Video/Voice | HTML5 player, ffprobe duration check |
| Moderation | Configurable keyword + regex + Hermes webhook |
| Audit | SHA-256 hash chain with nonce |
| Deployment | Docker + Docker Compose |
| PWA | Web App Manifest + Service Worker |
| Tests | pytest (250 tests, all passing) |

---

## Architecture

```
mini-social-media/
├── app.py                 # Flask app + SocketIO + 127 routes
├── database.py            # SQLite schema (54 tables) + CRUD
├── blockchain.py          # Tamper-evident audit hash chain
├── auth.py                # PBKDF2 + Argon2id hashing
├── config.py              # Environment-based configuration
├── feed.py                # Privacy-aware feed engine (4 sort modes)
├── uploads.py             # Photo, video, voice upload handler
├── moderation.py          # Agent moderation scoring
├── templates/              # 71 Jinja2 HTML templates
├── static/
│   ├── uploads/            # User media storage
│   └── sw.js               # PWA service worker
├── Dockerfile              # Multi-stage build
├── docker-compose.yml      # Compose stack
├── gunicorn.conf.py        # Production server config
├── requirements.txt
├── PROMPTS.md              # 30 original prompts
├── PROMPTS_v2.md           # 30 v0.2.0 prompts
├── PROMPTS_v3.md           # 30 v0.3.0 prompts
├── PROMPTS_v4.md           # 30 v0.4.0 prompts
├── PROMPTS_v5.md           # 30 v0.5.0 prompts
├── tests/                  # 80 pytest test files
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

250 tests covering:
- Database schema, connection layer, CRUD
- Password hashing (PBKDF2 + Argon2id) + transparent migration
- Session management + rate limiting
- Signup / login / logout / onboarding
- Post creation (text, link, photo, video, voice) + content warnings
- Feed engine (5 sort modes: newest, oldest, engaged, highlights, photos)
- Friend requests (send, accept, reject, unfriend)
- Likes + emoji reactions (16 types including 🦄♥️✨💕)
- Comments + @mentions
- Photo uploads (multi-format)
- Personal pages + professional albums
- Events + RSVPs
- Polls + voting
- Friend circles
- Bookmarks
- Direct messages + message groups
- Hashtags + trending
- Search (users, posts, pages)
- Discover + mutual friends
- Stories / ephemeral posts
- Daily prompts + ice breakers
- Reading list + wishlist
- Collaborative notes
- Birthday reminders
- Mood status
- Blockchain audit log
- Agent moderation scoring
- Human review queue
- Hermes webhook bridge
- Admin dashboard + disk usage
- Achievements (13 wellness-focused)
- User activity + streaks
- Backups
- Post series
- Community guidelines
- Custom feeds (hashtag, user, keyword, photo filters)
- Content labels (self-labeling + user preferences)
- Moderation lists (block/mute lists, subscriptions)
- Mute accounts
- Muted words (case-insensitive filtering)
- Starter packs (follow-all bundles)
- Reply controls (everyone/friends/mentioned/nobody)
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
Shor's algorithm and Grover's algorithm threaten *public-key* and *fast hash*
systems. Argon2id's memory hardness cannot be shortcut by quantum parallelism.
Legacy PBKDF2 hashes are transparently re-hashed to Argon2id on next login.

---

## Hermes Agent Bridge

Send a signed POST to `/hermes/webhook`:

```bash
curl -X POST http://localhost:9197/hermes/webhook \\
  -H "X-Hermes-Secret: $MINI_SOCIAL_HERMES_SECRET" \\
  -d '{"action":"notify","user_id":1,"text":"Hello from Hermes!"}'
```

Supported actions: `moderate`, `notify`, `summarize`, `connection_prompt`,
`mood_companion`, `photo_curator`, `event_planner`, `community_report`.

---

## Version History

| Version | Highlights |
|---------|-----------|
| **v0.1.0** | Core platform: auth, posts, feed, friends, likes, comments, photos, pages, blockchain, moderation, dashboard, Hermes bridge |
| **v0.2.0** | 30 new modules: events, polls, circles, reactions, bookmarks, mentions, DMs, notifications, search, hashtags, discover, mutual friends, analytics, content warnings, export, deactivation, theme, invite links, onboarding, help center, password reset, engaged sort |
| **v0.3.0** | Docker, WebSocket real-time, PWA, quantum-safe Argon2id passwords |
| **v0.4.0** | Short video (≤29s), voice messages, stories, professional photo albums, daily prompts, ice breakers, reading list, wishlist, collaborative notes, message groups, birthday reminders, mood status, expanded reactions (🥳🍑💾🖤☘️🙏🎉), "chronological with highlights" feed sort, Hermes AI integration |
| **v0.5.0** | Expanded reactions (🦄♥️✨💕), admin disk usage, profile improvements, 13 healthy-social-media achievements, Stripe donations, backup, logo/motto swap, photo-first sort, community guidelines, post series, code optimizations |
| **v0.6.0** | Bluesky-inspired: custom feeds, content labels, moderation lists, mute accounts, muted words, starter packs, reply controls — 7 new modules, 121 new tests |

---

## License

MIT — use it, fork it, run it for your community.

Built with care for small communities who deserve better than surveillance
social media. Your data. Your friends. Your rules.

*"Privacy isn't hiding. It's choosing who sees your light."*
