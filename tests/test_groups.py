import database


def test_create_group_and_add_members(test_db):
    a = test_db.create_user("group_a", "ga@test.com", "hash")
    b = test_db.create_user("group_b", "gb@test.com", "hash")
    gid = database.create_message_group("Test Group", a)
    database.add_to_group(gid, b)
    msgs = database.get_group_messages(gid)
    assert len(msgs) == 0
    database.send_group_message(a, gid, "Hello group!")
    msgs = database.get_group_messages(gid)
    assert len(msgs) == 1
