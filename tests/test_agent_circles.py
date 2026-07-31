"""
Tests for agent circle steward feature.
"""
import database
import agent_companion
from auth import hash_password


def test_suggest_circle_move_returns_circle(test_db):
    owner = database.create_user("csowner", "cso@test.com", hash_password("secret"))
    friend = database.create_user("csfriend", "csf@test.com", hash_password("secret"))
    database.create_circle(owner, "work circle")
    rec = agent_companion.suggest_circle_move(owner, friend, "bryonia")
    assert rec is not None
    assert "work" in rec["circle_name"].lower()


def test_suggest_circle_move_returns_none_without_circles(test_db):
    owner = database.create_user("nocircowner", "nco@test.com", hash_password("secret"))
    friend = database.create_user("nocircfriend", "ncf@test.com", hash_password("secret"))
    rec = agent_companion.suggest_circle_move(owner, friend, "bryonia")
    assert rec is None
