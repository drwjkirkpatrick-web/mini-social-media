"""
Tests for v0.8.0: meme engine and selfie features (prompts 4-9).
"""
import pytest, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

# ── Prompt 4 ──────────────────────────────────────────────────────────────
def test_meme_filter_schema_seed(client, monkeypatch):
    """list_meme_filters() returns 8 rows on fresh DB."""
    client.post("/signup", data={"username":"m4xx","email":"m4@test.com","password":"secret123","password2":"secret123"})
    client.post("/login", data={"identifier":"m4xx","password":"secret123"})
    monkeypatch.setattr(database, "DATABASE_PATH", database.DATABASE_PATH)
    database.init_database()
    filters = database.list_meme_filters()
    assert len(filters) == 8
    names = {f["name"] for f in filters}
    assert "Vaporwave" in names
    assert "Comic Book" in names

# ── Prompt 5 ──────────────────────────────────────────────────────────────
def test_meme_filter_creation_endpoint(client, monkeypatch):
    """Creating a filter returns a valid ID and appears in list."""
    client.post("/signup", data={"username":"m5xx","email":"m5@test.com","password":"secret123","password2":"secret123"})
    client.post("/login", data={"identifier":"m5xx","password":"secret123"})
    resp = client.post("/meme-filter/new", data={
        "name":"TestFilter","description":"desc","brightness":"1.1","contrast":"1.2",
        "saturate":"1.0","hue_rotate":"0deg","blur":"0px","grayscale":"0",
        "sepia":"0","invert":"0"
    }, follow_redirects=True)
    assert resp.status_code == 200
    filters = database.list_meme_filters()
    names = {f["name"] for f in filters}
    assert "TestFilter" in names

# ── Prompt 6 ──────────────────────────────────────────────────────────────
def test_meme_image_generation(client, monkeypatch):
    """Creating a meme produces a post row with non-empty photo_url."""
    client.post("/signup", data={"username":"m6xx","email":"m6@test.com","password":"secret123","password2":"secret123"})
    client.post("/login", data={"identifier":"m6xx","password":"secret123"})
    resp = client.post("/meme/new", data={
        "photo_url":"/static/uploads/test.jpg","filter_id":"1","caption":"hello meme"
    }, follow_redirects=True)
    assert resp.status_code == 200
    posts = database.list_posts_by_user(1)
    meme_posts = [p for p in posts if p["content_type"] == "meme"]
    assert len(meme_posts) >= 1
    assert meme_posts[0]["photo_url"] == "/static/uploads/test.jpg"

# ── Prompt 7 ──────────────────────────────────────────────────────────────
def test_selfie_upload_endpoint(client, tmp_path, monkeypatch):
    """Upload returns 200 and get_user shows the new selfie_url."""
    # Create user directly in DB to bypass signup form issues across module refs
    import auth
    pw_hash = auth.hash_password("secret123")
    uid = database.create_user("m7xx", "m7@test.com", pw_hash)
    # Set session manually
    with client.session_transaction() as sess:
        sess["user_id"] = uid
        sess["role"] = "user"
    # Create a tiny fake image
    img = tmp_path / "selfie.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 64)
    with open(img, "rb") as f:
        resp = client.post("/selfie/upload", data={"selfie": f}, content_type="multipart/form-data", follow_redirects=True)
    assert resp.status_code == 200
    # Verify via DB
    user = database.get_user(uid)
    assert user.get("selfie_url")
    assert "uploads" in user["selfie_url"]

# ── Prompt 8 ──────────────────────────────────────────────────────────────
def test_selfie_meme_compositing_with_selfie(client, monkeypatch):
    """User with selfie creates a meme post."""
    import auth
    pw_hash = auth.hash_password("secret123")
    uid = database.create_user("m8xx", "m8@test.com", pw_hash)
    database.update_user(uid, selfie_url="/static/uploads/selfie.jpg")
    with client.session_transaction() as sess:
        sess["user_id"] = uid
        sess["role"] = "user"
    resp = client.post("/meme/selfie", data={"filter_id":"1","caption":"me!"}, follow_redirects=True)
    assert resp.status_code == 200
    posts = database.list_posts_by_user(uid)
    meme = [p for p in posts if p["content_type"] == "meme"]
    assert len(meme) >= 1

def test_selfie_meme_compositing_without_selfie(client, monkeypatch):
    """User without selfie gets redirected."""
    client.post("/signup", data={"username":"m8b","email":"m8b@test.com","password":"secret123","password2":"secret123"})
    client.post("/login", data={"identifier":"m8b","password":"secret123"})
    resp = client.post("/meme/selfie", data={"filter_id":"1"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/profile" in resp.headers.get("Location", "")

# ── Prompt 9 ──────────────────────────────────────────────────────────────
def test_meme_gallery_shows_only_friends(client, monkeypatch):
    """Meme gallery only shows memes from accepted friends, not strangers."""
    # Alice
    client.post("/signup", data={"username":"alice9","email":"alice9@test.com","password":"secret123","password2":"secret123"})
    client.post("/login", data={"identifier":"alice9","password":"secret123"})
    uid_a = database.get_user_by_username("alice9")["id"]
    # Bob
    client.post("/signup", data={"username":"bob9","email":"bob9@test.com","password":"secret123","password2":"secret123"})
    uid_b = database.get_user_by_username("bob9")["id"]
    # Charlie
    client.post("/signup", data={"username":"charlie9","email":"charlie9@test.com","password":"secret123","password2":"secret123"})
    uid_c = database.get_user_by_username("charlie9")["id"]
    # Alice creates meme
    client.post("/login", data={"identifier":"alice9","password":"secret123"})
    database.create_meme_post(uid_a, "/static/uploads/a.jpg", 1, "alice meme")
    # Bob friend request + accept
    client.post("/friend/request/%s" % uid_b)
    client.get("/logout")
    client.post("/login", data={"identifier":"bob9","password":"secret123"})
    # Find friendship id for bob receiving from alice
    f = database.get_friendship(uid_a, uid_b)
    client.post("/friend/accept/%s" % f["id"])
    # Bob should see alice's meme
    resp = client.get("/memes")
    html = resp.data.decode()
    assert "alice meme" in html
    # Charlie (not friend) should NOT see it
    client.get("/logout")
    client.post("/login", data={"identifier":"charlie9","password":"secret123"})
    resp = client.get("/memes")
    html = resp.data.decode()
    assert "alice meme" not in html
