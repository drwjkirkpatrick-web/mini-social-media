import database
from feed import get_feed


def test_feed_shows_own_posts(test_db):
    me = test_db.create_user("me", "me@test.com", "hash")
    pid = test_db.create_post(me, "text", text_content="My post")
    # Posts start as pending moderation; approve for feed visibility
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    posts = get_feed(me, limit=10)
    assert len(posts) == 1
    assert posts[0]["text_content"] == "My post"


def test_feed_shows_friend_posts(test_db):
    me = test_db.create_user("me2", "me2@test.com", "hash")
    friend = test_db.create_user("friend", "friend@test.com", "hash")
    fid = test_db.send_friend_request(me, friend)
    test_db.accept_friend_request(fid)
    test_db.create_post(friend, "text", text_content="Friend post", visibility="friends")
    # Need to approve post for feed
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE user_id=?", (friend,))
    conn.commit()
    conn.close()
    posts = get_feed(me, limit=10)
    assert any(p["text_content"] == "Friend post" for p in posts)


def test_feed_hides_non_friend_posts(test_db):
    me = test_db.create_user("me3", "me3@test.com", "hash")
    stranger = test_db.create_user("stranger", "str@test.com", "hash")
    test_db.create_post(stranger, "text", text_content="Secret", visibility="friends")
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE user_id=?", (stranger,))
    conn.commit()
    conn.close()
    posts = get_feed(me, limit=10)
    assert not any(p["text_content"] == "Secret" for p in posts)
