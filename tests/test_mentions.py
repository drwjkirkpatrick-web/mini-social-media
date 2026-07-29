def test_mentions_page(client):
    client.post("/signup", data={
        "username": "mentionme", "email": "mnt@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/mentions")
    assert rv.status_code == 200
