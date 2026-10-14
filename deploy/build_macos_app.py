"""Create a simple unsigned macOS MeshWX.app bundle.

Run on macOS after creating .venv:
    python3 deploy/build_macos_app.py

The launcher runs the repository's .venv and needs the repository to stay in
place. It is NOT notarized or distributable as a standalone binary.
"""
from __future__ import annotations

import plistlib
import shlex
import stat
from pathlib import Path


def build(root: Path) -> Path:
    bundle = root / "dist" / "MeshWX.app"
    macos = bundle / "Contents" / "MacOS"
    macos.mkdir(parents=True, exist_ok=True)
    plist = {
        "CFBundleName": "MeshWX",
        "CFBundleDisplayName": "MeshWX",
        "CFBundleIdentifier": "org.meshwx.local",
        "CFBundleExecutable": "MeshWX",
        "CFBundlePackageType": "APPL",
        "CFBundleVersion": "1",
    }
    with (bundle / "Contents" / "Info.plist").open("wb") as file:
        plistlib.dump(plist, file)
    executable = macos / "MeshWX"
    script = f"""#!/bin/bash
set -e
cd {shlex.quote(str(root))}
if [ ! -x .venv/bin/python ]; then
  osascript -e 'display alert "MeshWX virtual environment not found"'
  exit 1
fi
open "http://127.0.0.1:8000/operator" >/dev/null 2>&1 &
exec .venv/bin/python -m app.main
"""
    executable.write_text(script)
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bundle


if __name__ == "__main__":
    print(build(Path(__file__).resolve().parent.parent))
