"""
Tests for agent post drafting and approval.
"""
import json
import database
import agent_companion
from auth import hash_password


def _owner_and_agent(test_db, persona="phosphorus"):
    owner = database.create_user("postowner", "po@test.com", hash_password("secret"))
    aid = agent_companion.create_agent_account(owner, "post_bot", "Post", persona)
    return owner, aid


def test_suggest_post_draft_by_personality(test_db):
    owner, aid = _owner_and_agent(test_db, "sulphur")
    draft = agent_companion.suggest_post_draft(database.get_user(owner), "sulphur", ["space"])
    assert draft["content_type"] == "text"
    assert "space" in draft["text"]


def test_create_and_approve_post_draft(test_db):
    owner, aid = _owner_and_agent(test_db, "phosphorus")
    draft = agent_companion.suggest_post_draft(database.get_user(owner), "phosphorus", ["joy"])
    content = json.dumps(draft)
    draft_id = database.create_agent_draft(aid, owner, "post", 0, content, context={"topics": ["joy"]})
    post_id = agent_companion.approve_and_post(aid, draft_id, owner)
    post = database.get_post(post_id)
    assert post["user_id"] == aid
    assert "joy" in post["text_content"]


def test_cannot_post_without_permission(test_db):
    owner, aid = _owner_and_agent(test_db, "bryonia")
    database.update_agent_profile(aid, owner, can_post=0)
    assert agent_companion.can_agent_feature(aid, "post") is False


def test_draft_post_route(client, test_db):
    owner, aid = _owner_and_agent(test_db, "phosphorus")
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.post(f"/agents/{aid}/draft-post", follow_redirects=True)
    assert resp.status_code == 200
