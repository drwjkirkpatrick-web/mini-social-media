import database


def test_send_message(test_db):
    a = test_db.create_user("msg_a", "ma@test.com", "hash")
    b = test_db.create_user("msg_b", "mb@test.com", "hash")
    mid = database.send_message(a, b, "Hello!")
    assert mid > 0
    msgs = database.get_messages_between(a, b)
    assert len(msgs) == 1
    assert msgs[0]["content"] == "Hello!"


def test_conversation_list(test_db):
    a = test_db.create_user("msg_a2", "ma2@test.com", "hash")
    b = test_db.create_user("msg_b2", "mb2@test.com", "hash")
    database.send_message(a, b, "Hey")
    convs = database.get_conversation_list(b)
    assert len(convs) == 1
