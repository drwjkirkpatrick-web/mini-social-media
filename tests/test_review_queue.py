def test_moderation_queue_admin_only(client):
    # Anonymous should be redirected
    rv = client.get("/admin/moderation")
    assert rv.status_code == 302


def test_moderation_queue_for_admin(client):
    # Signup as admin doesn't set role=admin by default;
    # create admin via DB
    import database
    from auth import hash_password
    database.create_user("adminuser", "admin@test.com", hash_password("pass"), role="admin")
    client.post("/login", data={"identifier": "adminuser", "password": "pass"})
    rv = client.get("/admin/moderation")
    assert rv.status_code == 200
