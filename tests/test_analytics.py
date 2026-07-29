def test_stats_page(client):
    import database
    from auth import hash_password
    u = database.create_user("stats", "st@test.com", hash_password("p"))
    p = database.create_post(u, "text", text_content="Stats post")
    conn = database.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id=?", (p,))
    conn.commit()
    conn.close()
    client.post("/login", data={"identifier": "stats", "password": "p"})
    rv = client.get(f"/post/{p}/stats")
    assert rv.status_code == 200
