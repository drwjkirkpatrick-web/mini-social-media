def test_settings_page(client):
    client.post("/signup", data={
        "username": "themeuser", "email": "th@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/settings")
    assert rv.status_code == 200
    assert b"Theme" in rv.data
