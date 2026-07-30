import database
from feed import get_feed


def _approve_all_posts(test_db):
    """Approve all posts so they become feed-visible."""
    conn = test_db.get_connection()
    conn.execute("UPDATE posts SET moderation_status='approved'")
    conn.commit()
    conn.close()


def test_feed_query_count_ceiling(test_db, monkeypatch):
    """Benchmark: 50 posts must be served with ≤ 3 DB execute() calls."""
    me = test_db.create_user("bench", "bench@test.com", "hash")
    friend = test_db.create_user("benchf", "benchf@test.com", "hash")
    fid = test_db.send_friend_request(me, friend)
    test_db.accept_friend_request(fid)

    for i in range(50):
        test_db.create_post(friend, "text", text_content=f"Post {i}", visibility="friends")
    _approve_all_posts(test_db)

    # Sprinkle engagement so subqueries actually run against real data.
    conn = test_db.get_connection()
    rows = conn.execute("SELECT id FROM posts WHERE user_id=? ORDER BY id LIMIT 50", (friend,)).fetchall()
    pids = [r["id"] for r in rows]
    for pid in pids[:10]:
        conn.execute("INSERT INTO post_likes (post_id, user_id) VALUES (?, ?)", (pid, me))
        conn.execute("INSERT INTO post_comments (post_id, user_id, text) VALUES (?, ?, ?)", (pid, me, "nice"))
        conn.execute("INSERT INTO reactions (post_id, user_id, reaction_type) VALUES (?, ?, ?)", (pid, me, "heart"))
    conn.commit()
    conn.close()

    execute_calls = []
    original_get_connection = database.get_connection

    class CountingConnection:
        """Proxy that counts execute() calls on a real sqlite3 connection."""
        def __init__(self, real_conn):
            self._real = real_conn

        def execute(self, sql, parameters=None):
            execute_calls.append(sql.strip())
            return self._real.execute(sql, parameters)

        def cursor(self):
            cur = self._real.cursor()
            original_cur_execute = cur.execute

            def cur_execute(sql, parameters=None):
                execute_calls.append(sql.strip())
                return original_cur_execute(sql, parameters)

            cur.execute = cur_execute
            return cur

        def commit(self):
            return self._real.commit()

        def close(self):
            return self._real.close()

        def __getattr__(self, name):
            return getattr(self._real, name)

    def counting_get_connection():
        real = original_get_connection()
        return CountingConnection(real)

    monkeypatch.setattr(database, "get_connection", counting_get_connection)

    posts = get_feed(me, limit=50)
    assert len(posts) == 50
    assert len([c for c in execute_calls if c.lower().startswith("select")]) <= 2
    assert len(execute_calls) <= 3


def test_feed_counts_are_accurate(test_db):
    """Inline counts must match dedicated count functions."""
    me = test_db.create_user("counts", "counts@test.com", "hash")
    friend = test_db.create_user("countsf", "countsf@test.com", "hash")
    fid = test_db.send_friend_request(me, friend)
    test_db.accept_friend_request(fid)
    pid = test_db.create_post(friend, "text", text_content="Counted", visibility="friends")
    _approve_all_posts(test_db)

    database.like_post(me, pid)
    database.add_comment(me, pid, "one")
    database.add_comment(me, pid, "two")
    database.add_reaction(pid, me, "fire")

    posts = get_feed(me, limit=10)
    assert len(posts) == 1
    post = posts[0]
    assert post["like_count"] == 1
    assert post["comment_count"] == 2
    assert post["reactions"] == {"fire": 1}
    assert post["engagement_score"] == 1 * 2 + 2 * 3 + 1
