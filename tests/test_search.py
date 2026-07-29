import database


def test_user_search_by_username(test_db):
    u = test_db.create_user("searchable", "s@test.com", "hash")
    conn = test_db.get_connection()
    rows = conn.execute("SELECT * FROM users WHERE username LIKE ?", ("%search%",)).fetchall()
    conn.close()
    assert len(rows) >= 1
