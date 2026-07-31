import pytest
"""
Tests for agent comment drafting, approval, and permission checks.
"""
import database
import agent_companion
from auth import hash_password


def _owner_and_agent(test_db):
    owner = database.create_user("owner2", "o2@test.com", hash_password("secret"))
    friend = database.create_user("friend2", "f2@test.com", hash_password("secret"))
    fid = database.send_friend_request(owner, friend)
    database.accept_friend_request(fid)
    aid = agent_companion.create_agent_account(owner, "comment_bot", "Comment", "pulsatilla")
    return owner, friend, aid


def test_draft_comment_creates_draft(test_db):
    owner, friend, aid = _owner_and_agent(test_db)
    pid = database.create_post(friend, "text", text_content="Hello world", visibility="friends")
    draft_id = agent_companion.draft_comment(aid, pid, "Lovely post!")
    draft = database.get_agent_draft(draft_id)
    assert draft["draft_type"] == "comment"
    assert draft["content"] == "Lovely post!"
    assert draft["is_approved"] == 0


def test_approve_comment_posts_under_agent_identity(test_db):
    owner, friend, aid = _owner_and_agent(test_db)
    pid = database.create_post(friend, "text", text_content="Hello world", visibility="friends")
    draft_id = agent_companion.draft_comment(aid, pid, "Nice one")
    cid = agent_companion.approve_and_post_comment(draft_id, owner)
    comment = database.get_comments(pid)[0]
    assert comment["user_id"] == aid
    assert comment["text"] == "Nice one"


def test_cannot_approve_others_draft(test_db):
    owner, friend, aid = _owner_and_agent(test_db)
    other = database.create_user("other", "o@test.com", hash_password("secret"))
    pid = database.create_post(friend, "text", text_content="Hello", visibility="friends")
    draft_id = agent_companion.draft_comment(aid, pid, "Nice")
    with pytest.raises(ValueError):
        agent_companion.approve_and_post_comment(draft_id, other)


def test_can_agent_feature_blocks_inactive_agent(test_db):
    owner, friend, aid = _owner_and_agent(test_db)
    assert agent_companion.can_agent_feature(aid, "comment") is True
    agent_companion.pause_agent(aid, owner)
    assert agent_companion.can_agent_feature(aid, "comment") is False


def test_suggest_comment_varies_by_personality(test_db):
    owner, friend, aid = _owner_and_agent(test_db)
    post = {"id": 1, "text_content": "Test post"}
    p_comment = agent_companion.suggest_comment_for_post(post, database.get_user(owner), "phosphorus")
    n_comment = agent_companion.suggest_comment_for_post(post, database.get_user(owner), "nux_vomica")
    assert p_comment != n_comment


def test_route_draft_comment(client, test_db):
    # Login as owner2 via direct session
    owner, friend, aid = _owner_and_agent(test_db)
    pid = database.create_post(friend, "text", text_content="Route post", visibility="friends")
    with client.session_transaction() as sess:
        sess["user_id"] = owner
        sess["role"] = "user"
    resp = client.post(f"/agents/{aid}/draft-comment/{pid}", follow_redirects=True)
    assert resp.status_code == 200
