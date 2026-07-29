from feed import get_feed
import database


def test_photos_sort(test_db):
    me = test_db.create_user("ps", "ps@test.com", "hash")
    friend = test_db.create_user("psf", "psf@test.com", "hash")
    fid = test_db.send_friend_request(me, friend)
    test_db.accept_friend_request(fid)
    conn = test_db.get_connection()
    cursor = conn.cursor()
    # Text post (approved)
    cursor.execute(
        "INSERT INTO posts (user_id, content_type, text_content, visibility, moderation_status) VALUES (?, 'text', 'Just text', 'friends', 'approved')",
        (friend,),
    )
    # Photo post (approved)
    cursor.execute(
        "INSERT INTO posts (user_id, content_type, text_content, photo_url, visibility, moderation_status) VALUES (?, 'photo', 'A photo', '/static/uploads/test.jpg', 'friends', 'approved')",
        (friend,),
    )
    conn.commit()
    conn.close()
    feed = get_feed(me, sort="photos", limit=10)
    assert len(feed) == 2
    # Photo post should be first
    assert feed[0].get("photo_url") or feed[0].get("photo_urls")
