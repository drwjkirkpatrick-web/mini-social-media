import database


def test_add_and_get_reading_list(test_db):
    u = test_db.create_user("reader", "rd@test.com", "hash")
    rid = database.add_to_reading_list(u, "https://example.com", "Great Article", "Very insightful")
    items = database.get_reading_list(u)
    assert len(items) == 1
    assert items[0]["title"] == "Great Article"
