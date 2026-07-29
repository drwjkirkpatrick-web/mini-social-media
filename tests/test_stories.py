import database


def test_create_and_get_stories(test_db):
    u = test_db.create_user("storyteller", "s@test.com", "hash")
    sid = database.create_story(u, "text", text_content="Hello story")
    assert sid > 0
    # Add friendship so stories appear
    f = test_db.create_user("viewer", "v@test.com", "hash")
    fid = test_db.send_friend_request(u, f)
    test_db.accept_friend_request(fid)
    stories = database.get_active_stories(f)
    assert len(stories) >= 1


def test_story_view_tracking(test_db):
    u = test_db.create_user("story2", "s2@test.com", "hash")
    sid = database.create_story(u, "text", text_content="View me")
    v = test_db.create_user("viewer2", "v2@test.com", "hash")
    database.view_story(sid, v)
    conn = test_db.get_connection()
    row = conn.execute("SELECT view_count FROM stories WHERE id=?", (sid,)).fetchone()
    conn.close()
    assert row["view_count"] == 1
