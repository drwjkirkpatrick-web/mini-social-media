import database


def test_unicorn_reaction(test_db):
    u1 = test_db.create_user("r1", "r1@test.com", "hash")
    u2 = test_db.create_user("r2", "r2@test.com", "hash")
    p = test_db.create_post(u1, "text", text_content="Magic")
    database.add_reaction(p, u1, "unicorn")
    database.add_reaction(p, u2, "sparkles")
    r = database.get_reactions(p)
    assert r.get("unicorn") == 1
    assert r.get("sparkles") == 1


def test_heart_suit_reaction(test_db):
    u1 = test_db.create_user("r3a", "r3a@test.com", "hash")
    u2 = test_db.create_user("r3b", "r3b@test.com", "hash")
    p = test_db.create_post(u1, "text", text_content="Love")
    database.add_reaction(p, u1, "heart_suit")
    database.add_reaction(p, u2, "two_hearts")
    r = database.get_reactions(p)
    assert r.get("heart_suit") == 1
    assert r.get("two_hearts") == 1
