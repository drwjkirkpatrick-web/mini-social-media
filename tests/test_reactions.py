import database


def test_add_reaction(test_db):
    u = test_db.create_user("reactor", "r@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="React to me")
    database.add_reaction(p, u, "heart")
    r = database.get_reactions(p)
    assert r.get("heart") == 1


def test_toggle_reaction(test_db):
    u = test_db.create_user("reactor2", "r2@test.com", "hash")
    p = test_db.create_post(u, "text", text_content="React")
    database.add_reaction(p, u, "heart")
    database.add_reaction(p, u, "heart")
    r = database.get_reactions(p)
    assert r.get("heart", 0) == 0
