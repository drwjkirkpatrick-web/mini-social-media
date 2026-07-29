"""
Tests for the v0.6.0 Content Labels module.
NOTE: Uses the test_db fixture (temp-file DB) and client fixture (Flask test client).
WHY: Ensures labels CRUD and routes work in isolation.
"""

import database


def _approve(post_id):
    """Helper: mark a post approved so it shows in feeds/label queries."""
    conn = database.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id=?", (post_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Database CRUD tests
# ---------------------------------------------------------------------------

def test_add_and_get_post_label(test_db):
    u = test_db.create_user("label_a", "la@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Sensitive post")
    lid = database.add_post_label(p, "sensitive")
    assert isinstance(lid, int) and lid > 0
    labels = database.get_post_labels(p)
    assert len(labels) == 1
    assert labels[0]["label_type"] == "sensitive"
    assert labels[0]["post_id"] == p


def test_add_invalid_label_type_raises(test_db):
    u = test_db.create_user("label_b", "lb@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Post")
    try:
        database.add_post_label(p, "not_a_real_label")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_get_post_labels_empty(test_db):
    u = test_db.create_user("label_c", "lc@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="No labels")
    labels = database.get_post_labels(p)
    assert labels == []


def test_multiple_labels_on_post(test_db):
    u = test_db.create_user("label_d", "ld@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Multi label")
    database.add_post_label(p, "sensitive")
    database.add_post_label(p, "spoiler")
    database.add_post_label(p, "ai_generated")
    labels = database.get_post_labels(p)
    assert len(labels) == 3
    types = {l["label_type"] for l in labels}
    assert types == {"sensitive", "spoiler", "ai_generated"}


def test_get_user_label_prefs_empty(test_db):
    u = test_db.create_user("label_e", "le@test.com", "hash")
    prefs = database.get_user_label_prefs(u)
    assert prefs == {}


def test_set_and_get_user_label_pref(test_db):
    u = test_db.create_user("label_f", "lf@test.com", "hash")
    database.set_user_label_pref(u, "nsfw", "hide")
    database.set_user_label_pref(u, "spoiler", "show")
    prefs = database.get_user_label_prefs(u)
    assert prefs["nsfw"] == "hide"
    assert prefs["spoiler"] == "show"


def test_set_user_label_pref_upsert(test_db):
    u = test_db.create_user("label_g", "lg@test.com", "hash")
    database.set_user_label_pref(u, "violence", "warn")
    assert database.get_user_label_prefs(u)["violence"] == "warn"
    # Update same pref to a new action
    database.set_user_label_pref(u, "violence", "hide")
    prefs = database.get_user_label_prefs(u)
    assert prefs["violence"] == "hide"
    assert len(prefs) == 1  # no duplicate row


def test_set_user_label_pref_validates_action(test_db):
    u = test_db.create_user("label_h", "lh@test.com", "hash")
    try:
        database.set_user_label_pref(u, "sensitive", "delete")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_get_visible_posts_no_prefs_shows_all(test_db):
    u = test_db.create_user("label_i", "li@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Visible")
    _approve(p)
    database.add_post_label(p, "sensitive")
    posts = database.get_visible_posts_with_labels(u, limit=50)
    assert any(post["id"] == p for post in posts)
    labeled = [post for post in posts if post["id"] == p][0]
    assert "sensitive" in labeled["labels"]


def test_get_visible_posts_hides_labeled_posts(test_db):
    u = test_db.create_user("label_j", "lj@test.com", "hash")
    # User hides nsfw content
    database.set_user_label_pref(u, "nsfw", "hide")
    # Post with nsfw label
    p_hidden = test_db.create_post(u, "text", text_content="NSFW post")
    _approve(p_hidden)
    database.add_post_label(p_hidden, "nsfw")
    # Post without nsfw label
    p_visible = test_db.create_post(u, "text", text_content="Clean post")
    _approve(p_visible)
    posts = database.get_visible_posts_with_labels(u, limit=50)
    post_ids = [post["id"] for post in posts]
    assert p_visible in post_ids
    assert p_hidden not in post_ids


def test_get_visible_posts_warn_does_not_hide(test_db):
    u = test_db.create_user("label_k", "lk@test.com", "hash")
    database.set_user_label_pref(u, "spoiler", "warn")
    p = test_db.create_post(u, "text", text_content="Spoiler post")
    _approve(p)
    database.add_post_label(p, "spoiler")
    posts = database.get_visible_posts_with_labels(u, limit=50)
    assert any(post["id"] == p for post in posts)


def test_get_visible_posts_show_does_not_hide(test_db):
    u = test_db.create_user("label_l", "ll@test.com", "hash")
    database.set_user_label_pref(u, "political", "show")
    p = test_db.create_post(u, "text", text_content="Political post")
    _approve(p)
    database.add_post_label(p, "political")
    posts = database.get_visible_posts_with_labels(u, limit=50)
    assert any(post["id"] == p for post in posts)


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

def test_label_settings_page(client):
    client.post("/signup", data={
        "username": "labeluser", "email": "label@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/settings/labels")
    assert rv.status_code == 200
    assert b"Content Label" in rv.data
    assert b"sensitive" in rv.data
    assert b"ai_generated" in rv.data


def test_label_settings_update(client):
    client.post("/signup", data={
        "username": "labeluser2", "email": "label2@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.post("/settings/labels", data={
        "sensitive": "hide",
        "nsfw": "warn",
        "spoiler": "show",
        "violence": "warn",
        "political": "show",
        "ai_generated": "hide",
    }, follow_redirects=True)
    assert rv.status_code == 200
    # Verify prefs were persisted
    conn = database.get_connection()
    row = conn.execute(
        "SELECT action FROM user_label_prefs WHERE label_type='sensitive'"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["action"] == "hide"


def test_add_label_to_post_route(client):
    client.post("/signup", data={
        "username": "labeluser3", "email": "label3@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    # Create a post via the app route
    rv = client.post("/post/new", data={
        "content_type": "text",
        "text_content": "Post to label",
    }, follow_redirects=True)
    # Find the post id
    conn = database.get_connection()
    row = conn.execute(
        "SELECT id FROM posts WHERE text_content='Post to label' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert row is not None
    post_id = row["id"]
    # Add a label
    rv = client.post(f"/post/{post_id}/label", data={
        "label_type": "sensitive",
    }, follow_redirects=True)
    assert rv.status_code == 200
    # Verify label was persisted
    labels = database.get_post_labels(post_id)
    assert len(labels) == 1
    assert labels[0]["label_type"] == "sensitive"