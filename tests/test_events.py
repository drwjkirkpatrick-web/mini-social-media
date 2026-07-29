import database


def test_create_event(test_db):
    u = test_db.create_user("eventer", "e@test.com", "hash")
    eid = test_db.create_event(u, "Party", "A fun party", "Park", "2026-08-01T18:00", "2026-08-01T22:00")
    assert eid > 0
    ev = test_db.get_event(eid)
    assert ev["title"] == "Party"


def test_rsvp_event(test_db):
    u = test_db.create_user("eventer2", "e2@test.com", "hash")
    eid = test_db.create_event(u, "Meetup", "Hi", "Cafe", None, None)
    test_db.rsvp_event(eid, u, "going")
    rsvps = test_db.get_event_rsvps(eid)
    assert len(rsvps) == 1
    assert rsvps[0]["status"] == "going"
