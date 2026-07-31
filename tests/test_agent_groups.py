"""
Tests for agent group chat participation.
"""
import database
import agent_companion
from auth import hash_password


def test_join_group_chat_requires_can_message(test_db):
    owner = database.create_user("groupowner", "go@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "group_bot", "Group", "bryonia")
    gid = database.create_message_group("Test Group", owner)
    database.add_to_group(gid, owner)
    assert agent_companion.join_group_chat(aid, gid, can_write=True) is True


def test_join_group_chat_fails_when_messaging_disabled(test_db):
    owner = database.create_user("groupowner2", "go2@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "group2_bot", "Group2", "bryonia")
    database.update_agent_profile(aid, owner, can_message=0)
    gid = database.create_message_group("Test Group2", owner)
    assert agent_companion.join_group_chat(aid, gid) is False


def test_agent_group_membership_crud(test_db):
    owner = database.create_user("groupowner3", "go3@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "group3_bot", "Group3", "bryonia")
    gid = database.create_message_group("Test Group3", owner)
    database.add_to_group(gid, owner)
    agent_companion.join_group_chat(aid, gid)
    members = database.list_agent_group_members(aid)
    assert any(m["group_id"] == gid for m in members)
    assert database.remove_agent_group_member(aid, gid) is True


def test_group_join_route(client, test_db):
    owner = database.create_user("groupowner4", "go4@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "group4_bot", "Group4", "bryonia")
    gid = database.create_message_group("Test Group4", owner)
    database.add_to_group(gid, owner)
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.post(f"/agents/{aid}/group/{gid}/join", data={"can_write": 1}, follow_redirects=True)
    assert resp.status_code == 200
