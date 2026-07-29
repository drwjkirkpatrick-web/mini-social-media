def test_authenticated_create_text_post(client):
    client.post("/signup", data={
        "username": "createuser", "email": "create@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.post("/post/new", data={
        "content_type": "text", "text_content": "A test post",
        "visibility": "friends",
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert b"Post created" in rv.data or b"pending" in rv.data


def test_anonymous_create_post_redirected(client):
    rv = client.post("/post/new", data={
        "content_type": "text", "text_content": "Should fail",
    })
    assert rv.status_code == 302


def test_text_over_2000_rejected(client):
    client.post("/signup", data={
        "username": "longuser", "email": "long@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.post("/post/new", data={
        "content_type": "text", "text_content": "x" * 2001,
    })
    assert rv.status_code == 400
