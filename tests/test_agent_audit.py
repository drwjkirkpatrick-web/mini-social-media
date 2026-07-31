"""
Tests for agent audit log, consent toggle, and transparency.
"""
import database
import agent_companion
from auth import hash_password


def _owner_and_agent(test_db):
    owner = database.create_user("auditowner", "ao@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "audit_bot", "Audit", "calcarea_carbonica")
    return owner, aid


def test_create_agent_logs_action(test_db):
    owner, aid = _owner_and_agent(test_db)
    log = database.list_agent_audit_log(owner, aid)
    assert any(entry["action"] == "created" for entry in log)


def test_pause_and_resume_log_actions(test_db):
    owner, aid = _owner_and_agent(test_db)
    agent_companion.pause_agent(aid, owner)
    agent_companion.resume_agent(aid, owner)
    log = database.list_agent_audit_log(owner, aid)
    assert any(entry["action"] == "paused" for entry in log)
    assert any(entry["action"] == "resumed" for entry in log)


def test_is_agent_active_after_pause(test_db):
    owner, aid = _owner_and_agent(test_db)
    assert agent_companion.is_agent_active(aid) is True
    agent_companion.pause_agent(aid, owner)
    assert agent_companion.is_agent_active(aid) is False


def test_agent_permission_override(test_db):
    owner, aid = _owner_and_agent(test_db)
    database.set_agent_permission(aid, owner, "comment", False)
    assert agent_companion.can_agent_feature(aid, "comment") is False


def test_agent_to_agent_consent_requires_mutual(test_db):
    owner = database.create_user("consentowner", "co@test.com", hash_password("secret"))
    a1 = agent_companion.create_agent_account(owner, "c1", "C1", "phosphorus")
    a2 = agent_companion.create_agent_account(owner, "c2", "C2", "pulsatilla")
    assert agent_companion.agent_to_agent_consent(a1, a2) is False
    database.set_agent_agent_consent(a1, a2, True)
    assert agent_companion.agent_to_agent_consent(a1, a2) is True
