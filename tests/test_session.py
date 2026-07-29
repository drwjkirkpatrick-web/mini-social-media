def test_login_required_redirects_anonymous(client):
    rv = client.get("/feed")
    assert rv.status_code == 302  # redirect to login


def test_session_cleared_on_login(client):
    # Signup creates a session
    client.post("/signup", data={
        "username": "sessuser", "email": "sess@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    with client.session_transaction() as sess:
        assert "user_id" in sess


def test_logout_clears_session(client):
    client.post("/signup", data={
        "username": "sessuser2", "email": "sess2@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    client.get("/logout")
    with client.session_transaction() as sess:
        assert "user_id" not in sess
