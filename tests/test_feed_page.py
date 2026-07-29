def test_feed_page_authenticated(client):
    client.post("/signup", data={
        "username": "feeduser", "email": "feed@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/feed")
    assert rv.status_code == 200
    assert b"Feed" in rv.data


def test_feed_page_anonymous_redirected(client):
    rv = client.get("/feed")
    assert rv.status_code == 302
