def test_valid_login_redirects_to_feed(client):
    client.post("/signup", data={
        "username": "loguser", "email": "log@test.com",
        "password": "password123", "password2": "password123",
    })
    rv = client.post("/login", data={
        "identifier": "loguser", "password": "password123",
    }, follow_redirects=True)
    assert b"Feed" in rv.data or b"feed" in rv.data.lower()


def test_wrong_password_stays_on_login(client):
    client.post("/signup", data={
        "username": "loguser2", "email": "log2@test.com",
        "password": "password123", "password2": "password123",
    })
    rv = client.post("/login", data={
        "identifier": "loguser2", "password": "wrongpass",
    })
    assert rv.status_code == 401


def test_nonexistent_user_stays_on_login(client):
    rv = client.post("/login", data={
        "identifier": "nobody", "password": "password123",
    })
    assert rv.status_code == 401
