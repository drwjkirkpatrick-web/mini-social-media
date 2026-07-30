# mini-social-media — 30 Accuracy & Efficiency Prompts (v0.7.0)

> Target: make the platform faster, more correct, and more robust without
> adding user-facing features. Every prompt must include a measurable claim and
> at least one automated test that proves the claim.

---

## Accuracy (Correctness & Robustness)

1. **Approve post before it can appear in any feed.** Currently some tests
   manually `UPDATE posts SET moderation_status='approved'`. Move approval into
   `create_post` for admin users, or add an explicit `approve_post()` helper and
   ensure `get_feed`, custom feeds, hashtags, and search all reject pending
   posts. Test: a pending post is invisible everywhere.

2. **Enforce friends-only visibility on profile export.** `export_data()` dumps
   all of the user's posts; verify it only includes posts the requester is
   allowed to see (own, friend-only with accepted friendship, or public). Test:
   export by a non-friend omits private posts.

3. **Fix mute/block race in feed.** `get_feed` filters blocks but does not
   filter mutes; muted-word and muted-account logic lives elsewhere. Unify
   suppression so feed, notifications, search, and mentions all respect blocks,
   mutes, and muted words through a single `is_content_visible(user_id, post)`
   predicate. Test: blocked/muted/muted-word content hidden in all four surfaces.

4. **Idempotent friend request.** Calling `send_friend_request(me, you)` twice
   must not create duplicate rows or corruption. Test: second call returns
   existing pending request ID.

5. **Consistent pagination across list endpoints.** Several list routes return
   `LIMIT ? OFFSET ?` but do not expose `next`/`prev` cursors or total counts.
   Standardize on a `paginate()` helper that returns `{items, total, has_more,
   next_offset}`. Test: all list endpoints produce the same shape.

6. **Validate email uniqueness case-insensitively.** `get_user_by_email` checks
   exact case; registrations can currently create `Alice@x.com` and `alice@x.com`.
   Normalize to lowercase on insert and lookup. Test: second signup with
   different case fails.

7. **Secure file upload path canonicalization.** Uploaded filenames are stored
   with user-provided extensions. Verify the saved path is inside `uploads/`
   after `os.path.realpath()` and reject path-traversal attempts (`../../../`).
   Test: filename `../etc/passwd.jpg` rejected.

8. **Atomic like toggle.** `toggle_like` currently does SELECT-then-INSERT/DELETE.
   Replace with an INSERT ... ON CONFLICT or a single transaction so concurrent
   requests cannot create duplicate likes. Test: 10 rapid toggles leave exactly
   one like or zero likes.

9. **Correct story expiry.** Stories use `expires_at` but expiry may not be
   enforced consistently in `get_active_stories`, feed injection, or API. Add a
   single `is_story_active(story)` helper used everywhere. Test: expired story is
   not returned.

10. **Consistent datetime timezone handling.** Some code uses `datetime.now()`,
    some `datetime.now(timezone.utc)`, some `.isoformat()` without `Z`. Adopt
    UTC everywhere and add a `_utc_now()` helper plus tests that verify no
    naive/aware comparison crashes occur.

11. **Notification deduplication.** Creating a like currently emits a
    notification on every toggle; unliking and re-liking spams the recipient.
    Add a `(user_id, type, reference_id, created_at DATE)` unique constraint or
    dedup check. Test: re-like within 24h does not create a second notification.

12. **Hermes webhook signature verification.** The `/hermes/webhook` endpoint
    accepts posts without HMAC validation. Add `X-Hermes-Signature` HMAC-SHA256
    check using `HERMES_WEBHOOK_SECRET`. Test: missing/invalid signature returns
    401, valid signature is processed.

13. **Poll vote idempotency.** A user voting twice in the same poll should
    update their choice, not create duplicate votes. Test: second vote changes
    option counts correctly.

14. **RSVP state machine correctness.** Event RSVP should transition only
    between valid states and only for accepted friends or the event owner.
    Test: rejected friendship blocks RSVP, duplicate RSVP updates state.

15. **Search ranking accuracy.** `/search` orders by `created_at DESC` only.
    Add relevance scoring (title/username match starts full word > substring >
    nowhere). Test: exact username match ranks first.

---

## Efficiency (Performance & Resource Usage)

16. **Eliminate N+1 queries in feed generation.** `get_feed` runs separate
    `COUNT(*)` queries for likes, comments, and reactions for every post. Replace
    with a single subquery or CTE that joins aggregate counts for the full page.
    Benchmark test: 50 posts must execute ≤ 3 DB statements.

17. **Add database indexes for hot paths.** Add composite indexes on
    `(posts.user_id, created_at)`, `(posts.moderation_status, is_draft,
    is_scheduled, created_at)`, `(friendships.requester_id, status)`,
    `(friendships.addressee_id, status)`, `(notifications.user_id, created_at)`,
    and `(messages.sender_id, recipient_id, created_at)`. Test: `EXPLAIN QUERY
    PLAN` shows index use for feed and messages.

18. **Connection pooling / thread-local reuse.** `get_connection()` opens a new
    SQLite connection on every call. Add a thread-local connection cache with
    a 30-second idle close. Test: 100 sequential calls in one thread reuse the
    same connection object.

19. **Lazy image thumbnail generation.** Video thumbnails are generated
    synchronously on upload, blocking the request. Move to a background thread
    and render a placeholder until ready. Test: upload returns 200 before
    thumbnail file exists.

20. **Batch notification creation.** Currently notifications are inserted one
    at a time inside loops (e.g., group messages, likes). Add
    `create_notifications_batch()` using `executemany()`. Test: 50 notifications
    created in one statement.

21. **Feed result caching with invalidation.** Cache the rendered feed result
    (post IDs only) keyed by `(user_id, sort, offset, limit)` for 30 seconds,
    invalidating on post create/like/comment/friend change. Test: identical
    request within 30s uses cache; after a post it misses.

22. **Compress static assets in production.** Add gzip/brotli precompression
    for CSS/JS and serve with `Content-Encoding`. Test: `/static/sw.js` returns
    `Content-Encoding: gzip` when a `.gz` sibling exists.

23. **Reduce memory copies in export.** `export_data()` materializes every row
    as a dict and then `json.dumps()`. Stream large exports using generators and
    `json.dump()` to a file handle. Test: export of 1000 posts stays under 10 MB
    peak memory.

24. **Batch database seeding.** `init_database()` seeds achievements with one
    `INSERT` per row. Replace with a single `INSERT ... VALUES` or
    `executemany()`. Test: seeding completes in ≤ 3 statements.

25. **Optimize moderation scan.** `moderation.scan_text()` compiles regex
    patterns on every call. Compile once at module load. Test: scan 1000 posts
    without recompiling patterns.

26. **Paginate large admin endpoints.** `/admin/disk`, `/moderation-queue`, and
    `/users` may load unbounded rows. Add default `limit=50` with `next_offset`
    to all admin list routes. Test: request without limit returns 50 items and
    a `has_more` flag.

27. **Avoid full table scans in discover.** `/discover` selects all active users
    and filters in Python. Push the friend-exclusion and limit into SQL. Test:
    `EXPLAIN QUERY PLAN` shows no full table scan on users.

28. **Compress stored stories after expiry.** Expired stories are deleted but
    their media files remain. Add a cleanup job that archives (or deletes)
    expired story media. Test: after story expiry, its media file is removed.

29. **Statement timeout for expensive queries.** Wrap long-running reporting
    queries with a `PRAGMA busy_timeout` and a `MAX_EXECUTION_TIME`-style
    guard or a Flask `timeout` decorator. Test: a 5-second sleep query is
    interrupted and returns 503, not a hung worker.

30. **Profile-aware query limits.** `feed_max_limit` is configurable but not
    enforced in several routes. Add a centralized `get_int_param(name, default,
    max)` helper used by feed, search, mentions, notifications, messages, and
    custom feeds. Test: requesting `?limit=9999` clamps to the configured max.

---

## Acceptance Criteria (all prompts)

- Every prompt must result in at least one new or updated test in `tests/`.
- No prompt may break existing tests without updating them to reflect the new
  correct behavior.
- All prompts must be verifiable in `pytest` without network access.
- Performance prompts must include a benchmark assertion (query count, timing
  ceiling, or memory ceiling) that fails before the optimization and passes
  after.
