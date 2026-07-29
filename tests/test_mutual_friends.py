def test_mutual_page(client):
    import database
    from auth import hash_password
    a = database.create_user("mut_a", "ma@test.com", hash_password("p"))
    b = database.create_user("mut_b", "mb@test.com", hash_password("p"))
    c = database.create_user("mut_c", "mc@test.com", hash_password("p"))
    f1 = database.send_friend_request(a, c)
    database.accept_friend_request(f1)
    f2 = database.send_friend_request(b, c)
    database.accept_friend_request(f2)
    client.post("/login", data={"identifier": "mut_a", "password": "p"})
    rv = client.get(f"/mutual/{b}")
    assert rv.status_code == 200
