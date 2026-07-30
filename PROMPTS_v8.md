# mini-social-media — 30 Visual, Meme & Locality Prompts (v0.8.0)

> Target: make the platform visually stunning, creatively expressive with meme
> filters, and locally connected. Every prompt includes a measurable claim and
> at least one automated test that proves the claim.

---

## Visual Themes (Professional Polish)

1. **Custom background color palettes.** Add 6 curated palettes (Midnight,
   Ocean, Forest, Sunset, Lavender, Slate) stored as CSS custom properties.
   Each palette defines `--bg-primary`, `--bg-secondary`, `--bg-card`,
   `--text-primary`, `--text-secondary`, `--accent`. Apply via `data-theme`
   attribute on `<html>`. Test: switching theme changes computed
   `background-color` of `<body>`.

2. **Background pattern overlay system.** Add 8 SVG patterns (dots, grid,
   stripes, waves, hexagons, confetti, stars, noise) applied as a
   `background-image` on `<body>` at 5% opacity. Patterns are composited over
   the theme color. Test: each pattern class renders a non-empty `background-image`
   on body.

3. **Per-user theme persistence.** Store `theme` and `pattern` in the users
   table. Apply on every page load via `inject_globals`. Default is `slate` +
   `none`. Test: user changes theme, logs out, logs back in — theme restored.

---

## Meme Engine (Creative Expression)

4. **Meme filter schema.** Create `meme_filters` table with `id`, `name`,
   `description`, `css_filters` (JSON), `overlay_svg` (text), `created_by`,
   `created_at`. Seed with 8 built-in filters: "Vaporwave", "Deep Fry",
   "Black & White", "Sepia Vintage", "Neon Glow", "Pixelate", "Blur Background",
   "Comic Book". Test: `list_meme_filters()` returns 8 rows on fresh DB.

5. **Meme filter creation endpoint.** `/meme-filter/new` allows users to create
   custom filters by selecting CSS filter values (brightness, contrast, saturate,
   hue-rotate, blur, grayscale, sepia, invert) and an optional SVG overlay.
   Store in `meme_filters`. Test: creating a filter returns a valid ID and
   the filter appears in `list_meme_filters()`.

6. **Meme image generation.** `/meme/create` accepts a photo URL and a filter
   ID, renders a `<canvas>`-based preview using CSS filters applied via an
   SVG `<foreignObject>` + `<img>` technique (no external image libraries).
   The generated meme is saved as a new post with `content_type='meme'`.
   Test: creating a meme produces a post row with non-empty `photo_url`.

7. **Selfie upload endpoint.** `/selfie/upload` accepts a photo file (same
   validation as regular uploads) and stores it as the user's `selfie_url` in
   the users table. Display selfie on profile. Test: upload returns 200 and
   `get_user()` shows the new `selfie_url`.

8. **Selfie + meme compositing.** `/meme/selfie` accepts a filter ID and
   composites the user's selfie with the selected filter, producing a
   personalized meme post. If no selfie exists, redirect to upload page with
   a flash message. Test: user with selfie creates a meme post; user without
   selfie gets redirected.

9. **Meme gallery and sharing.** `/memes` shows a gallery of all meme posts
   from friends. Memes can be shared (repost) with added caption. Test: meme
   gallery only shows memes from accepted friends, not from strangers.

---

## Location Awareness (Local Connection)

10. **Location storage with privacy tiers.** Add `location_lat`, `location_lng`,
    `location_general` (text, e.g. "Portland, OR"), `location_precision`
    (`hidden` | `general` | `precise`) to users table. Profile edit page has
    a location section: general text field + optional "Share precise location"
    toggle. Test: setting `precision='hidden'` clears lat/lng; `general` stores
    only text; `precise` stores all three.

11. **Location-based event discovery.** `/local/events` shows events whose
    `location` field (text) fuzzy-matches the user's `location_general`. Sort
    by start time. Test: user in "Portland" sees an event in "Portland, OR"
    but not one in "Seattle".

12. **Local news aggregation.** `/local/news` displays a curated feed of local
    news items. For this local-first platform, news is community-generated:
    any user can submit a "local news" post (a regular post with
    `is_local_news=1`). The page aggregates recent local-news posts from
    friends and friends-of-friends within the same general location. Test:
    a local-news post from a friend in the same city appears; one from a
    different city does not.

13. **Local fun & activities.** `/local/fun` shows a discoverable list of
    suggested local activities drawn from community posts tagged with
    `#localfun` or `#thingstodo`. Plus an "Add Activity" form. Test: a post
    with `#localfun` appears in the fun feed.

14. **"Connect Locally" feature.** `/local/people` shows a list of accepted
    friends who share the same `location_general`, plus a count of "friends
    near you". Uses only general location (never precise). Test: two friends
    with matching general locations appear; one with a different location is
    excluded.

15. **Location weather badge (mock).** Display a small weather indicator on the
    feed based on `location_general`. For the local-first platform without
    external APIs, this is a deterministic pseudo-weather generator based on
    location hash + day-of-year (sunny/cloudy/rainy/snowy + temperature
    range). Test: same location on the same day returns the same weather;
    different locations return different weather.

---

## Visual Quality of Life (The Remaining Prompts)

16. **Toast notification system.** Replace page-reload flash messages with
    auto-dismissing toast notifications (5s fade). Use a small JS module
    loaded in `base.html`. Test: after a successful POST, a toast div with
    `.toast-visible` appears in DOM within 1s.

17. **Skeleton loading screens.** Add skeleton placeholder cards to the feed
    while posts load. Implemented as CSS-only shimmer animation on empty
    `.skeleton-card` divs that are replaced by real content via JS. Test:
    feed page contains `.skeleton-card` elements on initial load before
    content injection.

18. **Smooth page transitions.** Add `page-transition` CSS class that fades
    content in over 300ms on every navigation. Apply via a small JS snippet
    in `base.html` that adds the class on `DOMContentLoaded`. Test:
    `opacity` transitions from 0 to 1 within 400ms of page load.

19. **Sticky glassmorphism navbar.** Convert the top navbar to a sticky
    position with `backdrop-filter: blur(12px)` and a subtle semi-transparent
    background. Test: navbar has `position: sticky` and `backdrop-filter` in
    computed styles.

20. **Card hover lift effect.** All content cards (posts, albums, events)
    get a `transform: translateY(-4px)` and enhanced `box-shadow` on hover
    with a 200ms transition. Test: hovering a `.card` element increases its
    `box-shadow` spread.

21. **Animated reaction buttons.** Emoji reaction buttons animate with a
    150ms scale(1.2) bounce on click, returning to scale(1). Test: clicking
    a reaction button triggers a `transform: scale(1.2)` style for at least
    100ms.

22. **Custom scrollbar theming.** Style the scrollbar to match the active
    theme using `::-webkit-scrollbar` and `scrollbar-color` (Firefox). Test:
    scrollbar thumb color matches the active theme accent color.

23. **Auto dark mode from OS preference.** If the user has not manually set a
    theme, respect `prefers-color-scheme: dark` on first visit. Once manually
    changed, the preference persists in the DB. Test: fresh session with
    `prefers-color-scheme: dark` loads the Midnight theme.

24. **Font size accessibility toggle.** Add a small "A+ / A-" control in the
    footer that adjusts the root `font-size` between 14px, 16px (default), and
    18px. Persist in `localStorage`. Test: clicking A+ increases
    `document.documentElement.style.fontSize`.

25. **High contrast mode toggle.** Add a toggle in settings that applies a
    `high-contrast` class to `<html>`, forcing `border: 2px solid currentColor`
    on all interactive elements and pure black/white text. Persist in DB.
    Test: toggling high contrast adds `.high-contrast` to `<html>`.

26. **Keyboard focus indicators.** Ensure all buttons, links, and form
    elements have a visible `:focus-visible` outline (2px dashed accent color).
    Test: focusing a button via keyboard shows a dashed outline.

27. **Empty state illustrations.** All list pages (bookmarks, messages,
    albums, events, memes) show a friendly empty-state message with a CSS
    illustration (e.g., a simple SVG drawing) when the list is empty.
    Test: an empty bookmarks page contains `.empty-state` with an SVG child.

28. **Inline upload preview.** The post creation form shows a thumbnail
    preview immediately after file selection (before submission), using
    `URL.createObjectURL()`. Test: selecting a file in the post form renders
    an `<img>` with `src` matching a blob URL.

29. **Post creation progress indicator.** Add a subtle linear progress bar at
    the top of the page during photo/video/meme upload, using the
    `XMLHttpRequest` `progress` event. Test: uploading a file shows a `.progress-bar`
    element whose width increases during the upload.

30. **Feed refresh pull-to-refresh (mobile).** On touch devices, pulling
    down on the feed triggers a reload with a rotating spinner. Implemented
    via `touchstart`/`touchmove`/`touchend` listeners on the feed container.
    Test: a `touchmove` downward of >80px on the feed adds `.pull-refresh-active`
    class.

---

## Acceptance Criteria (all prompts)

- Every prompt results in at least one new or updated test in `tests/`.
- No prompt breaks existing tests without updating them.
- All prompts verifiable in `pytest` without network access.
- Visual prompts must include a DOM/computed-style assertion that passes
  in the headless test environment.
