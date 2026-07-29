import database


def test_create_and_update_note(test_db):
    u = test_db.create_user("noter", "n@test.com", "hash")
    nid = database.create_note(u, "Ideas", "First draft")
    assert nid > 0
    database.update_note(nid, "Updated content", u)
    note = database.get_note(nid)
    assert note["content"] == "Updated content"
    assert note["version"] == 2
