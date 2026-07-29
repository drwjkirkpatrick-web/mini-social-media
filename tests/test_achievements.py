import database


def test_achievements_seeded(test_db):
    achs = database.get_achievements()
    assert len(achs) >= 13
    slugs = {a["slug"] for a in achs}
    assert "first_steps" in slugs
    assert "digital_detox" in slugs


def test_first_steps_achievement(test_db):
    u = test_db.create_user("achiever", "a@test.com", "hash")
    # Before posting
    user_ach = database.get_user_achievements(u)
    assert len(user_ach) == 0
    # Create a post
    test_db.create_post(u, "text", text_content="My first post")
    awarded = database.check_and_award_achievements(u)
    assert "first_steps" in awarded
    user_ach2 = database.get_user_achievements(u)
    assert len(user_ach2) >= 1


def test_verified_human_achievement(test_db):
    u = test_db.create_user("verifier", "v@test.com", "hash")
    conn = test_db.get_connection()
    conn.execute("UPDATE users SET has_onboarded=1, bio='Hello', avatar_url='/x.jpg', birthday_month=7 WHERE id=?", (u,))
    conn.commit()
    conn.close()
    awarded = database.check_and_award_achievements(u)
    assert "verified_human" in awarded
