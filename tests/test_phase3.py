"""Phase 3 regression tests: SQLite backup and manager state."""
import sqlite3

from app.backup import backup


def test_sqlite_backup_round_trip(tmp_path):
    source = tmp_path / "source.db"
    target = tmp_path / "backup.db"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE sample (value TEXT)")
        db.execute("INSERT INTO sample VALUES ('saved')")
    backup(source, target)
    with sqlite3.connect(target) as db:
        assert db.execute("SELECT value FROM sample").fetchone()[0] == "saved"


def test_backup_rotation(tmp_path):
    from app.scheduled_backup import backup_once
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE sample (value INTEGER)")
    destination = tmp_path / "backups"
    for _ in range(3):
        backup_once(source, destination, keep=2)
    assert len(list(destination.glob("meshwx-*.db"))) == 2


def test_backup_is_valid_sqlite(tmp_path):
    from app.scheduled_backup import backup_once
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as conn:
        conn.execute("CREATE TABLE alert (id INTEGER PRIMARY KEY, body TEXT)")
        conn.execute("INSERT INTO alert(body) VALUES ('warning')")
    output = backup_once(source, tmp_path / "backups")
    with sqlite3.connect(output) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT body FROM alert").fetchone()[0] == "warning"


def test_backup_failure_does_not_leave_partial_file(tmp_path):
    from app.scheduled_backup import backup_once
    import pytest
    destination = tmp_path / "backups"
    with pytest.raises(Exception):
        backup_once(tmp_path / "missing.db", destination)
    assert not list(destination.glob("meshwx-*.db"))
