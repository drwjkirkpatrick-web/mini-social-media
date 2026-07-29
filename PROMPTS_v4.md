# mini-social-media — 30 New Module Prompts (v0.4.0)

> New reactions, short video, voice messages, feed sorts, photographer tools,
> social connection helpers, Hermes integration, stories, and community features.

---

## Media & Reactions

01. **Expanded emoji reactions** — Add 🥳🍑💾🖤☘️🙏🎉 to the reaction bar.
    Update database, templates, and feed display.

02. **Custom reaction upload** — Users can upload a 64x64 PNG as a custom emoji.
    Stored in static/uploads/reactions/. Max 5 custom per user.

03. **GIF search & insert** — Integrate with Giphy or Tenor API (or local
    keyword-to-GIF mapping). Insert GIFs into posts and DMs.

04. **Short video module (≤29 seconds)** — Accept mp4/webm/mov. Use ffprobe
    (if installed) to verify duration, else fall back to 30 MB size cap.
    Thumbnail generation via ffmpeg. Stored in static/uploads/videos/.
    Special `content_type='video'` with `video_url` and `video_thumb_url`.

05. **Voice messages** — Accept webm/ogg/mp3/m4a. Max 5 minutes, 10 MB.
    Inline audio player in DMs and posts. `content_type='voice'`.
    Visual waveform placeholder.

---

## Feed & Content

06. **"Chronological with highlights" feed sort** — Newest first, but pins one
    "highlight" per day (most engaged post from friends) to the top.
    Best of both worlds: recency + serendipity.

07. **Stories / ephemeral posts** — 24-hour disappearing posts. `content_type='story'`.
    Auto-purge via cron or lazy cleanup. View count tracked. No likes/comments.
    Tap-to-advance UI.

08. **Post templates** — Recipe, travel, review formats. Structured fields
    (title, ingredients, rating, location) rendered with custom CSS.

09. **Daily prompt / conversation starter** — Admin sets a daily question.
    Banner on feed. Encourages posting. Stored in `daily_prompts` table.

10. **Mood status / feeling tracker** — Users set a mood (😊😐😢😠🤩) on their
    profile. Displayed next to name in feed and DMs. Changes reset daily.

---

## Photographer & Album Tools

11. **Professional photo album view** — Grid layout (2-3 columns), lightbox
    overlay with prev/next navigation. Fullscreen mode. Keyboard arrows.

12. **Photo collage / grid post** — Upload 2-9 photos arranged in a grid.
    Single post with multiple `photo_url` entries. Masonry or square grid.

13. **Watermark / photographer credit** — Optional text watermark overlay
    on uploaded photos (e.g., "© Username"). Configurable in settings.

14. **EXIF data display** — Parse EXIF from uploaded photos. Show camera,
    lens, aperture, shutter, ISO on photo detail page. Optional privacy toggle.

15. **Before/after slider** — Special post format: two photos with a draggable
    slider overlay. Great for photography transformations.

---

## Social Connection & Community

16. **Birthday reminders** — Users set birthday (month/day, year optional).
    Daily cron checks. Notifications to friends 7 days and 1 day before.

17. **Friend-versary tracker** — Celebrate friendship anniversaries.
    Notification on the yearly anniversary of becoming friends.

18. **Ice breaker questions** — Random question generator for new friends.
    "What's your favorite childhood memory?" etc. Stored in `ice_breakers`.

19. **Shared availability / calendar** — Users mark free times. Friends can
    see overlapping availability. No external calendar integration — purely local.

20. **Gift registry / wishlist** — Users add items (name, link, price, priority).
    Friends can "claim" items without the user knowing (surprise mode).

21. **Collaborative notes / docs** — Simple markdown notes shared with circles.
    Edit history tracked. No real-time collaboration (simplicity).

22. **Reading list / article sharing** — Share links with personal notes.
    Friends can see your reading list. Extract title/description automatically.

23. **Group chat / multi-person DMs** — Create named groups with 3+ friends.
    Messages table extended with `group_id`. Group admin can rename/kick.

24. **Weekly friend activity digest** — Email-style summary of what friends
    posted, liked, commented. Delivered as a notification or in-app digest page.

---

## Hermes & AI Integration

25. **Hermes connection encouragement** — Daily Hermes webhook sends
    personalized prompts: "You haven't talked to Sarah in 2 weeks — send a message!"
    Tracks interaction gaps. Actionable one-click reply links.

26. **Hermes mood companion** — Hermes reads mood statuses and suggests
    activities: "You're feeling 😢 — here's a photo from a happy memory."
    Or suggests friends with matching moods.

27. **Hermes photo curator** — Hermes analyzes photo uploads (via EXIF + tags)
    and suggests album groupings, best-of collections, or "this day last year".

28. **Hermes event planner** — Hermes suggests events based on friend
    availability, weather, and past attendance patterns. "Looks like 5 friends
    are free Saturday — plan a hike?"

29. **Hermes content moderator assistant** — Beyond keyword scanning:
    Hermes receives post content via webhook and returns nuanced moderation
    scores (sentiment, toxicity, spam probability). Human still decides.

30. **Hermes weekly community report** — Admin dashboard addition: Hermes
    summarizes community health (post velocity, friend growth, mod queue backlog)
    in natural language. Actionable recommendations.
