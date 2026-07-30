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
smile and friends stay connected. With v0.8.0, the platform is visually stunning,
creatively expressive with meme filters, and locally connected with location-aware
discovery. Because the future is coming — and your data should be ready.

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

### Accuracy & Efficiency (v0.7.0)
- **Feed N+1 Elimination** — `get_feed()` now computes like counts, comment
  counts, and reaction tallies in two SQL queries instead of 3N+2. 50 posts
  are served with ≤ 3 total DB statements. Faster feed, happier Jetson.
- **Prompt Roadmap** — `PROMPTS_v7.md` contains 30 testable accuracy and
  efficiency improvements covering correctness (approval gating, idempotent
  likes, timezone handling, webhook HMAC) and performance (indexes, connection
  reuse, batch inserts, query-count ceilings).

### Visual Themes & Professional Polish (v0.8.0)
- **6 Color Palettes** — Slate (default), Midnight, Ocean, Forest, Sunset,
  Lavender. Each defines `bg-primary`, `bg-secondary`, `bg-card`, `text-primary`,
  `text-secondary`, and `accent` CSS custom properties.
- **8 Background Patterns** — Dots, grid, stripes, waves, hexagons, confetti,
  stars, noise. Composited at low opacity over the theme color.
- **Per-User Theme Persistence** — Theme + pattern stored in DB and applied on
  every page load via `inject_globals`.
- **Auto Dark Mode** — Respects `prefers-color-scheme: dark` on first visit.
- **High Contrast Mode** — Accessibility toggle in settings adds `.high-contrast`
  to `<html>`, forcing visible borders and pure black/white.
- **Font Size Toggle** — A+ / A- controls in footer adjust root font-size
  (12–24px) with `localStorage` persistence.
- **Glassmorphism Navbar** — Sticky position with `backdrop-filter: blur(12px)`.
- **Card Hover Lift** — All cards lift on hover with `translateY(-4px)` and
  enhanced shadow.
- **Toast Notifications** — Auto-dismissing toasts replace page-reload flashes.
- **Skeleton Loading** — CSS shimmer placeholders on feed while content loads.
- **Smooth Page Transitions** — 300ms fade-in on every navigation.
- **Animated Reactions** — Emoji buttons scale-bounce on click.
- **Custom Scrollbar** — Themed to match the active palette.
- **Empty State Illustrations** — Friendly SVG illustrations on all empty lists.
- **Inline Upload Preview** — Thumbnail preview immediately after file selection.
- **Upload Progress Bar** — Linear progress indicator during photo/video/meme
  upload.
- **Pull-to-Refresh** — Mobile gesture on feed container triggers reload.

### Meme Engine & Creative Expression (v0.8.0)
- **8 Built-In Filters** — Vaporwave, Deep Fry, Black & White, Sepia Vintage,
  Neon Glow, Pixelate, Blur Background, Comic Book.
- **Custom Filter Creation** — Users create filters by adjusting CSS filter
  values (brightness, contrast, saturate, hue-rotate, blur, grayscale, sepia,
  invert). Stored in `meme_filters` table.
- **Meme Post Generation** — `/meme/new` accepts a photo + filter + caption,
  saves as a `content_type='meme'` post.
- **Selfie Upload** — `/selfie/upload` stores user's selfie in the users table.
- **Selfie Memes** — `/meme/selfie` composites the user's selfie with a chosen
  filter into a personalized meme post.
- **Meme Gallery** — `/memes` shows a gallery of all meme posts from friends.
  Memes can be shared (repost) with added caption.

### Meme Engine v0.9.0 — Advanced Creative Tools (30 New Features)
Inspired by [memelord.com](https://memelord.com), adapted for privacy-first
local-first communities. No external APIs — all deterministic, all local.

**Templates & Text**
- **12 Classic Meme Templates** — Drake, Distracted Boyfriend, Woman Yelling at
  Cat, Change My Mind, Two Buttons, Expanding Brain, Gal Brain, Stonks, Roll
  Safe, Doge, This Is Fine, Surprised Pikachu. Seeded in `meme_templates` table.
- **Custom Template Creation** — `/meme/template/new` lets users add their own
  templates with name, category, image URL, and dimensions.
- **Template Search** — `/meme/template/search?q=` fuzzy-searches templates by
  name or category.
- **Template Favorites** — `/meme/template/<id>/favorite` toggles a favorite;
  favorited templates appear in the user's shortlist.
- **Top/Bottom Text** — Classic Impact-style top text and bottom text fields on
  meme posts. Stored as `top_text` and `bottom_text` columns on `posts`.
- **Custom Text Color** — `/meme/<id>/text-color` sets the meme text color
  (default white, any hex).
- **Text Rotation** — `text_rotation` column allows tilted meme text (0–360°).
- **Caption Suggestion Bank** — 10 seeded trending tags (`trending`, `classic`,
  `wholesome`, `spicy`, `dark`, `absurdist`, `relatable`, `niche`, `ironic`)
  serve as caption inspiration.

**Stickers & Overlays**
- **8 Built-In SVG Stickers** — Fire, Heart, 100, Crown, Thumbs Up, Skull,
  Clown, Flex. Seeded in `meme_stickers` table.
- **Sticker Placement** — `/meme/<id>/sticker` places stickers on meme posts
  with x/y coordinates, rotation, and scale.
- **User Watermark** — `/meme/<id>/watermark` stamps a custom watermark (e.g.
  `@username`) on meme posts.

**Interactions & Voting**
- **Meme-Specific Emoji Reactions** — `/meme/<id>/react-meme` toggles emoji
  reactions (🔥, ❤️, 😂, etc.) separate from post reactions.
- **Meme Remix Chain** — `/meme/<id>/remix` creates a remix post with
  `meme_remix_of` pointing to the original. Full chain traceable via
  `/meme/remix-chain/<id>`.
- **Upvote/Downvote System** — `/meme/<id>/vote` casts a +1 or -1 vote.
  `meme_votes` table with UNIQUE constraint per user per post.
- **Meme Leaderboard** — `/meme/leaderboard` ranks memes by net vote score
  among friends.

**Organization & Workflow**
- **Meme Collections** — `/meme/collections` lets users organize memes into
  named folders. Add/remove posts from collections.
- **Custom Meme Tags** — `/meme/<id>/tag` tags memes with free-form labels.
  `meme_tags` and `meme_post_tags` tables.
- **Meme Drafts** — `/meme/drafts` lists unfinished memes. Toggle draft status
  via `/meme/<id>/draft`.
- **Meme Scheduling** — `/meme/<id>/schedule` sets a future publish time.
  `list_scheduled_memes()` queries upcoming scheduled memes.

**Variations & Tools**
- **A/B Variant Voting** — `/meme/<id>/ab-variant` creates a variant pair.
  Vote via `/meme/ab/<id>/vote` (choice=a or b). `meme_ab_variants` table.
- **Filter Roulette** — `/meme/filter-roulette` picks a random filter and
  redirects to the meme creation page with it pre-selected.
- **Filter Strength Slider** — `/meme/<id>/filter-strength` sets intensity
  0–100%. `filter_strength` column on `posts`.
- **Before/After Comparison** — `/meme/<id>/compare` shows side-by-side
  original vs filtered meme.
- **Meme Grid Maker** — `/meme/grid` combines multiple photos into a 2×2 or
  3×3 grid meme. `meme_grid_layout` column on `posts`.
- **Custom Text Color Picker** — Full hex color selection for meme text.

**Social & Discovery**
- **Meme of the Day** — `/meme/of-the-day` deterministically selects a meme
  using date + post hash. Same result all day, changes next day.
- **Weekly Meme Challenges** — `/meme/challenges` lists active challenges.
  Create challenges, enter with a meme post. `meme_challenges` and
  `meme_challenge_entries` tables.
- **Meme Stats Page** — `/meme/<id>/stats` shows views, votes, reactions, and
  remix count for a single meme.
- **Meme JSON Export** — `/meme/<id>/export` returns full meme data as JSON
  (post, tags, stickers, reactions).
- **Trending Meme Tags** — `/meme/trending` shows most-used tags in the last
  7 days. `get_trending_meme_tags()` with time-windowed counting.

### Location Awareness & Local Connection (v0.8.0)
- **Location Storage with Privacy Tiers** — `location_general` (text, e.g.
  "Portland, OR"), optional `location_lat`/`location_lng`, and
  `location_precision` (`hidden` | `general` | `precise`).
- **Local Events Discovery** — `/local/events` fuzzy-matches events by general
  location text.
- **Local News Aggregation** — `/local/news` shows community-generated local-news
  posts from friends and friends-of-friends in the same general location.
- **Local Fun & Activities** — `/local/fun` surfaces posts tagged `#localfun` or
  `#thingstodo`.
- **Connect Locally** — `/local/people` lists accepted friends who share the
  same `location_general`.
- **Pseudo-Weather Badge** — Deterministic weather based on location hash +
  day-of-year (Sunny/Cloudy/Rainy/Snowy + temperature range). No external API.

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
| Database | SQLite (WAL mode, 67 tables) |
| Auth | PBKDF2 (legacy) + Argon2id (default, quantum-safe) |
| Photos | Werkzeug secure_filename + timestamp prefix |
| Video/Voice | HTML5 player, ffprobe duration check |
| Moderation | Configurable keyword + regex + Hermes webhook |
| Audit | SHA-256 hash chain with nonce |
| Deployment | Docker + Docker Compose |
| PWA | Web App Manifest + Service Worker |
|| Tests | pytest (252 tests, all passing) |

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
├── PROMPTS_v7.md           # 30 accuracy & efficiency prompts
├── tests/                  # 81 pytest test files
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
- 6 visual themes + 8 background patterns (Slate, Midnight, Ocean, Forest, Sunset, Lavender)
- Meme engine: 8 built-in filters + custom filter creation
- Selfie upload + selfie meme compositing
- Location-aware local hub (events, news, fun, people, weather)
- Privacy-tiered location storage (hidden/general/precise)
- Toast notifications, skeleton loading, glassmorphism navbar
- Card hover lift, animated reactions, custom scrollbar
- Empty-state illustrations, inline upload preview, upload progress bar
- High-contrast mode, font-size toggle, pull-to-refresh (mobile)
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
| **v0.7.0** | Feed N+1 elimination, 30 accuracy & efficiency prompts — correctness (approval gating, idempotent likes, timezone handling, webhook HMAC) and performance (indexes, connection reuse, batch inserts, query-count ceilings) — 252 tests |
| **v0.8.0** | Visual themes (6 palettes + 8 patterns), meme engine (8 filters + custom + selfie memes), location-aware local hub (events, news, fun, people, weather), toast notifications, skeleton loading, glassmorphism navbar, card hover lift, animated reactions, custom scrollbar, empty-state illustrations, inline upload preview, upload progress bar, high-contrast mode, font-size toggle, pull-to-refresh — 30 new prompts, 32 new tests, 284 total |
| **v0.9.0** | Meme engine v2 inspired by memelord.com: 12 classic templates + search + favorites, top/bottom text + Impact font styling + text color + rotation, 8 SVG stickers + placement, watermark, meme-specific emoji reactions, remix chain with attribution, upvote/downvote + leaderboard, meme collections/folders, custom meme tags, meme drafts + scheduling, A/B variant voting, filter roulette, filter strength slider, before/after comparison, meme grid maker (2×2/3×3), meme of the day, weekly challenges, meme stats page, JSON export, trending tags — 30 new prompts, 35 new tests, 319 total |

---

## License

MIT — use it, fork it, run it for your community.

Built with care for small communities who deserve better than surveillance
social media. Your data. Your friends. Your rules.

*"Privacy isn't hiding. It's choosing who sees your light."*
