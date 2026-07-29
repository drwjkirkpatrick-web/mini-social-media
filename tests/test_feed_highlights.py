from feed import get_feed
import database


def test_chronological_with_highlights_sort(test_db):
    me = test_db.create_user("hl", "hl@test.com", "hash")
    friend = test_db.create_user("hlf", "hlf@test.com", "hash")
    fid = test_db.send_friend_request(me, friend)
    test_db.accept_friend_request(fid)
    p1 = test_db.create_post(friend, "text", text_content="Low engagement", visibility="friends")
    p2 = test_db.create_post(friend, "text", text_content="High engagement", visibility="friends")
    database.add_reaction(p2, me, "heart")
    database.add_reaction(p2, me, "fire")
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved' WHERE id IN (?, ?)", (p1, p2))
    conn.commit()
    conn.close()
    feed = get_feed(me, sort="chronological_with_highlights", limit=10)
    assert len(feed) == 2
