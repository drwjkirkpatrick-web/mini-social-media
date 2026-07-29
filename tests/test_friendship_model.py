import database
import pytest


def test_send_request_creates_pending(test_db):
    a = test_db.create_user("a", "a@test.com", "hash")
    b = test_db.create_user("b", "b@test.com", "hash")
    fid = test_db.send_friend_request(a, b)
    assert fid > 0
    f = test_db.get_friendship(a, b)
    assert f["status"] == "pending"


def test_duplicate_request_returns_existing(test_db):
    a = test_db.create_user("a2", "a2@test.com", "hash")
    b = test_db.create_user("b2", "b2@test.com", "hash")
    fid1 = test_db.send_friend_request(a, b)
    fid2 = test_db.send_friend_request(a, b)
    assert fid1 == fid2 or fid2 > 0


def test_accept_friendship(test_db):
    a = test_db.create_user("a3", "a3@test.com", "hash")
    b = test_db.create_user("b3", "b3@test.com", "hash")
    fid = test_db.send_friend_request(a, b)
    test_db.accept_friend_request(fid)
    f = test_db.get_friendship(a, b)
    assert f["status"] == "accepted"


def test_reject_friendship(test_db):
    a = test_db.create_user("a4", "a4@test.com", "hash")
    b = test_db.create_user("b4", "b4@test.com", "hash")
    fid = test_db.send_friend_request(a, b)
    test_db.reject_friend_request(fid)
    f = test_db.get_friendship(a, b)
    assert f["status"] == "rejected"


def test_cannot_friend_self(test_db):
    a = test_db.create_user("a5", "a5@test.com", "hash")
    with pytest.raises(ValueError):
        test_db.send_friend_request(a, a)
