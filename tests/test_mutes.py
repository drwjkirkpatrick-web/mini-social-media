"""
Tests for the Mute Accounts module.
Covers CRUD functions and Flask routes.
"""
import database
from auth import hash_password


# ---------------------------------------------------------------------------
# Database CRUD tests
# ---------------------------------------------------------------------------

def test_mute_user(test_db):
    a = test_db.create_user("muter", "muter@test.com", "hash")
    b = test_db.create_user("mutee", "mutee@test.com", "hash")
    mid = database.mute_user(a, b)
    assert mid is not None


def test_mute_user_idempotent(test_db):
    a = test_db.create_user("muter2", "muter2@test.com", "hash")
    b = test_db.create_user("mutee2", "mutee2@test.com", "hash")
    database.mute_user(a, b)
    database.mute_user(a, b)  # should not raise
    assert database.is_muted(a, b) is True


def test_mute_self_raises(test_db):
    a = test_db.create_user("selfmuter", "sm@test.com", "hash")
    import pytest
    with pytest.raises(ValueError):
        database.mute_user(a, a)


def test_unmute_user(test_db):
    a = test_db.create_user("unmuter", "unmuter@test.com", "hash")
    b = test_db.create_user("unmutee", "unmutee@test.com", "hash")
    database.mute_user(a, b)
    assert database.is_muted(a, b) is True
    removed = database.unmute_user(a, b)
    assert removed is True
    assert database.is_muted(a, b) is False


def test_unmute_user_not_muted(test_db):
    a = test_db.create_user("nm1", "nm1@test.com", "hash")
    b = test_db.create_user("nm2", "nm2@test.com", "hash")
    removed = database.unmute_user(a, b)
    assert removed is False


def test_is_muted(test_db):
    a = test_db.create_user("ismuter", "ismuter@test.com", "hash")
    b = test_db.create_user("ismutee", "ismutee@test.com", "hash")
    assert database.is_muted(a, b) is False
    database.mute_user(a, b)
    assert database.is_muted(a, b) is True
    # Asymmetric — b has not muted a
    assert database.is_muted(b, a) is False


def test_list_muted(test_db):
    a = test_db.create_user("lister", "lister@test.com", "hash")
    b = test_db.create_user("listed1", "listed1@test.com", "hash")
    c = test_db.create_user("listed2", "listed2@test.com", "hash")
    database.mute_user(a, b)
    database.mute_user(a, c)
    muted = database.list_muted(a)
    assert len(muted) == 2
    ids = {m["target_id"] for m in muted}
    assert ids == {b, c}
    # Joined user fields present
    names = {m["username"] for m in muted}
    assert names == {"listed1", "listed2"}


def test_list_muted_empty(test_db):
    a = test_db.create_user("emptylister", "el@test.com", "hash")
    assert database.list_muted(a) == []


def test_get_muted_ids(test_db):
    a = test_db.create_user("setmuter", "setmuter@test.com", "hash")
    b = test_db.create_user("setmutee1", "setmutee1@test.com", "hash")
    c = test_db.create_user("setmutee2", "setmutee2@test.com", "hash")
    database.mute_user(a, b)
    database.mute_user(a, c)
    ids = database.get_muted_ids(a)
    assert isinstance(ids, set)
    assert ids == {b, c}


def test_get_muted_ids_empty(test_db):
    a = test_db.create_user("setempty", "se@test.com", "hash")
    assert database.get_muted_ids(a) == set()


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

def _signup_and_login(client, username, email, password="password123"):
    client.post("/signup", data={
        "username": username, "email": email,
        "password": password, "password2": password,
    }, follow_redirects=True)


def test_mute_route(client):
    _signup_and_login(client, "routemuter", "rm@test.com")
    import database
    target = database.create_user("routetarget", "rt@test.com", hash_password("pass"))
    rv = client.post(f"/user/{target}/mute", follow_redirects=True)
    assert rv.status_code == 200
    assert database.is_muted(database.get_user_by_username("routemuter")["id"], target) is True


def test_unmute_route(client):
    _signup_and_login(client, "routeunmuter", "ru@test.com")
    import database
    me = database.get_user_by_username("routeunmuter")
    target = database.create_user("routeunmutee", "rut@test.com", hash_password("pass"))
    database.mute_user(me["id"], target)
    rv = client.post(f"/user/{target}/unmute", follow_redirects=True)
    assert rv.status_code == 200
    assert database.is_muted(me["id"], target) is False


def test_muted_accounts_settings_page(client):
    _signup_and_login(client, "settingsmuter", "smr@test.com")
    rv = client.get("/settings/muted")
    assert rv.status_code == 200
    assert b"Muted" in rv.data


def test_muted_accounts_page_shows_muted(client):
    _signup_and_login(client, "showmuter", "shm@test.com")
    import database
    me = database.get_user_by_username("showmuter")
    target = database.create_user("showtarget", "sht@test.com", hash_password("pass"))
    database.mute_user(me["id"], target)
    rv = client.get("/settings/muted")
    assert rv.status_code == 200
    assert b"showtarget" in rv.data