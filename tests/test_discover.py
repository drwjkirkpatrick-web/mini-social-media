def test_discover_page(client):
    client.post("/signup", data={
        "username": "disc", "email": "disc@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/discover")
    assert rv.status_code == 200
