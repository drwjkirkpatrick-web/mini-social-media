# mini-social-media — 30 New Module Prompts (v0.2.0)

> No video. Focus: polish, interaction depth, feed intelligence, onboarding,
> accessibility, and quality-of-life features.

---

## Wave 1: Deep Social Interaction (Prompts 1–10)

### Prompt 01 — Event System
Create `events` table (id, user_id, title, description, location, start_time, end_time, created_at). Create `event_rsvps` (id, event_id, user_id, status: going/maybe/not_going). Routes: `/events` (list), `/event/new`, `/event/<id>`, `/event/<id>/rsvp`. Event detail shows attendee list. Invite friends to event.

**Test:** `test_events.py` — create event returns id; RSVP toggles status; attendee list correct.

### Prompt 02 — Polls / Voting
Create `polls` (id, post_id, question, created_at), `poll_options` (id, poll_id, text, sort_order), `poll_votes` (id, poll_option_id, user_id). Attach polls to posts. Display inline in feed. Show results after voting. Prevent duplicate votes.

**Test:** `test_polls.py` — create poll with options; vote increments count; duplicate vote rejected.

### Prompt 03 — Friend Circles
Create `circles` (id, user_id, name), `circle_members` (id, circle_id, member_id). Extend posts.visibility to include circle names. Route `/circles` to manage. Post form shows circle selector alongside "friends"/"only_me".

**Test:** `test_circles.py` — create circle; add member; post to circle visible to member, hidden from non-member friends.

### Prompt 04 — Emoji Reactions
Create `reactions` (id, post_id, user_id, reaction_type). Types: heart, laugh, wow, sad, fire. Route `/post/<id>/react` (POST with reaction param). Toggle: same reaction removes it; different reaction swaps. Show reaction bar under each post.

**Test:** `test_reactions.py` — react heart adds count; toggle removes; swap changes type; multiple users aggregate.

### Prompt 05 — Saved Posts / Bookmarks
Create `bookmarks` (id, user_id, post_id, created_at). Route `/bookmarks` to view saved posts. Bookmark icon on each post card. Unbookmark removes.

**Test:** `test_bookmarks.py` — bookmark adds to list; unbookmark removes; only bookmark owner sees their list.

### Prompt 06 — @Mentions
Parse `@username` in post text and comment text. On create, extract mentions, send notifications to mentioned users. Route `/mentions` to see posts mentioning you.

**Test:** `test_mentions.py` — post with @user creates notification; mentioned user sees in mentions feed.

### Prompt 07 — Direct Messages (DMs)
Create `messages` (id, sender_id, recipient_id, content, is_read, created_at). Routes: `/messages` (conversation list), `/messages/<user_id>` (thread), `/messages/send` (POST). Only friends can DM. Enforce block list.

**Test:** `test_messages.py` — send DM between friends; blocked user cannot send; unread count correct.

### Prompt 08 — Notifications Center (Full UI)
Extend existing `notifications` table usage. Route `/notifications` with mark-all-read, dismiss, and filter by type. Navbar shows unread badge count. Auto-dismiss old notifications (>30 days).

**Test:** `test_notifications.py` — unread badge count accurate; mark-read updates; filter by type works.

### Prompt 09 — Search
Implement `/search` with tabs: Users, Posts, Pages. SQLite `LIKE` search on username, display_name, post text_content, page title. Paginated results. Search bar in navbar.

**Test:** `test_search.py` — search finds user by username; finds post by content; finds page by title.

### Prompt 10 — Activity Log
Route `/activity` shows user's own actions: posts created, likes given, comments made, friend changes, logins. Query existing tables, no new schema needed.

**Test:** `test_activity_log.py` — shows recent posts; shows likes given; excludes other users' activity.

---

## Wave 2: Polish, Onboarding & Power Features (Prompts 11–20)

### Prompt 11 — Dark Mode
CSS `prefers-color-scheme` support + manual toggle stored in `localStorage`. Dark palette swaps: `--bg`, `--card`, `--text`, `--accent`. Toggle button in navbar.

**Test:** `test_dark_mode.py` — dark stylesheet loads; toggle switches class on body.

### Prompt 12 — Accessibility Improvements
Add `aria-label` to all interactive elements, `role="button"` to icon buttons, skip-to-content link, focus-visible outlines, `alt` text enforcement on uploads. Test keyboard navigation on feed and post forms.

**Test:** `test_accessibility.py` — all images have alt text; buttons have aria-labels; focus styles visible.

### Prompt 13 — Welcome / Onboarding Flow
First-login flag on users table. Route `/welcome` with 4-step wizard: (1) upload avatar, (2) write bio, (3) find friends (user directory), (4) create first post. Skip option available. Completes by clearing flag.

**Test:** `test_onboarding.py` — new user redirected to /welcome; completing steps clears flag; skip works.

### Prompt 14 — Help Center / FAQ
Static `/help` route with FAQ sections: Getting Started, Privacy, Moderation, Account. Searchable within page. Admin-editable via JSON file.

**Test:** `test_help_center.py` — page loads; contains FAQ sections; search filters visible questions.

### Prompt 15 — Password Reset Flow
`users` table gets `reset_token` and `reset_expires`. Routes: `/forgot-password` (enter email, token shown on screen for demo), `/reset-password/<token>` (set new password). Token expires in 1 hour.

**Test:** `test_password_reset.py` — forgot-password generates token; valid token resets password; expired token rejected.

### Prompt 16 — Two-Factor Authentication (TOTP)
`users` gets `totp_secret`. Use `pyotp` library. Route `/settings/2fa` to enable: show QR code (base64 SVG), verify once. Login flow checks 2FA if enabled. Backup codes generated.

**Test:** `test_2fa.py` — enable 2FA sets secret; valid TOTP code accepted; invalid rejected; backup codes work once.

### Prompt 17 — Post Scheduling
`posts` table gets `is_draft`, `is_scheduled`, `scheduled_at`. Route `/post/schedule`. Scheduled posts appear in feed only after `scheduled_at <= now`. Drafts visible only to author at `/drafts`.

**Test:** `test_scheduling.py` — scheduled post invisible before time; visible after; draft only visible to author.

### Prompt 18 — Post Drafts
Extend Prompt 17. Auto-save drafts every 30s via JS fetch to `/post/autosave`. Route `/drafts` shows all drafts. Resume editing loads saved content.

**Test:** `test_drafts.py` — autosave creates/updates draft; drafts page lists them; resume loads content.

### Prompt 19 — Pinned Posts
`posts` gets `is_pinned`. Users can pin one post to top of their profile. Admin can pin one post to global feed top. Pinning unpins previous. Route `/post/<id>/pin`.

**Test:** `test_pinned_posts.py` — pin places post first on profile; unpinning removes; only one pinned at a time.

### Prompt 20 — Post Sharing / Reposting
`posts` gets `original_post_id` and `share_comment`. Route `/post/<id>/share` with optional comment. Shared post appears in sharer's feed with attribution card. Original author notified.

**Test:** `test_sharing.py` — share creates repost; attribution visible; original author notified.

---

## Wave 3: Discovery, Safety & Customization (Prompts 21–30)

### Prompt 21 — Hashtags
`hashtags` (id, tag), `post_hashtags` (id, post_id, hashtag_id). Extract `#tag` from post text. Route `/tag/<tag>` shows all posts. Clickable hashtags in post text.

**Test:** `test_hashtags.py` — post with #tag creates hashtag entry; tag page shows post; click navigates.

### Prompt 22 — User Directory / Discovery
Route `/discover` lists all users with search/filter: by location, by bio keyword, recently joined. "New here?" spotlight for users <7 days old. Suggested friends based on mutuals.

**Test:** `test_discover.py` — discover lists users; filter by location works; new users highlighted.

### Prompt 23 — Mutual Friends Display
On user profile cards, show "X mutual friends" count. Route `/mutual/<user_id>` shows the list. Builds trust before sending friend request.

**Test:** `test_mutual_friends.py` — mutual count accurate; list shows correct shared friends.

### Prompt 24 — Post Analytics (Author-only)
On post detail, author sees: view count (incremented on each feed load), reaction breakdown by type, comment count, share count. Route `/post/<id>/stats`.

**Test:** `test_analytics.py` — view count increments; reaction breakdown correct; only author sees stats.

### Prompt 25 — Content Warnings / Spoiler Tags
`posts` gets `content_warning` field. Author can set a warning label (e.g., "Spoiler", "Sensitive", "Politics"). Post content hidden behind click-to-reveal overlay. Optional blur on photos.

**Test:** `test_content_warnings.py` — warning label shown; content hidden initially; reveal button works.

### Prompt 26 — Export Data / GDPR-style Download
Route `/settings/export` generates JSON of all user data: profile, posts, likes, comments, friends, messages, bookmarks. Served as downloadable file. No external dependencies.

**Test:** `test_export.py` — export contains user data; JSON is valid; includes all tables.

### Prompt 27 — Account Deactivation
`users` gets `is_active` (default 1). Route `/settings/deactivate` soft-deletes: hides profile, anonymizes posts ("[deleted user]"), preserves friendships for reactivation. Reactivation by logging in with confirmation.

**Test:** `test_deactivation.py` — deactivate hides profile; reactivation restores; posts anonymized.

### Prompt 28 — Theme Customization
`users` gets `theme` (light/dark), `accent_color` (hex). Route `/settings/theme` to pick accent from preset palette or custom hex. Applied via CSS custom properties. Stored in user record and localStorage fallback.

**Test:** `test_theme.py` — accent color updates CSS var; theme persists across sessions.

### Prompt 29 — Feed Sort: Algorithmic (Most Engaged)
New sort option `engaged` in feed engine. Score = likes*2 + comments*3 + shares*5 + recency_bonus (hours_since^(-0.5)). Top-scored posts first. Toggle in feed UI.

**Test:** `test_feed_engaged.py` — engaged sort ranks high-interaction posts higher; respects privacy.

### Prompt 30 — Guest / Invite Links
`invite_tokens` (id, token, created_by, max_uses, used_count, expires_at). Route `/settings/invites` to generate links. Signup page accepts `?invite=TOKEN`. Token validated, decrements uses. Expired/used-up tokens rejected.

**Test:** `test_invite_links.py` — valid token allows signup; used-up token rejected; expired token rejected.

---

## Dependency Table

| Prompt | New Tables | Modified Tables | Depends On |
|---|---|---|---|
| 01 Events | events, event_rsvps | — | 08 (notifications) |
| 02 Polls | polls, poll_options, poll_votes | — | 09 (posts) |
| 03 Circles | circles, circle_members | posts.visibility | 13 (friendships) |
| 04 Reactions | reactions | — | 09 (posts) |
| 05 Bookmarks | bookmarks | — | 09 (posts) |
| 06 Mentions | — | notifications | 08 |
| 07 DMs | messages | — | 13, blocks |
| 08 Notifications | — | (uses existing) | — |
| 09 Search | — | — | — |
| 10 Activity Log | — | — | — |
| 11 Dark Mode | — | — | — |
| 12 Accessibility | — | — | — |
| 13 Onboarding | users.has_onboarded | users | 05 (signup) |
| 14 Help Center | — | — | — |
| 15 Password Reset | users.reset_token | users | 05 (signup) |
| 16 2FA | users.totp_secret, backup_codes | users | 04 (session) |
| 17 Scheduling | — | posts.is_draft, scheduled_at | 09 (posts) |
| 18 Drafts | — | posts.is_draft | 17 |
| 19 Pinned Posts | — | posts.is_pinned | 09 (posts) |
| 20 Sharing | — | posts.original_post_id | 09 (posts) |
| 21 Hashtags | hashtags, post_hashtags | — | 09 (posts) |
| 22 Discover | — | — | 13 (friendships) |
| 23 Mutual Friends | — | — | 13 (friendships) |
| 24 Analytics | — | — | 04, 09 (posts) |
| 25 Content Warnings | — | posts.content_warning | 09 (posts) |
| 26 Export | — | — | ALL |
| 27 Deactivation | — | users.is_active | — |
| 28 Theme | — | users.theme, accent_color | — |
| 29 Engaged Sort | — | — | 11 (feed) |
| 30 Invite Links | invite_tokens | — | 05 (signup) |
