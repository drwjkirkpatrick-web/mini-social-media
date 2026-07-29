import database


def test_row_factory(test_db):
    conn = test_db.get_connection()
    assert conn.row_factory is not None
    conn.close()


def test_foreign_keys_enabled(test_db):
    conn = test_db.get_connection()
    row = conn.execute("PRAGMA foreign_keys").fetchone()
    assert row[0] == 1
    conn.close()
