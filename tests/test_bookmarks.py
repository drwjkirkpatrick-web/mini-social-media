import database


def test_toggle_bookmark(test_db):
    u = test_db.create_user("bookmarker", "b@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Bookmark me")
    added = database.toggle_bookmark(u, p)
    assert added is True
    b = database.get_bookmarks(u)
    assert len(b) == 1
    added2 = database.toggle_bookmark(u, p)
    assert added2 is False
    b2 = database.get_bookmarks(u)
    assert len(b2) == 0
