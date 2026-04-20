#!/usr/bin/env bash
# Install the committed pre-commit hook into .git/hooks/.
#
# Run once per clone:
#     bash hooks/install-hooks.sh
#
# Uses a symlink so future edits to hooks/pre-commit take effect immediately
# without re-running this script. Falls back to a copy on platforms where
# symlinks are unavailable (some Windows environments without Developer Mode).

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SRC="$REPO_ROOT/hooks/pre-commit"
DST="$REPO_ROOT/.git/hooks/pre-commit"

if [ ! -f "$SRC" ]; then
  echo "error: $SRC does not exist" >&2
  exit 1
fi

chmod +x "$SRC" 2>/dev/null || true

# Try symlink first, fall back to copy.
if ln -sf "$SRC" "$DST" 2>/dev/null; then
  echo "Installed pre-commit hook (symlink) -> $DST"
else
  cp "$SRC" "$DST"
  chmod +x "$DST"
  echo "Installed pre-commit hook (copy)    -> $DST"
  echo "Note: re-run this script after editing hooks/pre-commit."
fi
