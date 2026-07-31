"""
Tests for agent public profile and agent-to-agent protocol.
"""
import database
import agent_companion
from auth import hash_password


def test_agent_detail_requires_owner_or_friend(client, test_db):
    owner = database.create_user("profowner", "pro@test.com", hash_password("secret"))
    stranger = database.create_user("stranger", "s@test.com", hash_password("secret"))
    friend = database.create_user("proffriend", "pf@test.com", hash_password("secret"))
    fid = database.send_friend_request(owner, friend)
    database.accept_friend_request(fid)
    aid = agent_companion.create_agent_account(owner, "prof_bot", "Prof", "sulphur")
    # Stranger cannot view
    with client.session_transaction() as sess:
        sess["user_id"] = stranger
        sess["role"] = "user"
    resp = client.get(f"/agents/{aid}")
    assert resp.status_code == 403
    # Friend can view
    with client.session_transaction() as sess:
        sess["user_id"] = friend
        sess["role"] = "user"
    resp = client.get(f"/agents/{aid}")
    assert resp.status_code == 200


def test_agent_public_profile_shows_personality(client, test_db):
    owner = database.create_user("pubowner", "pubo@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "pub_bot", "Pub", "phosphorus")
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.get(f"/agents/{aid}")
    assert b"Charismatic Communicator" in resp.data or b"phosphorus" in resp.data
