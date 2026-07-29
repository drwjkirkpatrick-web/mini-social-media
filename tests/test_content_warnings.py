def test_content_warning_field(client):
    client.post("/signup", data={
        "username": "cwuser", "email": "cw@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/post/new")
    assert rv.status_code == 200
