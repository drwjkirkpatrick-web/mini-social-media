"""
Tests for v0.9.0: meme engine improvements (30 features + 5 additional tests).

These tests cover new database functions that may be added by another worker.
If a function does not exist yet, tests will fail with AttributeError — that's expected.
The test file itself must be syntactically valid.
"""
import pytest, json, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database


# Helper ----------------------------------------------------------------------

def _make_user(client, username, email=None):
    """Signup + login a user; return (uid, None) on success or (None, resp) on failure."""
    if email is None:
        email = username + "@test.com"
    client.post("/signup", data={
        "username": username,
        "email": email,
        "password": "secret123",
        "password2": "secret123",
    })
    client.post("/login", data={"identifier": username, "password": "secret123"})
    user = database.get_user_by_username(username)
    return user["id"] if user else None


def _make_meme_post(uid, photo_url="/static/uploads/m.jpg", filter_id=1, text="meme caption"):
    """Create a meme post via database helper and return its id."""
    return database.create_meme_post(uid, photo_url, filter_id, text)


# ── 1. Template schema & seed ──────────────────────────────────────────────
def test_meme_templates_schema_and_seed(client):
    """init_database creates meme_templates table with 12 seeded templates (Drake, Distracted Boyfriend, etc.)."""
    templates = database.list_meme_templates()
    assert len(templates) == 12
    names = {t["name"] for t in templates}
    assert "Drake" in names
    assert "Distracted Boyfriend" in names


# ── 2. Create custom template ──────────────────────────────────────────────
def test_create_custom_meme_template(client):
    """create_meme_template() returns int ID and appears in list_meme_templates()."""
    uid = _make_user(client, "tmpl_user")
    tid = database.create_meme_template(
        "CustomT2", "funny", "/static/uploads/t2.jpg", 500, 500, uid
    )
    assert isinstance(tid, int)
    assert tid > 0
    templates = database.list_meme_templates()
    names = {t["name"] for t in templates}
    assert "CustomT2" in names


# ── 3. Search templates ─────────────────────────────────────────────────────
def test_search_meme_templates(client):
    """search_meme_templates('drake') returns Drake template."""
    results = database.search_meme_templates("drake")
    assert len(results) >= 1
    assert any("Drake" in r["name"] for r in results)


# ── 4. Template favorites toggle ───────────────────────────────────────────
def test_template_favorites_toggle(client):
    """favorite_template() toggles, list_favorite_templates() shows favorited."""
    uid = _make_user(client, "fav_user")
    templates = database.list_meme_templates()
    tpl_id = templates[0]["id"]

    # Favorite it
    database.favorite_template(uid, tpl_id)
    favs = database.list_favorite_templates(uid)
    fav_ids = {f["template_id"] if "template_id" in f else f["id"] for f in favs}
    assert tpl_id in fav_ids

    # Unfavorite it (toggle)
    database.favorite_template(uid, tpl_id)
    favs_after = database.list_favorite_templates(uid)
    fav_ids_after = {f["template_id"] if "template_id" in f else f["id"] for f in favs_after}
    assert tpl_id not in fav_ids_after


# ── 5. Top/bottom text ──────────────────────────────────────────────────────
def test_meme_top_bottom_text(client):
    """update_meme_post() sets top_text and bottom_text, get_post() returns them."""
    uid = _make_user(client, "tb_user")
    pid = _make_meme_post(uid)
    database.update_meme_post(pid, top_text="TOP LINE", bottom_text="BOTTOM LINE")
    post = database.get_post(pid)
    assert post["top_text"] == "TOP LINE"
    assert post["bottom_text"] == "BOTTOM LINE"


# ── 6. Text color ───────────────────────────────────────────────────────────
def test_meme_text_color(client):
    """update_meme_post() sets text_color to custom hex."""
    uid = _make_user(client, "color_user")
    pid = _make_meme_post(uid)
    database.update_meme_post(pid, text_color="#ff5733")
    post = database.get_post(pid)
    assert post["text_color"] == "#ff5733"


# ── 7. Text rotation ───────────────────────────────────────────────────────
def test_meme_text_rotation(client):
    """update_meme_post() sets text_rotation to 5.0 degrees."""
    uid = _make_user(client, "rot_user")
    pid = _make_meme_post(uid)
    database.update_meme_post(pid, text_rotation=5.0)
    post = database.get_post(pid)
    assert float(post["text_rotation"]) == 5.0


# ── 8. Caption suggestion bank ─────────────────────────────────────────────
def test_caption_suggestion_bank(client):
    """list_meme_tags() returns seeded tags including 'trending', 'classic', 'wholesome'."""
    tags = database.list_meme_tags()
    assert len(tags) >= 3
    tag_names = {t["name"] for t in tags}
    assert "trending" in tag_names
    assert "classic" in tag_names
    assert "wholesome" in tag_names


# ── 9. Stickers schema & seed ──────────────────────────────────────────────
def test_meme_stickers_schema_and_seed(client):
    """list_meme_stickers() returns 8 seeded stickers (Fire, Heart, 100, etc.)."""
    stickers = database.list_meme_stickers()
    assert len(stickers) == 8
    names = {s["name"] for s in stickers}
    assert "Fire" in names
    assert "Heart" in names
    assert "100" in names


# ── 10. Sticker placement ──────────────────────────────────────────────────
def test_sticker_placement(client):
    """place_sticker() creates placement, get_sticker_placements() returns it with x/y/rotation."""
    uid = _make_user(client, "sticker_user")
    pid = _make_meme_post(uid)
    stickers = database.list_meme_stickers()
    sid = stickers[0]["id"]

    database.place_sticker(pid, sid, 100, 200, rotation=15.0, scale=1.5)
    placements = database.get_sticker_placements(pid)
    assert len(placements) >= 1
    p = placements[0]
    assert p["pos_x"] == 100
    assert p["pos_y"] == 200
    assert float(p["rotation"]) == 15.0


# ── 11. Watermark ──────────────────────────────────────────────────────────
def test_meme_watermark(client):
    """update_meme_post() sets watermark_text, get_post() shows it."""
    uid = _make_user(client, "wm_user")
    pid = _make_meme_post(uid)
    database.update_meme_post(pid, watermark_text="@myhandle")
    post = database.get_post(pid)
    assert post["watermark_text"] == "@myhandle"


# ── 12. Specific reactions ─────────────────────────────────────────────────
def test_meme_specific_reactions(client):
    """react_meme() toggles emoji reaction, get_meme_reactions() returns counts."""
    uid = _make_user(client, "react_user")
    pid = _make_meme_post(uid)

    database.react_meme(pid, uid, "🔥")
    reactions = database.get_meme_reactions(pid)
    assert len(reactions) >= 1
    fire = [r for r in reactions if r["emoji"] == "🔥"]
    assert len(fire) == 1
    assert fire[0]["count"] == 1

    # Toggle off
    database.react_meme(pid, uid, "🔥")
    reactions = database.get_meme_reactions(pid)
    fire = [r for r in reactions if r["emoji"] == "🔥"]
    assert len(fire) == 0 or fire[0]["count"] == 0


# ── 13. Remix chain ────────────────────────────────────────────────────────
def test_meme_remix_chain(client):
    """Create meme post A, create remix post B with meme_remix_of=A.id, get_meme_remix_chain(B.id) returns [B, A]."""
    uid = _make_user(client, "remix_user")
    post_a = _make_meme_post(uid, text="original")
    post_b = _make_meme_post(uid, text="remix version")

    database.update_meme_post(post_b, meme_remix_of=post_a)
    chain = database.get_meme_remix_chain(post_b)
    assert len(chain) >= 2
    # Chain should start with root (A) then B (database reverses to root-first order)
    chain_ids = [p["id"] for p in chain]
    assert post_b in chain_ids
    assert post_a in chain_ids
    # Root should be first (chain is reversed: root → leaf)
    assert chain_ids[0] == post_a


# ── 14. Vote up ─────────────────────────────────────────────────────────────
def test_meme_vote_up(client):
    """vote_meme(1) increases score, get_meme_score() returns 1."""
    uid = _make_user(client, "vote_up_user")
    pid = _make_meme_post(uid)
    database.vote_meme(pid, uid, 1)
    score = database.get_meme_score(pid)
    assert score == 1


# ── 15. Vote down ──────────────────────────────────────────────────────────
def test_meme_vote_down(client):
    """vote_meme(-1) decreases score, get_meme_score() returns -1."""
    uid = _make_user(client, "vote_down_user")
    pid = _make_meme_post(uid)
    database.vote_meme(pid, uid, -1)
    score = database.get_meme_score(pid)
    assert score == -1


# ── 16. Leaderboard ────────────────────────────────────────────────────────
def test_meme_leaderboard(client):
    """Create multiple meme posts with different votes, get_top_memes() returns sorted by score desc."""
    uid_a = _make_user(client, "lead_a")
    uid_b = _make_user(client, "lead_b")
    uid_c = _make_user(client, "lead_c")

    # Make them all friends so memes show up in leaderboard
    database.send_friend_request(uid_a, uid_b)
    database.send_friend_request(uid_a, uid_c)
    database.send_friend_request(uid_b, uid_c)
    # Accept all pending requests for uid_b and uid_c
    for f in database.list_pending_requests(uid_b):
        database.accept_friend_request(f["id"])
    for f in database.list_pending_requests(uid_c):
        database.accept_friend_request(f["id"])

    p1 = _make_meme_post(uid_a, text="meme1")
    p2 = _make_meme_post(uid_b, text="meme2")
    p3 = _make_meme_post(uid_c, text="meme3")

    # p1: +3, p2: +1, p3: -1
    for _ in range(3):
        database.vote_meme(p1, uid_b, 1)
    database.vote_meme(p2, uid_a, 1)
    database.vote_meme(p3, uid_a, -1)

    # get_top_memes requires user_id (filters to friends), so pass uid_a
    # Note: get_top_memes only shows friends' memes, not your own
    top = database.get_top_memes(uid_a, limit=10)
    assert len(top) >= 2  # p2 and p3 from friends uid_b and uid_c
    scores = [m["score"] for m in top if "score" in m]
    assert scores == sorted(scores, reverse=True)


# ── 17. Collection create ───────────────────────────────────────────────────
def test_meme_collection_create(client):
    """create_meme_collection() returns ID, list_meme_collections() shows it."""
    uid = _make_user(client, "coll_user")
    cid = database.create_meme_collection(uid, name="My Collection", description="best memes")
    assert isinstance(cid, int)
    assert cid > 0
    collections = database.list_meme_collections(uid)
    names = {c["name"] for c in collections}
    assert "My Collection" in names


# ── 18. Collection add/remove ──────────────────────────────────────────────
def test_meme_collection_add_remove(client):
    """add_to_collection() then list_collection_items(), then remove_from_collection()."""
    uid = _make_user(client, "coll_add_user")
    pid = _make_meme_post(uid)
    cid = database.create_meme_collection(uid, name="Add Test")

    database.add_to_collection(cid, pid)
    items = database.list_collection_items(cid)
    assert len(items) >= 1
    assert any(i["post_id"] == pid for i in items)

    database.remove_from_collection(cid, pid)
    items_after = database.list_collection_items(cid)
    assert all(i["post_id"] != pid for i in items_after)


# ── 19. Tagging ─────────────────────────────────────────────────────────────
def test_meme_tagging(client):
    """tag_meme_post() creates tag and links, get_meme_post_tags() returns tag names."""
    uid = _make_user(client, "tag_user")
    pid = _make_meme_post(uid)
    database.tag_meme_post(pid, "funny")
    database.tag_meme_post(pid, "cats")
    tags = database.get_meme_post_tags(pid)
    tag_names = {t["name"] for t in tags}
    assert "funny" in tag_names
    assert "cats" in tag_names


# ── 20. Draft ───────────────────────────────────────────────────────────────
def test_meme_draft(client):
    """update_meme_post(is_meme_draft=1) marks as draft, list_meme_drafts() returns it."""
    uid = _make_user(client, "draft_user")
    pid = _make_meme_post(uid)
    database.update_meme_post(pid, is_meme_draft=1)
    drafts = database.list_meme_drafts(uid)
    draft_ids = [d["id"] for d in drafts]
    assert pid in draft_ids


# ── 21. Scheduling ──────────────────────────────────────────────────────────
def test_meme_scheduling(client):
    """update_meme_post(meme_scheduled_at='2026-08-01 10:00') schedules, list_scheduled_memes() returns it."""
    uid = _make_user(client, "sched_user")
    pid = _make_meme_post(uid)
    database.update_meme_post(pid, meme_scheduled_at="2026-08-01 10:00")
    scheduled = database.list_scheduled_memes(uid)
    sched_ids = [s["id"] for s in scheduled]
    assert pid in sched_ids


# ── 22. A/B variant creation ───────────────────────────────────────────────
def test_ab_variant_creation(client):
    """create two meme posts, create_ab_variant(post_a, post_b), get_ab_variant() returns it."""
    uid = _make_user(client, "ab_user")
    post_a = _make_meme_post(uid, text="variant A")
    post_b = _make_meme_post(uid, text="variant B")
    vid = database.create_ab_variant(post_a, post_b)
    assert isinstance(vid, int)
    assert vid > 0
    variant = database.get_ab_variant(vid)
    assert variant is not None
    assert variant["original_post_id"] == post_a
    assert variant["variant_post_id"] == post_b


# ── 23. A/B variant voting ────────────────────────────────────────────────
def test_ab_variant_voting(client):
    """vote_ab(variant_id, 'a') increments votes_a, vote_ab(variant_id, 'b') increments votes_b."""
    uid = _make_user(client, "ab_vote_user")
    post_a = _make_meme_post(uid, text="A")
    post_b = _make_meme_post(uid, text="B")
    vid = database.create_ab_variant(post_a, post_b)

    database.vote_ab(vid, "a")
    database.vote_ab(vid, "a")
    database.vote_ab(vid, "b")
    variant = database.get_ab_variant(vid)
    assert variant["votes_a"] == 2
    assert variant["votes_b"] == 1


# ── 24. Filter roulette ────────────────────────────────────────────────────
def test_filter_roulette(client):
    """list_meme_filters() returns at least 8, random choice is valid (test that random filter selection works)."""
    filters = database.list_meme_filters()
    assert len(filters) >= 8
    # Simulate filter roulette: pick a random filter and verify it's valid
    random.seed(42)
    chosen = random.choice(filters)
    assert "name" in chosen
    assert "id" in chosen
    # Verify it's still in the list
    assert chosen in filters


# ── 25. Filter strength ────────────────────────────────────────────────────
def test_filter_strength(client):
    """update_meme_post(filter_strength=50) sets it, get_post() returns 50."""
    uid = _make_user(client, "fs_user")
    pid = _make_meme_post(uid)
    database.update_meme_post(pid, filter_strength=50)
    post = database.get_post(pid)
    assert post["filter_strength"] == 50


# ── 26. Before/after compare ───────────────────────────────────────────────
def test_before_after_compare(client):
    """Create meme with filter, get_post() has both photo_url and filter_id for comparison."""
    uid = _make_user(client, "ba_user")
    pid = database.create_meme_post(uid, "/static/uploads/before.jpg", filter_id=1, text_content="compare me")
    post = database.get_post(pid)
    assert post["photo_url"] == "/static/uploads/before.jpg"
    assert post["filter_id"] == 1


# ── 27. Meme grid ──────────────────────────────────────────────────────────
def test_meme_grid(client):
    """update_meme_post(meme_grid_layout='2x2') sets layout, get_post() returns it."""
    uid = _make_user(client, "grid_user")
    pid = _make_meme_post(uid)
    database.update_meme_post(pid, meme_grid_layout="2x2")
    post = database.get_post(pid)
    assert post["meme_grid_layout"] == "2x2"


# ── 28. Meme of the day ─────────────────────────────────────────────────────
def test_meme_of_the_day(client):
    """get_meme_of_the_day() returns a dict (may be empty if no memes, but function works without error)."""
    result = database.get_meme_of_the_day()
    # May return a dict or None if no memes exist
    assert result is None or isinstance(result, dict)


# ── 29. Meme stats ─────────────────────────────────────────────────────────
def test_meme_stats(client):
    """Create meme post, add vote and reaction, get_meme_stats() returns dict with votes and reactions counts."""
    uid = _make_user(client, "stats_user")
    pid = _make_meme_post(uid)
    database.vote_meme(pid, uid, 1)
    database.react_meme(pid, uid, "❤️")

    stats = database.get_meme_stats(pid)
    assert isinstance(stats, dict)
    assert stats["votes"] == 1
    assert stats["reactions"] >= 1


# ── 30. JSON export ────────────────────────────────────────────────────────
def test_meme_json_export(client):
    """Create meme post with text, filter, vote, export_meme_json() returns dict with all fields."""
    uid = _make_user(client, "export_user")
    pid = _make_meme_post(uid, text="export caption")
    database.update_meme_post(pid, top_text="TOP", bottom_text="BOTTOM", filter_strength=75)
    database.vote_meme(pid, uid, 1)

    exported = database.export_meme_json(pid)
    assert isinstance(exported, dict)
    # export_meme_json returns {"post": {...}, "tags": [...], ...}
    post_data = exported.get("post", exported)
    assert post_data["id"] == pid
    assert post_data["top_text"] == "TOP"
    assert post_data["bottom_text"] == "BOTTOM"
    assert post_data["filter_id"] == 1
    assert post_data["filter_strength"] == 75


# ── Additional tests ───────────────────────────────────────────────────────

def test_meme_trending_tags(client):
    """get_trending_meme_tags() returns list (may be empty)."""
    result = database.get_trending_meme_tags()
    assert isinstance(result, list)


def test_meme_search(client):
    """search_meme_posts('hello') returns posts matching top_text/bottom_text/watermark."""
    uid = _make_user(client, "search_user")
    pid = _make_meme_post(uid, text="hello world")
    database.update_meme_post(pid, top_text="hello there", bottom_text="general kenobi")
    results = database.search_meme_posts("hello")
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any(r["id"] == pid for r in results)


def test_meme_challenge_create(client):
    """create_meme_challenge() returns ID, list_meme_challenges() shows it."""
    cid = database.create_meme_challenge(
        "Best Cat Meme",
        "Submit your best cat memes",
        "2026-08-01 00:00",
        "2026-08-15 23:59",
    )
    assert isinstance(cid, int)
    assert cid > 0
    challenges = database.list_meme_challenges()
    assert any(c["id"] == cid for c in challenges)


def test_meme_challenge_enter(client):
    """enter_meme_challenge() creates entry, get_challenge_entries() returns it."""
    uid = _make_user(client, "challenge_enter_user")
    pid = _make_meme_post(uid, text="challenge entry")
    cid = database.create_meme_challenge(
        "Test Challenge", "d", "2026-08-01 00:00", "2026-08-15 23:59"
    )

    entry_id = database.enter_meme_challenge(cid, pid, uid)
    assert entry_id is not None
    entries = database.get_challenge_entries(cid)
    assert len(entries) >= 1
    assert any(e["post_id"] == pid for e in entries)


def test_meme_remix_of_the_day(client):
    """get_meme_of_the_day() deterministic — same result on same day with same data."""
    uid = _make_user(client, "remix_day_user")
    # Create a meme so there's data to pick from
    _make_meme_post(uid, text="day candidate")

    result1 = database.get_meme_of_the_day()
    result2 = database.get_meme_of_the_day()
    # Should be deterministic — same result both calls
    if result1 is None and result2 is None:
        assert True  # both empty is deterministic
    else:
        assert result1 is not None
        assert result2 is not None
        assert result1.get("id") == result2.get("id")