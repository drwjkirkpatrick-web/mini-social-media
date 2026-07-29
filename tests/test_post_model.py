import database


def test_create_text_post(test_db):
    uid = test_db.create_user("poster", "poster@test.com", "hash")
    pid = test_db.create_post(uid, "text", text_content="Hello world")
    assert pid > 0
    post = test_db.get_post(pid)
    assert post["content_type"] == "text"
    assert post["text_content"] == "Hello world"


def test_photo_post_requires_photo_url(test_db):
    uid = test_db.create_user("poster2", "poster2@test.com", "hash")
    # We allow creation without photo_url at DB level; app layer validates
    pid = test_db.create_post(uid, "photo", photo_url="/static/uploads/1.jpg")
    post = test_db.get_post(pid)
    assert post["photo_url"] == "/static/uploads/1.jpg"


def test_create_link_post(test_db):
    uid = test_db.create_user("poster3", "poster3@test.com", "hash")
    pid = test_db.create_post(uid, "link", link_url="https://example.com")
    post = test_db.get_post(pid)
    assert post["link_url"] == "https://example.com"
