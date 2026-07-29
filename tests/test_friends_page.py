from auth import hash_password


def test_friends_page_lists_accepted(client):
    import database
    me = database.create_user("fpage", "fpage@test.com", hash_password("pass"))
    friend = database.create_user("ff", "ff@test.com", hash_password("pass"))
    fid = database.send_friend_request(me, friend)
    database.accept_friend_request(fid)
    client.post("/login", data={"identifier": "fpage", "password": "pass"})
    rv = client.get("/friends")
    assert rv.status_code == 200


def test_unfriend_removes_friendship(client):
    import database
    me = database.create_user("ufpage", "ufpage@test.com", hash_password("pass"))
    friend = database.create_user("uff", "uff@test.com", hash_password("pass"))
    fid = database.send_friend_request(me, friend)
    database.accept_friend_request(fid)
    client.post("/login", data={"identifier": "ufpage", "password": "pass"})
    rv = client.post(f"/friend/remove/{fid}", follow_redirects=True)
    assert rv.status_code == 200
