import database


def test_party_reaction(test_db):
    u = test_db.create_user("reactor3", "r3@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="Party time")
    database.add_reaction(p, u, "party")
    r = database.get_reactions(p)
    assert r.get("party") == 1


def test_peach_reaction(test_db):
    u1 = test_db.create_user("reactor4a", "r4a@test.com", "hash")
    u2 = test_db.create_user("reactor4b", "r4b@test.com", "hash")
    u3 = test_db.create_user("reactor4c", "r4c@test.com", "hash")
    p = test_db.create_post(u1, "text", text_content="Peachy")
    database.add_reaction(p, u1, "peach")
    database.add_reaction(p, u2, "pray")
    database.add_reaction(p, u3, "tada")
    r = database.get_reactions(p)
    assert r.get("peach") == 1
    assert r.get("pray") == 1
    assert r.get("tada") == 1
