import database


def test_birthday_fields_exist(test_db):
    u = test_db.create_user("bday", "bd@test.com", "hash")
    conn = test_db.get_connection()
    conn.execute("UPDATE users SET birthday_month=7, birthday_day=15 WHERE id=?", (u,))
    conn.commit()
    user = database.get_user(u)
    conn.close()
    assert user["birthday_month"] == 7
    assert user["birthday_day"] == 15
