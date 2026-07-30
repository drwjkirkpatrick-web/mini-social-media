"""
Tests for v0.8.0: locality, location, weather (prompts 10-15).
"""
import pytest, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

# ── Prompt 10 ─────────────────────────────────────────────────────────────
def test_location_storage_privacy_tiers_hidden(client, monkeypatch):
    """Setting precision='hidden' clears lat/lng."""
    client.post("/signup", data={"username":"loc10","email":"loc10@test.com","password":"secret123","password2":"secret123"})
    client.post("/login", data={"identifier":"loc10","password":"secret123"})
    client.post("/profile/edit", data={
        "location_general":"Portland, OR","location_precision":"hidden",
        "location_lat":"45.5","location_lng":"-122.6"
    }, follow_redirects=True)
    user = database.get_user_by_username("loc10")
    assert user["location_precision"] == "hidden"
    assert user["location_general"] == "Portland, OR"

def test_location_storage_privacy_tiers_precise(client, monkeypatch):
    """Setting precision='precise' stores lat/lng."""
    client.post("/signup", data={"username":"loc10b","email":"loc10b@test.com","password":"secret123","password2":"secret123"})
    client.post("/login", data={"identifier":"loc10b","password":"secret123"})
    client.post("/profile/edit", data={
        "location_general":"Portland, OR","location_precision":"precise",
        "location_lat":"45.5","location_lng":"-122.6"
    }, follow_redirects=True)
    user = database.get_user_by_username("loc10b")
    assert user["location_precision"] == "precise"
    assert float(user["location_lat"]) == pytest.approx(45.5)

# ── Prompt 11 ─────────────────────────────────────────────────────────────
def test_location_based_event_discovery(client, monkeypatch):
    """User in 'Portland' sees an event in 'Portland, OR' but not 'Seattle'."""
    client.post("/signup", data={"username":"ev11","email":"ev11@test.com","password":"secret123","password2":"secret123"})
    uid = database.get_user_by_username("ev11")["id"]
    database.update_user(uid, location_general="Portland, OR")
    # Create events
    database.create_event(uid, "Park Meetup", "desc", "Portland, OR", "2026-08-01T10:00")
    database.create_event(uid, "Sea Meetup", "desc", "Seattle, WA", "2026-08-02T10:00")
    client.post("/login", data={"identifier":"ev11","password":"secret123"})
    events = database.list_events_by_location("Portland, OR")
    titles = {e["title"] for e in events}
    assert "Park Meetup" in titles
    assert "Sea Meetup" not in titles

# ── Prompt 12 ─────────────────────────────────────────────────────────────
def test_local_news_aggregation(client, monkeypatch):
    """Local-news post from friend in same city appears; different city excluded."""
    client.post("/signup", data={"username":"news_a","email":"news_a@test.com","password":"secret123","password2":"secret123"})
    uid_a = database.get_user_by_username("news_a")["id"]
    database.update_user(uid_a, location_general="Portland, OR")
    client.post("/signup", data={"username":"news_b","email":"news_b@test.com","password":"secret123","password2":"secret123"})
    uid_b = database.get_user_by_username("news_b")["id"]
    database.update_user(uid_b, location_general="Portland, OR")
    client.post("/signup", data={"username":"news_c","email":"news_c@test.com","password":"secret123","password2":"secret123"})
    uid_c = database.get_user_by_username("news_c")["id"]
    database.update_user(uid_c, location_general="Seattle, WA")
    # Friend a <-> b
    database.send_friend_request(uid_a, uid_b)
    f = database.get_friendship(uid_a, uid_b)
    database.accept_friend_request(f["id"])
    # Create local news posts
    pid = database.create_post(uid_a, "text", text_content="PDX update", visibility="friends")
    conn = database.get_connection()
    conn.execute("UPDATE posts SET is_local_news=1, moderation_status='approved' WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    # B should see it
    news = database.get_local_news_posts(uid_b, "Portland, OR")
    assert any(n["text_content"] == "PDX update" for n in news)
    # C should not see it (different location and not friend)
    news_c = database.get_local_news_posts(uid_c, "Seattle, WA")
    assert not any(n["text_content"] == "PDX update" for n in news_c)

# ── Prompt 13 ─────────────────────────────────────────────────────────────
def test_local_fun_activities(client, monkeypatch):
    """A post with #localfun appears in the fun feed."""
    client.post("/signup", data={"username":"fun13","email":"fun13@test.com","password":"secret123","password2":"secret123"})
    uid = database.get_user_by_username("fun13")["id"]
    database.update_user(uid, location_general="Portland, OR")
    pid = database.create_post(uid, "text", text_content="Check out this trail! #localfun", visibility="friends")
    database.store_hashtags(pid, "Check out this trail! #localfun")
    conn = database.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    posts = database.get_local_fun_posts("Portland, OR")
    assert any("Check out this trail" in p["text_content"] for p in posts)

# ── Prompt 14 ─────────────────────────────────────────────────────────────
def test_connect_locally_feature(client, monkeypatch):
    """Two friends with matching general locations appear; one with a different location is excluded."""
    client.post("/signup", data={"username":"cl_a","email":"cl_a@test.com","password":"secret123","password2":"secret123"})
    uid_a = database.get_user_by_username("cl_a")["id"]
    database.update_user(uid_a, location_general="Portland, OR")
    client.post("/signup", data={"username":"cl_b","email":"cl_b@test.com","password":"secret123","password2":"secret123"})
    uid_b = database.get_user_by_username("cl_b")["id"]
    database.update_user(uid_b, location_general="Portland, OR")
    client.post("/signup", data={"username":"cl_c","email":"cl_c@test.com","password":"secret123","password2":"secret123"})
    uid_c = database.get_user_by_username("cl_c")["id"]
    database.update_user(uid_c, location_general="Seattle, WA")
    # Friend a <-> b, a <-> c
    database.send_friend_request(uid_a, uid_b)
    f = database.get_friendship(uid_a, uid_b)
    database.accept_friend_request(f["id"])
    database.send_friend_request(uid_a, uid_c)
    f2 = database.get_friendship(uid_a, uid_c)
    database.accept_friend_request(f2["id"])
    nearby = database.list_friends_by_location(uid_a, "Portland, OR")
    ids = {p["id"] for p in nearby}
    assert uid_b in ids
    assert uid_c not in ids
    assert database.count_friends_nearby(uid_a, "Portland, OR") == 1

# ── Prompt 15 ─────────────────────────────────────────────────────────────
def test_location_weather_badge_deterministic(client, monkeypatch):
    """Same location on same day returns same weather; different locations return different weather."""
    w1 = database.get_local_weather("Portland, OR", "2026-08-01")
    w2 = database.get_local_weather("Portland, OR", "2026-08-01")
    w3 = database.get_local_weather("Seattle, WA", "2026-08-01")
    assert w1 == w2
    assert w1["location"] == "Portland, OR"
    assert w3["location"] == "Seattle, WA"
    assert w1["condition"] in {"Sunny","Partly Cloudy","Cloudy","Light Rain","Rainy","Snowy","Clear"}
    assert isinstance(w1["low"], int)
    assert isinstance(w1["high"], int)
