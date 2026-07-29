import database
import pytest


def test_add_comment(test_db):
    u = test_db.create_user("commenter", "c@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Comment here")
    cid = test_db.add_comment(u, p, "Nice post!")
    assert cid > 0
    assert test_db.count_comments(p) == 1


def test_comment_over_1000_rejected(test_db):
    u = test_db.create_user("longcommenter", "lc@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Comment here")
    with pytest.raises(ValueError):
        test_db.add_comment(u, p, "x" * 1001)
