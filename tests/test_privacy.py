import database
from feed import get_feed


def test_friends_only_visible_to_friend(test_db):
    me = test_db.create_user("privme", "pm@test.com", "hash")
    friend = test_db.create_user("privfriend", "pf@test.com", "hash")
    fid = test_db.send_friend_request(me, friend)
    test_db.accept_friend_request(fid)
    post = test_db.create_post(friend, "text", text_content="Friend secret", visibility="friends")
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id=?", (post,))
    conn.commit()
    conn.close()
    feed = get_feed(me, limit=10)
    assert any(p["text_content"] == "Friend secret" for p in feed)


def test_only_me_visible_only_to_author(test_db):
    me = test_db.create_user("privme2", "pm2@test.com", "hash")
    friend = test_db.create_user("privfriend2", "pf2@test.com", "hash")
    fid = test_db.send_friend_request(me, friend)
    test_db.accept_friend_request(fid)
    post = test_db.create_post(me, "text", text_content="My secret", visibility="only_me")
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id=?", (post,))
    conn.commit()
    conn.close()
    feed = get_feed(friend, limit=10)
    assert not any(p["text_content"] == "My secret" for p in feed)
