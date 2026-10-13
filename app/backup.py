"""Back up and restore the MeshWX SQLite database while the app is stopped.

Usage:
    python -m app.backup backup --database /path/to/meshwx.db --output /path/to/backup.db
    python -m app.backup restore --database /path/to/meshwx.db --source /path/to/backup.db

Restore is intentionally offline-only: stop the MeshWX service first.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def backup(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() == destination.resolve():
        raise ValueError("backup destination must differ from source")
    with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("backup", "restore"))
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.action == "backup":
        if args.output is None:
            parser.error("--output required")
        backup(args.database, args.output)
    else:
        if args.source is None:
            parser.error("--source required")
        if not args.database.exists():
            parser.error("database must exist; stop the service before restoring")
        backup(args.source, args.database)


if __name__ == "__main__":
    main()
