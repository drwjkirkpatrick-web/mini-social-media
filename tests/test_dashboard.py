def test_dashboard_admin_only(client):
    rv = client.get("/admin/dashboard")
    assert rv.status_code == 302


def test_dashboard_shows_stats(client):
    import database
    from auth import hash_password
    database.create_user("dashadmin", "dash@test.com", hash_password("pass"), role="admin")
    client.post("/login", data={"identifier": "dashadmin", "password": "pass"})
    rv = client.get("/admin/dashboard")
    assert rv.status_code == 200
    assert b"Total Users" in rv.data
