def test_hermes_webhook_invalid_secret(client):
    rv = client.post("/hermes/webhook", headers={"X-Hermes-Secret": "wrong"}, json={"action": "notify"})
    assert rv.status_code == 403


def test_hermes_webhook_valid_notify(client):
    import database
    from auth import hash_password
    uid = database.create_user("hermesuser", "hermes@test.com", hash_password("pass"))
    rv = client.post("/hermes/webhook",
                     headers={"X-Hermes-Secret": "change-me-in-production"},
                     json={"action": "notify", "user_id": uid, "text": "Hello from Hermes"})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["ok"] is True
    assert data["notified"] == uid
