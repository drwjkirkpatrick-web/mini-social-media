import database


def test_log_and_list_backups(test_db):
    u = test_db.create_user("admin", "adm@test.com", "hash")
    bid = database.log_backup("backup_20260728.tar.gz", 1024000, u)
    assert bid > 0
    backups = database.list_backups()
    assert len(backups) == 1
    assert backups[0]["filename"] == "backup_20260728.tar.gz"
