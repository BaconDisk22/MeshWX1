#!/bin/bash
# Double-clickable macOS launcher (after installation and permissions setup).
set -e
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo "Missing .venv. Create a Python 3.11+ environment and install requirements first."
  read -r -p "Press Enter to close..."
  exit 1
fi
echo "Starting MeshWX. Keep this window open while the server is running."
exec .venv/bin/python -m app.main
