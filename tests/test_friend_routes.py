from auth import hash_password


def test_send_friend_request_route(client):
    client.post("/signup", data={
        "username": "req_sender", "email": "rs@test.com",
        "password": "password123", "password2": "password123",
    }, follow_redirects=True)
    # Create target user manually via DB with hashed password
    import database
    tid = database.create_user("target", "target@test.com", hash_password("pass"))
    rv = client.post(f"/friend/request/{tid}", follow_redirects=True)
    assert rv.status_code == 200


def test_accept_request_route(client):
    import database
    a = database.create_user("accepter", "accepter@test.com", hash_password("pass"))
    b = database.create_user("sender", "sender@test.com", hash_password("pass"))
    fid = database.send_friend_request(b, a)
    # Login as accepter
    client.post("/login", data={"identifier": "accepter", "password": "pass"})
    rv = client.post(f"/friend/accept/{fid}", follow_redirects=True)
    assert rv.status_code == 200
