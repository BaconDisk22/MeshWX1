"""Run smoke checks for MeshWX without transmitting any radio messages.

Usage: python -m app.smokecheck
"""
from __future__ import annotations

import importlib
import sys


def main() -> int:
    modules = [
        "app.main", "app.transmit", "app.network_discovery",
        "app.bluetooth_discovery", "app.backup", "app.scheduled_backup",
        "app.poller", "app.ipaws",
    ]
    failures = []
    for module in modules:
        try:
            importlib.import_module(module)
            print("OK", module)
        except Exception as exc:
            failures.append((module, str(exc)))
            print("FAIL", module, exc)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
