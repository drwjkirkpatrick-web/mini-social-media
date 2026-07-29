import database


def test_like_post(test_db):
    u = test_db.create_user("liker", "liker@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Like me")
    liked = test_db.like_post(u, p)
    assert liked is True
    assert test_db.count_likes(p) == 1


def test_unlike_post(test_db):
    u = test_db.create_user("unliker", "unliker@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Unlike me")
    test_db.like_post(u, p)
    liked = test_db.like_post(u, p)
    assert liked is False
    assert test_db.count_likes(p) == 0
