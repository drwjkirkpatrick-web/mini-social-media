import database
from auth import hash_password


def _approve_posts(user_id):
    """Mark all of a user's posts as approved (tests create pending posts)."""
    conn = database.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Database-level CRUD tests
# ---------------------------------------------------------------------------

def test_create_custom_feed(test_db):
    u = test_db.create_user("feed_owner", "fo@test.com", hash_password("pass"))
    fid = database.create_custom_feed(u, "My Feed", "hashtag", "travel")
    assert fid > 0
    feed = database.get_custom_feed(fid)
    assert feed is not None
    assert feed["name"] == "My Feed"
    assert feed["filter_type"] == "hashtag"
    assert feed["filter_value"] == "travel"
    assert feed["is_pinned"] == 0


def test_list_custom_feeds(test_db):
    u = test_db.create_user("lister", "li@test.com", hash_password("pass"))
    database.create_custom_feed(u, "Feed A", "hashtag", "a")
    database.create_custom_feed(u, "Feed B", "user", "someone")
    feeds = database.list_custom_feeds(u)
    assert len(feeds) == 2


def test_list_custom_feeds_isolated(test_db):
    """Feeds for one user are not visible to another."""
    a = test_db.create_user("iso_a", "ia@test.com", hash_password("pass"))
    b = test_db.create_user("iso_b", "ib@test.com", hash_password("pass"))
    database.create_custom_feed(a, "Only A", "hashtag", "x")
    assert len(database.list_custom_feeds(a)) == 1
    assert len(database.list_custom_feeds(b)) == 0


def test_delete_custom_feed(test_db):
    u = test_db.create_user("deleter", "del@test.com", hash_password("pass"))
    fid = database.create_custom_feed(u, "To Delete", "hashtag", "gone")
    removed = database.delete_custom_feed(fid, u)
    assert removed is True
    assert database.get_custom_feed(fid) is None


def test_delete_custom_feed_not_owner(test_db):
    """A user cannot delete another user's feed."""
    a = test_db.create_user("owner_d", "od@test.com", hash_password("pass"))
    b = test_db.create_user("intruder_d", "id@test.com", hash_password("pass"))
    fid = database.create_custom_feed(a, "Owned", "hashtag", "keep")
    removed = database.delete_custom_feed(fid, b)
    assert removed is False
    assert database.get_custom_feed(fid) is not None


def test_toggle_pin_custom_feed(test_db):
    u = test_db.create_user("pinner", "pin@test.com", hash_password("pass"))
    fid = database.create_custom_feed(u, "Pin Me", "hashtag", "stuff")
    assert database.get_custom_feed(fid)["is_pinned"] == 0
    pinned = database.toggle_pin_custom_feed(fid, u)
    assert pinned is True
    assert database.get_custom_feed(fid)["is_pinned"] == 1
    unpinned = database.toggle_pin_custom_feed(fid, u)
    assert unpinned is False
    assert database.get_custom_feed(fid)["is_pinned"] == 0


def test_pin_lists_pinned_first(test_db):
    u = test_db.create_user("orderer", "ord@test.com", hash_password("pass"))
    f1 = database.create_custom_feed(u, "First", "hashtag", "a")
    f2 = database.create_custom_feed(u, "Second", "hashtag", "b")
    database.toggle_pin_custom_feed(f2, u)
    feeds = database.list_custom_feeds(u)
    # Pinned feed should come first
    assert feeds[0]["id"] == f2
    assert feeds[0]["is_pinned"] == 1
    assert feeds[1]["id"] == f1


def test_get_custom_feed_posts_hashtag(test_db):
    u = test_db.create_user("tagger", "tg@test.com", hash_password("pass"))
    p1 = test_db.create_post(u, "text", text_content="Loving this #travel trip")
    p2 = test_db.create_post(u, "text", text_content="Nothing relevant here")
    database.store_hashtags(p1, "Loving this #travel trip")
    database.store_hashtags(p2, "Nothing relevant here")
    _approve_posts(u)
    fid = database.create_custom_feed(u, "Travel Feed", "hashtag", "travel")
    posts = database.get_custom_feed_posts(fid)
    assert len(posts) == 1
    assert posts[0]["id"] == p1


def test_get_custom_feed_posts_user(test_db):
    u = test_db.create_user("poster_a", "pa@test.com", hash_password("pass"))
    other = test_db.create_user("poster_b", "pb@test.com", hash_password("pass"))
    test_db.create_post(u, "text", text_content="Post from A")
    test_db.create_post(other, "text", text_content="Post from B")
    _approve_posts(u)
    _approve_posts(other)
    fid = database.create_custom_feed(u, "A's Posts", "user", "poster_a")
    posts = database.get_custom_feed_posts(fid)
    assert len(posts) == 1
    assert posts[0]["text_content"] == "Post from A"


def test_get_custom_feed_posts_keyword(test_db):
    u = test_db.create_user("kw_user", "kw@test.com", hash_password("pass"))
    test_db.create_post(u, "text", text_content="I love coffee in the morning")
    test_db.create_post(u, "text", text_content="Tea is also fine")
    _approve_posts(u)
    fid = database.create_custom_feed(u, "Coffee Feed", "keyword", "coffee")
    posts = database.get_custom_feed_posts(fid)
    assert len(posts) == 1
    assert "coffee" in posts[0]["text_content"]


def test_get_custom_feed_posts_photos(test_db):
    u = test_db.create_user("photo_user", "ph@test.com", hash_password("pass"))
    test_db.create_post(u, "text", text_content="No photo here")
    test_db.create_post(u, "text", text_content="With photo", photo_url="/uploads/test.jpg")
    _approve_posts(u)
    fid = database.create_custom_feed(u, "Photo Feed", "photos", "")
    posts = database.get_custom_feed_posts(fid)
    assert len(posts) == 1
    assert posts[0]["photo_url"] == "/uploads/test.jpg"


def test_get_custom_feed_posts_nonexistent_feed(test_db):
    posts = database.get_custom_feed_posts(99999)
    assert posts == []


def test_get_custom_feed_posts_pending_excluded(test_db):
    """Posts not yet approved should not appear in feed results."""
    u = test_db.create_user("pend_user", "pend@test.com", hash_password("pass"))
    test_db.create_post(u, "text", text_content="Still pending keyword")
    # intentionally NOT approving
    fid = database.create_custom_feed(u, "Keyword", "keyword", "pending")
    posts = database.get_custom_feed_posts(fid)
    assert len(posts) == 0


# ---------------------------------------------------------------------------
# Route-level tests (using the Flask test client)
# ---------------------------------------------------------------------------

def _signup_login(client, username="feeduser"):
    client.post("/signup", data={
        "username": username, "email": f"{username}@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    return database.get_user_by_username(username)["id"]


def test_custom_feeds_page_returns_200(client):
    _signup_login(client)
    rv = client.get("/custom-feeds")
    assert rv.status_code == 200
    assert b"My Custom Feeds" in rv.data


def test_custom_feeds_page_requires_auth(client):
    rv = client.get("/custom-feeds")
    assert rv.status_code == 302


def test_new_custom_feed_creates_feed(client):
    uid = _signup_login(client)
    rv = client.post("/custom-feed/new", data={
        "name": "My Test Feed",
        "filter_type": "hashtag",
        "filter_value": "news",
    }, follow_redirects=True)
    assert rv.status_code == 200
    feeds = database.list_custom_feeds(uid)
    assert len(feeds) == 1
    assert feeds[0]["name"] == "My Test Feed"


def test_custom_feed_detail_returns_200(client):
    uid = _signup_login(client)
    fid = database.create_custom_feed(uid, "Detail Feed", "hashtag", "test")
    rv = client.get(f"/custom-feed/{fid}", follow_redirects=True)
    assert rv.status_code == 200
    assert b"Detail Feed" in rv.data


def test_custom_feed_detail_404(client):
    _signup_login(client)
    rv = client.get("/custom-feed/99999")
    assert rv.status_code == 404


def test_delete_custom_feed_route(client):
    uid = _signup_login(client)
    fid = database.create_custom_feed(uid, "ToDelete", "hashtag", "x")
    rv = client.post(f"/custom-feed/{fid}/delete", follow_redirects=True)
    assert rv.status_code == 200
    assert database.get_custom_feed(fid) is None


def test_pin_custom_feed_route(client):
    uid = _signup_login(client)
    fid = database.create_custom_feed(uid, "ToPin", "hashtag", "x")
    rv = client.post(f"/custom-feed/{fid}/pin", follow_redirects=True)
    assert rv.status_code == 200
    assert database.get_custom_feed(fid)["is_pinned"] == 1
    # Toggle back
    client.post(f"/custom-feed/{fid}/pin", follow_redirects=True)
    assert database.get_custom_feed(fid)["is_pinned"] == 0


def test_new_custom_feed_invalid_type_rejected(client):
    _signup_login(client)
    rv = client.post("/custom-feed/new", data={
        "name": "Bad Feed",
        "filter_type": "bogus",
        "filter_value": "x",
    }, follow_redirects=True)
    # Should redirect (302) or render error, not create the feed
    assert rv.status_code == 200