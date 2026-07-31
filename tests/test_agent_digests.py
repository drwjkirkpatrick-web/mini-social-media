"""
Tests for agent daily digest and notifications.
"""
import database
import agent_companion
from auth import hash_password


def test_generate_daily_digest_includes_drafts(test_db):
    owner = database.create_user("digowner", "do@test.com", hash_password("secret"))
    friend = database.create_user("digfriend", "df@test.com", hash_password("secret"))
    fid = database.send_friend_request(owner, friend)
    database.accept_friend_request(fid)
    aid = agent_companion.create_agent_account(owner, "dig_bot", "Digest", "pulsatilla")
    pid = database.create_post(friend, "text", text_content="Digest post", visibility="friends")
    agent_companion.draft_comment(aid, pid, "Draft comment")
    digest = agent_companion.generate_daily_digest(owner)
    assert len(digest["pending_drafts"]) == 1
    assert digest["agent_count"] == 1


def test_digest_route(client, test_db):
    owner = database.create_user("dig2owner", "do2@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "dig2_bot", "Digest2", "pulsatilla")
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.get(f"/agents/{aid}/digest")
    assert resp.status_code == 200
