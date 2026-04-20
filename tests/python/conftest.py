"""Pytest conftest that puts `scripts/` on sys.path so tests can import the
pipeline modules directly as ``constants``, ``transforms``, ``io_helpers``.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_HERE))
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "scripts")

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
