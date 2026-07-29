import database


def test_create_and_validate_token(test_db):
    u = test_db.create_user("inviter", "i@test.com", "hash")
    token = database.create_invite_token(u, max_uses=2)
    assert len(token) > 0
    assert database.validate_invite_token(token) is True
    assert database.validate_invite_token(token) is True
    assert database.validate_invite_token(token) is False  # used up
