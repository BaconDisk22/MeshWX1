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
