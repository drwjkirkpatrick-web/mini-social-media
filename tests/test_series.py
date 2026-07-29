import database


def test_create_series_and_add_posts(test_db):
    u = test_db.create_user("series_user", "su@test.com", "hash")
    sid = database.create_series(u, "My Vacation", "Summer trip")
    assert sid > 0
    p1 = test_db.create_post(u, "text", text_content="Day 1")
    p2 = test_db.create_post(u, "text", text_content="Day 2")
    database.add_post_to_series(sid, p1, 0)
    database.add_post_to_series(sid, p2, 1)
    posts = database.get_series_posts(sid)
    assert len(posts) == 2
    assert posts[0]["text_content"] == "Day 1"
