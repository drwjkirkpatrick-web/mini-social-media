def test_export_requires_auth(client):
    rv = client.get("/settings/export")
    assert rv.status_code == 302  # redirect to login


def test_export_authenticated(client):
    client.post("/signup", data={
        "username": "exporter", "email": "exp@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.get("/settings/export")
    assert rv.status_code == 200
    assert rv.content_type == "application/json"
