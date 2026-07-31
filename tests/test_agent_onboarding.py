"""
Tests for agent onboarding wizard.
"""
import database
import agent_companion
from auth import hash_password


def test_onboarding_route(client, test_db):
    owner = database.create_user("onboardowner", "obo@test.com", hash_password("secret"))
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.get("/agents/onboarding")
    assert resp.status_code == 200
    assert b"Agent Companion Setup" in resp.data


def test_onboarding_creates_agent_via_form(client, test_db):
    owner = database.create_user("onboardowner2", "obo2@test.com", hash_password("secret"))
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.post("/agents/new", data={
        "username": "onboard_bot",
        "display_name": "Onboard Bot",
        "remedy_personality": "pulsatilla",
    }, follow_redirects=True)
    assert resp.status_code == 200
    agent = database.get_user_by_username("onboard_bot")
    assert agent["role"] == "agent"
