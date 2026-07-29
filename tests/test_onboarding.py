def test_welcome_page(client):
    client.post("/signup", data={
        "username": "onboard", "email": "onb@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/welcome")
    assert rv.status_code == 200
    assert b"Step" in rv.data
