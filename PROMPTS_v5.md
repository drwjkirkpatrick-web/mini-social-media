# mini-social-media — 30 New Module Prompts (v0.5.0)

> New emojis, admin tooling, profile glow-up, healthy-social-media achievements,
> Stripe donations, code optimizations, backup, branding, photo-first sort.

---

## Wave 1: Reactions + Admin + Profile

1. **New Emoji Reactions** — Add 🦄 (unicorn), ♥️ (heart_suit), ✨ (sparkles),
   💕 (two_hearts), 🔥 (fire — already exists). 9 total new emojis in the
   reaction bar. Update feed.html reaction forms and all reaction count logic.

2. **Admin Disk Usage Dashboard** — `/admin/disk` shows: SQLite DB size,
   uploads/ directory size, number of files, total users, total posts,
   total photos/videos/voice. Only accessible to `role='admin'`.

3. **Profile Cover Photo** — Users can upload a cover image for their profile
   page. Stored in `users.cover_url`. Displayed as full-width banner.

4. **Profile Bio / About** — Markdown-supported bio field on user profile.
   `users.bio TEXT`. Rendered safely (bleach or escape). Max 500 chars.

5. **Profile Activity Graph** — GitHub-style contribution graph showing days
   with posts over the last year. `user_activity` table tracks daily post counts.

6. **Post Streaks** — Consecutive days of posting. Display current streak on
   profile. Encourages healthy daily engagement without addiction mechanics.

## Wave 2: Achievements (Healthy Social Media)

7. **Achievements Schema** — `achievements` table (id, slug, name, description,
   icon, category, threshold). `user_achievements` (user_id, achievement_id,
   unlocked_at, is_seen).

8. **Achievement: "First Steps"** — Create your first post.

9. **Achievement: "Social Butterfly"** — Accept 10 friend requests.

10. **Achievement: "Deep Connector"** — Send 50 direct messages.

11. **Achievement: "Healthy Habit"** — Post on 7 consecutive days (streak).

12. **Achievement: "Digital Detox Champion"** — Take a 3+ day break, then return
    and post. Rewards healthy boundaries, not addiction.

13. **Achievement: "Community Builder"** — Create an event with 5+ RSVPs.

14. **Achievement: "Thoughtful Responder"** — Comment on 20 different friends'
    posts. Rewards quality interaction over volume.

15. **Achievement: "Memory Keeper"** — Create 3 photo albums.

16. **Achievement: "Storyteller"** — Publish 10 ephemeral stories.

17. **Achievement: "Poll Master"** — Create 5 polls receiving 10+ votes each.

18. **Achievement: "Helper"** — Answer 10 daily prompts or ice breakers.

19. **Achievement: "Verified Human"** — Complete onboarding + fill bio +
    upload avatar + set birthday.

20. **Achievement: "Long-Term Friend"** — Reach a 1-year friend-versary.

## Wave 3: Monetization + Operations

21. **Stripe Donations (Optional)** — `/donate` page with Stripe Checkout
    session. Configurable product name, price, success/cancel URLs. Only enabled
    if `STRIPE_SECRET_KEY` and `STRIPE_PRICE_ID` are set.

22. **Manual Database Backup** — Admin `/admin/backup` triggers SQLite `.dump`
    + `tar` of uploads/ into `backups/YYYY-MM-DD_HH-MM/`. Download link.

23. **Auto-Backup Cron** — Nightly `.dump` + uploads tar to `backups/`.
    Keeps last 7 backups, auto-deletes older.

24. **Logo Swap** — `SITE_LOGO_URL` env var. Defaults to `/static/logo.png`.
    Easy to replace by dropping a new file.

25. **Site Motto** — `SITE_MOTTO` env var. Displayed in navbar or footer.
    Optional; hidden if unset.

## Wave 4: Feed + Performance

26. **Photo-First Feed Sort** — `?sort=photos` — all photo/video posts first
    (newest within that group), then text/link posts. Great for visual browsing.

27. **Request Deduplication Cache** — In-memory LRU cache for identical feed
    queries within 5 seconds. Reduces DB load for popular pages.

28. **Connection Pool** — Thread-local SQLite connections. Prevents
    "database locked" under concurrent load.

29. **Lazy Image Loading** — `loading="lazy"` + IntersectionObserver on feed
    images. Faster initial page load, lower bandwidth.

30. **Community Guidelines** — `/guidelines` page with built-in rules.
    Track `users.accepted_guidelines_at`. Required before first post.
