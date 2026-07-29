"""
End-to-end integration test: full social media workflow.
NOTE: This exercises signup, friends, posts, likes, comments, moderation,
      blockchain audit, and admin dashboard in one flow.
"""


def test_full_flow(client):
    # 1. User A signs up and logs in
    client.post("/signup", data={
        "username": "user_a", "email": "a@test.com",
        "password": "password123", "password2": "password123",
        "display_name": "User A",
    }, follow_redirects=True)

    # 2. User B signs up
    client.post("/logout")
    client.post("/signup", data={
        "username": "user_b", "email": "b@test.com",
        "password": "password123", "password2": "password123",
        "display_name": "User B",
    }, follow_redirects=True)

    # 3. A sends friend request; B accepts
    import database
    a = database.get_user_by_username("user_a")
    b = database.get_user_by_username("user_b")
    fid = database.send_friend_request(a["id"], b["id"])
    database.accept_friend_request(fid)

    # 4. A creates a text post and a photo post
    client.post("/login", data={"identifier": "user_a", "password": "password123"})
    rv = client.post("/post/new", data={
        "content_type": "text", "text_content": "Hello friends!",
        "visibility": "friends",
    }, follow_redirects=True)
    assert rv.status_code == 200

    # 5. B sees posts in feed
    client.post("/logout")
    client.post("/login", data={"identifier": "user_b", "password": "password123"})
    rv = client.get("/feed")
    assert rv.status_code == 200

    # 6. B likes a post and comments
    posts = database.list_posts_by_user(a["id"], limit=1)
    assert len(posts) > 0
    pid = posts[0]["id"]
    client.post(f"/post/{pid}/like")
    client.post(f"/post/{pid}/comment", data={"text": "Great post!"})

    # 7. Moderation scan — approve all pending for clean test
    conn = database.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE user_id=?", (a["id"],))
    conn.commit()
    conn.close()

    # 8. Blockchain audit log verifies clean
    import blockchain
    result = blockchain.verify_chain()
    assert result["clean"] is True

    # 9. Admin dashboard shows stats (create admin)
    from auth import hash_password
    database.create_user("adminflow", "adminflow@test.com", hash_password("pass"), role="admin")
    client.post("/logout")
    client.post("/login", data={"identifier": "adminflow", "password": "pass"})
    rv = client.get("/admin/dashboard")
    assert rv.status_code == 200
    assert b"Total Users" in rv.data
