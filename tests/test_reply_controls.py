"""
Tests for the Reply Controls module (v0.6.0).

Covers:
  - set_reply_control / get_reply_control (default 'friends')
  - can_reply for each scope (everyone/friends/mentioned/nobody)
  - POST /post/<id>/reply-control sets scope
  - commenting is blocked when scope is 'nobody'
"""

import database
from auth import hash_password


# ---------------------------------------------------------------------------
# Database-level CRUD tests
# ---------------------------------------------------------------------------

def test_get_reply_control_default_is_friends(test_db):
    u = test_db.create_user("rcowner", "rc@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    # No control set yet → default is 'friends'
    assert test_db.get_reply_control(p) == "friends"


def test_set_reply_control_returns_id(test_db):
    u = test_db.create_user("rcset", "rset@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    rcid = test_db.set_reply_control(p, "nobody")
    assert rcid > 0
    assert test_db.get_reply_control(p) == "nobody"


def test_set_reply_control_upsert(test_db):
    """Setting a control twice updates the existing row (UNIQUE post_id)."""
    u = test_db.create_user("rcup", "rcup@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    test_db.set_reply_control(p, "nobody")
    test_db.set_reply_control(p, "everyone")
    assert test_db.get_reply_control(p) == "everyone"


# ---------------------------------------------------------------------------
# can_reply tests for each scope
# ---------------------------------------------------------------------------

def test_can_reply_everyone(test_db):
    u = test_db.create_user("rcevery", "rcevery@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    test_db.set_reply_control(p, "everyone")
    assert test_db.can_reply(p, 999, is_friend=False, is_mentioned=False) is True


def test_can_reply_friends_allowed(test_db):
    u = test_db.create_user("rcfr", "rcfr@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    test_db.set_reply_control(p, "friends")
    # is_friend=True → allowed
    assert test_db.can_reply(p, 999, is_friend=True, is_mentioned=False) is True


def test_can_reply_friends_blocked_for_non_friend(test_db):
    u = test_db.create_user("rcfr2", "rcfr2@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    test_db.set_reply_control(p, "friends")
    # is_friend=False → blocked
    assert test_db.can_reply(p, 999, is_friend=False, is_mentioned=False) is False


def test_can_reply_mentioned_allowed(test_db):
    u = test_db.create_user("rcment", "rcment@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    test_db.set_reply_control(p, "mentioned")
    # is_mentioned=True → allowed
    assert test_db.can_reply(p, 999, is_friend=False, is_mentioned=True) is True


def test_can_reply_mentioned_blocked(test_db):
    u = test_db.create_user("rcment2", "rcment2@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    test_db.set_reply_control(p, "mentioned")
    # is_mentioned=False → blocked
    assert test_db.can_reply(p, 999, is_friend=False, is_mentioned=False) is False


def test_can_reply_nobody_always_false(test_db):
    u = test_db.create_user("rcno", "rcno@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    test_db.set_reply_control(p, "nobody")
    # Even if friend and mentioned → blocked
    assert test_db.can_reply(p, 999, is_friend=True, is_mentioned=True) is False


def test_can_reply_default_friends_blocks_non_friend(test_db):
    """Default scope (no row) behaves like 'friends'."""
    u = test_db.create_user("rcdef", "rcdef@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Reply here")
    assert test_db.can_reply(p, 999, is_friend=False, is_mentioned=False) is False
    assert test_db.can_reply(p, 999, is_friend=True, is_mentioned=False) is True


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

def test_reply_control_route_sets_scope(client):
    """POST /post/<id>/reply-control sets the reply scope."""
    client.post("/signup", data={
        "username": "rcroute", "email": "rcroute@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    import database as db
    u = db.get_user_by_username("rcroute")
    p = db.create_post(u["id"], "text", text_content="My post")
    rv = client.post(f"/post/{p}/reply-control", data={"reply_scope": "nobody"},
                     follow_redirects=True)
    assert rv.status_code == 200
    assert db.get_reply_control(p) == "nobody"


def test_reply_control_route_rejects_non_owner(client):
    """Only the post owner can change reply settings."""
    import database as db
    # Owner (create_user returns the int user id)
    owner_id = db.create_user("rcown", "rcown@test.com", hash_password("password123"))
    # Other user who will be logged in
    other_id = db.create_user("rcother", "rcother@test.com", hash_password("password123"))
    p = db.create_post(owner_id, "text", text_content="Owner post")
    # Login as other user
    client.post("/login", data={"identifier": "rcother", "password": "password123"})
    rv = client.post(f"/post/{p}/reply-control", data={"reply_scope": "everyone"},
                     follow_redirects=True)
    assert rv.status_code == 200
    # Scope should NOT have changed (stays default)
    assert db.get_reply_control(p) == "friends"


def test_comment_blocked_when_scope_nobody(client):
    """Commenting is blocked when the post's reply scope is 'nobody'."""
    import database as db
    # Post owner
    owner_id = db.create_user("rcblk", "rcblk@test.com", hash_password("password123"))
    # Commenter (a friend) — logged in
    commenter_id = db.create_user("rccom", "rccom@test.com", hash_password("password123"))
    p = db.create_post(owner_id, "text", text_content="Nobody can reply")
    db.set_reply_control(p, "nobody")
    # Make them friends so the only blocker is the reply scope
    fid = db.send_friend_request(commenter_id, owner_id)
    db.accept_friend_request(fid)
    # Login as commenter
    client.post("/login", data={"identifier": "rccom", "password": "password123"})
    rv = client.post(f"/post/{p}/comment", data={"text": "Hello!"},
                     follow_redirects=True)
    assert rv.status_code == 200
    # Comment should NOT have been added
    assert db.count_comments(p) == 0


def test_comment_allowed_when_scope_friends_and_friend(client):
    """Commenting works when scope is 'friends' and commenter is a friend."""
    import database as db
    owner_id = db.create_user("rcok", "rcok@test.com", hash_password("password123"))
    commenter_id = db.create_user("rccom2", "rccom2@test.com", hash_password("password123"))
    p = db.create_post(owner_id, "text", text_content="Friends can reply")
    db.set_reply_control(p, "friends")
    fid = db.send_friend_request(commenter_id, owner_id)
    db.accept_friend_request(fid)
    client.post("/login", data={"identifier": "rccom2", "password": "password123"})
    rv = client.post(f"/post/{p}/comment", data={"text": "Nice!"},
                     follow_redirects=True)
    assert rv.status_code == 200
    assert db.count_comments(p) == 1