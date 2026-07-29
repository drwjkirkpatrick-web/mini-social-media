import database


def test_create_page(test_db):
    uid = test_db.create_user("pager", "pager@test.com", "hash")
    pid = test_db.create_page(uid, "About Me", "about", '{"bio":"Hello"}', 0)
    assert pid > 0
    page = test_db.get_page(uid, "about")
    assert page["title"] == "About Me"
    assert page["is_public"] == 0


def test_page_slug_unique_per_user(test_db):
    uid = test_db.create_user("pager2", "pager2@test.com", "hash")
    test_db.create_page(uid, "Page 1", "slug1", "{}")
    # Same user, same slug should conflict
    import sqlite3
    with __import__('pytest').raises((sqlite3.IntegrityError, Exception)):
        test_db.create_page(uid, "Page 2", "slug1", "{}")
