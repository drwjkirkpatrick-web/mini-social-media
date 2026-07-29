def test_deactivate_account(client):
    client.post("/signup", data={
        "username": "deact", "email": "d@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    rv = client.post("/settings/deactivate", follow_redirects=True)
    assert rv.status_code == 200
