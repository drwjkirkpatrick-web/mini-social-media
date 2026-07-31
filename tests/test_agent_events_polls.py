"""
Tests for agent event and poll suggestion routes.
"""
import database
import agent_companion
from auth import hash_password


def _setup(client, test_db):
    owner = database.create_user("epowner", "ep@test.com", hash_password("secret"))
    f1 = database.create_user("epf1", "epf1@test.com", hash_password("secret"))
    f2 = database.create_user("epf2", "epf2@test.com", hash_password("secret"))
    for f in (f1, f2):
        fid = database.send_friend_request(owner, f)
        database.accept_friend_request(fid)
    aid = agent_companion.create_agent_account(owner, "ep_bot", "EP", "bryonia")
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    return owner, aid


def test_event_plan_route(client, test_db):
    owner, aid = _setup(client, test_db)
    resp = client.get(f"/agents/{aid}/event-plan")
    assert resp.status_code == 200
    assert b"Focused Co-Working" in resp.data or b"title" in resp.data


def test_poll_suggest_route(client, test_db):
    owner, aid = _setup(client, test_db)
    resp = client.get(f"/agents/{aid}/poll-suggest")
    assert resp.status_code == 200
    assert b"Poll Suggestion" in resp.data or b"?" in resp.data


def test_icebreaker_suggestion_route(client, test_db):
    owner, aid = _setup(client, test_db)
    friend = database.list_friends(owner)[0]["id"]
    resp = client.get(f"/agents/{aid}/icebreaker/{friend}")
    assert resp.status_code == 200
