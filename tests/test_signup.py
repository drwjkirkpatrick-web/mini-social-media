import database


def test_valid_signup_creates_user(client):
    rv = client.post("/signup", data={
        "username": "newuser", "email": "new@test.com",
        "password": "password123", "password2": "password123",
        "display_name": "New User",
    }, follow_redirects=True)
    assert rv.status_code == 200
    user = database.get_user_by_username("newuser")
    assert user is not None
    assert user["display_name"] == "New User"


def test_duplicate_username_rejected(client):
    client.post("/signup", data={
        "username": "dupuser", "email": "dup1@test.com",
        "password": "password123", "password2": "password123",
    })
    rv = client.post("/signup", data={
        "username": "dupuser", "email": "dup2@test.com",
        "password": "password123", "password2": "password123",
    })
    assert b"already taken" in rv.data


def test_short_password_rejected(client):
    rv = client.post("/signup", data={
        "username": "shortpw", "email": "short@test.com",
        "password": "123", "password2": "123",
    })
    assert rv.status_code == 400
    assert b"at least 8" in rv.data


def test_mismatched_passwords_rejected(client):
    rv = client.post("/signup", data={
        "username": "mismpw", "email": "mism@test.com",
        "password": "password123", "password2": "different123",
    })
    assert rv.status_code == 400
    assert b"do not match" in rv.data
