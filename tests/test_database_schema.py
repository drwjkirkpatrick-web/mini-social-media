import database


def test_all_tables_exist(test_db):
    conn = test_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {r["name"] for r in cursor.fetchall()}
    conn.close()
    required = {"users", "posts", "friendships", "post_likes", "post_comments",
                "blocks", "pages", "audit_log", "notifications"}
    assert required.issubset(names)
