"""
Tests for agent tone check and conflict de-escalation.
"""
import database
import agent_companion
from auth import hash_password


def test_moderate_tone_flags_all_caps(test_db):
    result = agent_companion.moderate_tone("WHY IS THIS HAPPENING", "nux_vomica")
    assert result["flagged"] is True
    assert "ALL_CAPS" in result["flags"]


def test_moderate_tone_flags_harsh_words(test_db):
    result = agent_companion.moderate_tone("You are stupid and wrong", "nux_vomica")
    assert result["flagged"] is True
    assert result["score"] >= 2


def test_moderate_tone_passes_calm_text(test_db):
    result = agent_companion.moderate_tone("Thanks for sharing your perspective.", "bryonia")
    assert result["flagged"] is False
    assert result["score"] == 0


def test_detect_conflict_thread_flags_heated_comments(test_db):
    owner = database.create_user("modowner", "mo@test.com", hash_password("secret"))
    friend = database.create_user("modfriend", "mf@test.com", hash_password("secret"))
    fid = database.send_friend_request(owner, friend)
    database.accept_friend_request(fid)
    pid = database.create_post(friend, "text", text_content="Topic", visibility="friends")
    for text in ("You are wrong!!", "That is stupid!!", "I see your point"):
        database.add_comment(friend, pid, text)
    assert agent_companion.detect_conflict_thread(pid, owner) is True


def test_detect_conflict_thread_returns_false_when_calm(test_db):
    owner = database.create_user("calmowner", "co@test.com", hash_password("secret"))
    friend = database.create_user("calmfriend", "cf@test.com", hash_password("secret"))
    fid = database.send_friend_request(owner, friend)
    database.accept_friend_request(fid)
    pid = database.create_post(friend, "text", text_content="Topic", visibility="friends")
    database.add_comment(friend, pid, "Nice share")
    assert agent_companion.detect_conflict_thread(pid, owner) is False


def test_suggest_de_escalation_by_personality(test_db):
    p = agent_companion.suggest_de_escalation({}, "pulsatilla")
    n = agent_companion.suggest_de_escalation({}, "nux_vomica")
    assert p != n
    assert "soften" in p or "heavy" in p


def test_tone_check_route(client, test_db):
    owner = database.create_user("toneowner", "to@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "tone_bot", "Tone", "nux_vomica")
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.post(f"/agents/{aid}/tone-check", data={"text": "SHUT UP"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["flagged"] is True
