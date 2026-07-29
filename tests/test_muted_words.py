import database


def test_add_and_list_muted_word(test_db):
    u = test_db.create_user("muter", "m@test.com", "hash")
    wid = database.add_muted_word(u, "spoilers")
    assert wid > 0
    words = database.list_muted_words(u)
    assert len(words) == 1
    assert words[0]["word"] == "spoilers"
    assert words[0]["user_id"] == u


def test_add_duplicate_ignored(test_db):
    u = test_db.create_user("muter2", "m2@test.com", "hash")
    database.add_muted_word(u, "spam")
    database.add_muted_word(u, "spam")
    words = database.list_muted_words(u)
    assert len(words) == 1


def test_remove_muted_word(test_db):
    u = test_db.create_user("muter3", "m3@test.com", "hash")
    database.add_muted_word(u, "junk")
    assert database.remove_muted_word(u, "junk") is True
    assert database.remove_muted_word(u, "junk") is False  # already gone
    words = database.list_muted_words(u)
    assert len(words) == 0


def test_get_muted_word_list(test_db):
    u = test_db.create_user("muter4", "m4@test.com", "hash")
    database.add_muted_word(u, "politics")
    database.add_muted_word(u, "ads")
    word_list = database.get_muted_word_list(u)
    assert "politics" in word_list
    assert "ads" in word_list
    assert len(word_list) == 2


def test_is_word_muted_case_insensitive(test_db):
    u = test_db.create_user("muter5", "m5@test.com", "hash")
    database.add_muted_word(u, "Spoilers")
    assert database.is_word_muted(u, "This post contains spoilers!") is True
    assert database.is_word_muted(u, "SPOILERS everywhere") is True
    assert database.is_word_muted(u, "no trigger words here") is False


def test_is_word_muted_substring(test_db):
    u = test_db.create_user("muter6", "m6@test.com", "hash")
    database.add_muted_word(u, "cat")
    # Substring match — "category" contains "cat"
    assert database.is_word_muted(u, "This is a category") is True
    assert database.is_word_muted(u, "just a dog") is False


def test_is_word_muted_no_words(test_db):
    u = test_db.create_user("muter7", "m7@test.com", "hash")
    assert database.is_word_muted(u, "anything") is False
    assert database.is_word_muted(u, "") is False


def test_is_word_muted_empty_text(test_db):
    u = test_db.create_user("muter8", "m8@test.com", "hash")
    database.add_muted_word(u, "test")
    assert database.is_word_muted(u, "") is False
    assert database.is_word_muted(u, None) is False


def test_words_isolated_per_user(test_db):
    u1 = test_db.create_user("muter9", "m9@test.com", "hash")
    u2 = test_db.create_user("muter10", "m10@test.com", "hash")
    database.add_muted_word(u1, "private")
    assert len(database.list_muted_words(u1)) == 1
    assert len(database.list_muted_words(u2)) == 0
    assert database.is_word_muted(u2, "private stuff") is False


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

def test_muted_words_page_requires_auth(client):
    rv = client.get("/settings/muted-words")
    assert rv.status_code == 302  # redirect to login


def test_muted_words_page_authenticated(client):
    client.post("/signup", data={
        "username": "mwuser", "email": "mw@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/settings/muted-words")
    assert rv.status_code == 200
    assert b"Muted Words" in rv.data


def test_add_muted_word_route(client):
    client.post("/signup", data={
        "username": "mwuser2", "email": "mw2@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.post("/settings/muted-words/add", data={"word": "spoilers"},
                     follow_redirects=True)
    assert rv.status_code == 200
    rv = client.get("/settings/muted-words")
    assert b"spoilers" in rv.data


def test_add_muted_word_empty_redirects(client):
    client.post("/signup", data={
        "username": "mwuser3", "email": "mw3@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.post("/settings/muted-words/add", data={"word": ""},
                     follow_redirects=True)
    assert rv.status_code == 200


def test_remove_muted_word_route(client):
    client.post("/signup", data={
        "username": "mwuser4", "email": "mw4@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    # Add a word via route
    client.post("/settings/muted-words/add", data={"word": "junk"},
                follow_redirects=True)
    # Fetch the page to get the word's id
    from flask import session as flask_session
    with client.session_transaction() as sess:
        uid = sess["user_id"]
    words = database.list_muted_words(uid)
    assert len(words) == 1
    wid = words[0]["id"]
    # Remove it via route
    rv = client.post(f"/settings/muted-words/{wid}/remove",
                     follow_redirects=True)
    assert rv.status_code == 200
    assert database.list_muted_words(uid) == []


def test_remove_nonexistent_muted_word(client):
    client.post("/signup", data={
        "username": "mwuser5", "email": "mw5@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.post("/settings/muted-words/99999/remove",
                     follow_redirects=True)
    assert rv.status_code == 200  # flashes not found, redirects