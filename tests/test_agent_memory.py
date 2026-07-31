"""
Tests for agent memory bank CRUD.
"""
import database
import agent_companion
from auth import hash_password


def _owner(test_db):
    return database.create_user("memowner", "mo@test.com", hash_password("secret"))


def test_remember_and_recall(test_db):
    owner = _owner(test_db)
    friend = database.create_user("memfriend", "mf@test.com", hash_password("secret"))
    agent_companion.remember(owner, friend, "preference", "tea", "loves chai", 5)
    rows = agent_companion.recall(owner, friend, "preference")
    assert len(rows) == 1
    assert rows[0]["value"] == "loves chai"


def test_recall_filtered_by_category(test_db):
    owner = _owner(test_db)
    agent_companion.remember(owner, None, "general", "motto", "keep it cozy")
    agent_companion.remember(owner, None, "work", "focus", "morning")
    rows = agent_companion.recall(owner, category="work")
    assert len(rows) == 1
    assert rows[0]["key"] == "focus"


def test_forget_removes_owner_memory(test_db):
    owner = _owner(test_db)
    mid = agent_companion.remember(owner, None, "test", "k", "v")
    assert agent_companion.forget(owner, mid) is True
    assert agent_companion.forget(owner, mid) is False


def test_cannot_forget_other_owner_memory(test_db):
    owner = _owner(test_db)
    other = database.create_user("otherowner", "oo@test.com", hash_password("secret"))
    mid = agent_companion.remember(owner, None, "test", "k", "v")
    assert agent_companion.forget(other, mid) is False


def test_memory_route(client, test_db):
    owner = _owner(test_db)
    aid = agent_companion.create_agent_account(owner, "mem_bot", "Mem", "calcarea_carbonica")
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.get(f"/agents/{aid}/memory")
    assert resp.status_code == 200
