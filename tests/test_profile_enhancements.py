import database


def test_update_pronouns(test_db):
    uid = test_db.create_user("pronoun", "pro@test.com", "hash")
    test_db.update_user(uid, pronouns="they/them")
    user = test_db.get_user(uid)
    assert user["pronouns"] == "they/them"


def test_update_location(test_db):
    uid = test_db.create_user("locuser", "loc@test.com", "hash")
    test_db.update_user(uid, location="Portland, OR")
    user = test_db.get_user(uid)
    assert user["location"] == "Portland, OR"
