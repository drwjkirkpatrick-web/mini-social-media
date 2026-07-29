import database


def test_extract_hashtags():
    tags = database.extract_hashtags("Hello #world and #python")
    assert "world" in tags
    assert "python" in tags


def test_store_hashtags(test_db):
    u = test_db.create_user("tagger", "t@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="#hello world")
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id=?", (p,))
    conn.commit()
    conn.close()
    database.store_hashtags(p, "#hello world")
    posts = database.get_posts_by_hashtag("hello")
    assert len(posts) >= 1
