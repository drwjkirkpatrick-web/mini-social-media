def test_logout_clears_and_redirects(client):
    client.post("/signup", data={
        "username": "logoutuser", "email": "out@test.com",
        "password": "password123", "password2": "password123",
    })
    rv = client.get("/logout", follow_redirects=True)
    assert rv.status_code == 200
    with client.session_transaction() as sess:
        assert "user_id" not in sess
