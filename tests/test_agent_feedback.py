"""
Tests for agent feedback learning loop.
"""
import database
import agent_companion
from auth import hash_password


def test_record_feedback(test_db):
    owner = database.create_user("feedowner", "fo@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "feed_bot", "Feed", "nux_vomica")
    draft_id = database.create_agent_draft(aid, owner, "comment", 1, "Test")
    fid = agent_companion.record_feedback(aid, owner, draft_id, "up", "Good one")
    rows = database.list_agent_feedback(aid)
    assert len(rows) == 1
    assert rows[0]["direction"] == "up"


def test_feedback_route(client, test_db):
    owner = database.create_user("feed2owner", "fo2@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "feed2_bot", "Feed2", "nux_vomica")
    draft_id = database.create_agent_draft(aid, owner, "comment", 1, "Test")
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.post(f"/agents/draft/{draft_id}/feedback", data={"direction": "up", "note": ""}, follow_redirects=True)
    assert resp.status_code == 200
