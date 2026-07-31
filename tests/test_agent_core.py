"""
Tests for Agent Companion Online: account lifecycle, personality, schema.
"""
import pytest
import database
import agent_companion
from auth import hash_password


def _login_user(client, username="owner", password="secret"):
    # Ensure user exists
    user = database.get_user_by_username(username)
    if not user:
        uid = database.create_user(username, f"{username}@test.com", hash_password(password))
        database.update_user(uid, role="user")
    client.post("/login", data={"identifier": username, "password": password}, follow_redirects=True)


def test_agent_account_creation(client, test_db):
    _login_user(client)
    owner = database.get_user_by_username("owner")
    aid = agent_companion.create_agent_account(owner["id"], "spark_bot", "Spark", "phosphorus")
    agent = database.get_user(aid)
    assert agent["role"] == "agent"
    assert agent["username"] == "spark_bot"


def test_agent_profile_created_with_user(client, test_db):
    _login_user(client)
    owner = database.get_user_by_username("owner")
    aid = agent_companion.create_agent_account(owner["id"], "plan_bot", "Plan", "bryonia")
    profile = database.get_agent_profile(aid)
    assert profile["owner_id"] == owner["id"]
    assert profile["remedy_personality"] == "bryonia"
    assert profile["is_active"] == 1


def test_invalid_personality_defaults_to_phosphorus(client, test_db):
    _login_user(client)
    owner = database.get_user_by_username("owner")
    aid = agent_companion.create_agent_account(owner["id"], "default_bot", "Default", "unknown")
    profile = database.get_agent_profile(aid)
    assert profile["remedy_personality"] == "phosphorus"


def test_generate_agent_bio_includes_owner_and_strengths(client, test_db):
    _login_user(client)
    owner = database.get_user_by_username("owner")
    bio = agent_companion.generate_agent_bio(owner, "sulphur")
    assert owner["username"] in bio or owner["display_name"] in bio
    assert "Curious" in bio or "links" in bio


def test_persona_lookup_falls_back(client, test_db):
    p = agent_companion.get_persona("nonexistent")
    assert p["name"] == "Phosphorus"


def test_get_agent_profile_returns_user_join(client, test_db):
    _login_user(client)
    owner = database.get_user_by_username("owner")
    aid = agent_companion.create_agent_account(owner["id"], "join_bot", "Join", "pulsatilla")
    profile = database.get_agent_profile(aid)
    assert "display_name" in profile
    assert "role" in profile


def test_list_agent_profiles_for_owner(client, test_db):
    _login_user(client)
    owner = database.get_user_by_username("owner")
    agent_companion.create_agent_account(owner["id"], "a1", "A1", "phosphorus")
    agent_companion.create_agent_account(owner["id"], "a2", "A2", "bryonia")
    profiles = database.list_agent_profiles_for_owner(owner["id"])
    assert len(profiles) == 2


def test_create_agent_route(client, test_db):
    _login_user(client)
    resp = client.post("/agents/new", data={
        "username": "route_bot",
        "display_name": "Route Bot",
        "remedy_personality": "nux_vomica",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Agent companion created" in resp.data


def test_create_agent_duplicate_username_fails(client, test_db):
    _login_user(client)
    client.post("/agents/new", data={
        "username": "dup_bot",
        "display_name": "Dup",
        "remedy_personality": "phosphorus",
    }, follow_redirects=True)
    resp = client.post("/agents/new", data={
        "username": "dup_bot",
        "display_name": "Dup2",
        "remedy_personality": "phosphorus",
    }, follow_redirects=True)
    assert b"already taken" in resp.data


def test_agent_detail_visible_to_owner(client, test_db):
    _login_user(client)
    owner = database.get_user_by_username("owner")
    aid = agent_companion.create_agent_account(owner["id"], "detail_bot", "Detail", "calcarea_carbonica")
    resp = client.get(f"/agents/{aid}")
    assert resp.status_code == 200
    assert b"Careful Archivist" in resp.data or b"Calcarea" in resp.data


def test_agent_detail_404_for_nonexistent(client, test_db):
    _login_user(client)
    resp = client.get("/agents/99999")
    assert resp.status_code == 404
