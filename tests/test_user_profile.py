import database


def test_get_user_returns_dict(test_db):
    uid = test_db.create_user("prof", "prof@test.com", "hash")
    user = test_db.get_user(uid)
    assert isinstance(user, dict)
    assert user["username"] == "prof"


def test_update_user_display_name(test_db):
    uid = test_db.create_user("prof2", "prof2@test.com", "hash")
    test_db.update_user(uid, display_name="Pro User")
    user = test_db.get_user(uid)
    assert user["display_name"] == "Pro User"


def test_update_user_ignores_password_hash(test_db):
    uid = test_db.create_user("prof3", "prof3@test.com", "hash")
    old_hash = test_db.get_user(uid)["password_hash"]
    test_db.update_user(uid, password_hash="evil", display_name="OK")
    user = test_db.get_user(uid)
    assert user["password_hash"] == old_hash  # ignored
