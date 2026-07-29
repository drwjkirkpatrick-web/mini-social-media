import database
import blockchain


def test_create_post_adds_audit_block(test_db):
    uid = test_db.create_user("bcuser", "bc@test.com", "hash")
    conn = test_db.get_connection()
    pid = test_db.create_post(uid, "text", text_content="blockchain test")
    blockchain.add_block_within_conn(conn, "posts", pid, "create", uid, "test")
    conn.commit()
    # Count audit entries
    row = conn.execute("SELECT COUNT(*) as c FROM audit_log").fetchone()
    assert row["c"] >= 1
    conn.close()


def test_verify_chain_clean(test_db):
    result = blockchain.verify_chain()
    assert result["clean"] is True
    assert result["issues"] == []
