def test_activity_page(client):
    client.post("/signup", data={
        "username": "actuser", "email": "act@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/activity")
    assert rv.status_code == 200
