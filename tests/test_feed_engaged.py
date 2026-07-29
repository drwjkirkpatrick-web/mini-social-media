import database
from feed import get_feed


def test_engaged_sort_ranks_by_interaction(test_db):
    me = test_db.create_user("eng", "eng@test.com", "hash")
    friend = test_db.create_user("engf", "engf@test.com", "hash")
    fid = test_db.send_friend_request(me, friend)
    test_db.accept_friend_request(fid)
    # Create low-engagement post
    p1 = test_db.create_post(friend, "text", text_content="Low", visibility="friends")
    # Create high-engagement post
    p2 = test_db.create_post(friend, "text", text_content="High", visibility="friends")
    # Add reactions to p2
    database.add_reaction(p2, me, "heart")
    database.add_reaction(p2, me, "fire")
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id IN (?, ?)", (p1, p2))
    conn.commit()
    conn.close()
    feed = get_feed(me, sort="engaged", limit=10)
    assert len(feed) == 2
    # High engagement should rank higher
    assert feed[0]["text_content"] == "High"
