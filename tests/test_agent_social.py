"""
Tests for agent social suggestions: check-ins, gratitude, birthdays, icebreakers.
"""
import database
import agent_companion
from auth import hash_password


def _owner_with_friends(test_db):
    owner = database.create_user("socialowner", "so@test.com", hash_password("secret"))
    f1 = database.create_user("socialf1", "sf1@test.com", hash_password("secret"))
    f2 = database.create_user("socialf2", "sf2@test.com", hash_password("secret"))
    for f in (f1, f2):
        fid = database.send_friend_request(owner, f)
        database.accept_friend_request(fid)
    return owner, f1, f2


def test_suggest_checkin_target_returns_friend(test_db):
    owner, f1, f2 = _owner_with_friends(test_db)
    target = agent_companion.suggest_checkin_target(owner)
    assert target is not None
    assert target["id"] in (f1, f2)


def test_suggest_gratitude_by_personality(test_db):
    owner, f1, f2 = _owner_with_friends(test_db)
    friend = database.get_user(f1)
    p = agent_companion.suggest_gratitude_message(database.get_user(owner), friend, "phosphorus")
    n = agent_companion.suggest_gratitude_message(database.get_user(owner), friend, "nux_vomica")
    assert "spark" in p or "brightens" in p
    assert "respect" in n or "Thanks" in n


def test_suggest_icebreaker_by_personality(test_db):
    owner, f1, f2 = _owner_with_friends(test_db)
    friend = database.get_user(f1)
    p = agent_companion.suggest_icebreaker(database.get_user(owner), friend, "pulsatilla")
    assert "glad" in p or "connected" in p


def test_suggest_event_plan(test_db):
    owner, f1, f2 = _owner_with_friends(test_db)
    friends = database.list_friends(owner)
    plan = agent_companion.suggest_event_plan(database.get_user(owner), friends, "phosphorus")
    assert "title" in plan
    assert "start_time" in plan
    assert f1 in plan["invitee_ids"] or f2 in plan["invitee_ids"]


def test_suggest_poll(test_db):
    owner, f1, f2 = _owner_with_friends(test_db)
    poll = agent_companion.suggest_poll(database.get_user(owner), 2, "sulphur")
    assert "question" in poll
    assert len(poll["options"]) >= 2
