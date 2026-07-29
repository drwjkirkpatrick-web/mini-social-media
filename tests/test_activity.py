import database


def test_record_and_get_activity(test_db):
    u = test_db.create_user("active", "ac@test.com", "hash")
    database.record_user_activity(u, "2026-07-28")
    database.record_user_activity(u, "2026-07-28")
    database.record_user_activity(u, "2026-07-29")
    activity = database.get_user_activity(u)
    assert len(activity) == 2
    dates = {a["activity_date"] for a in activity}
    assert "2026-07-28" in dates
    assert "2026-07-29" in dates
