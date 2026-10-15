"""
server/

FastAPI backend for the PhishForge Console. Wraps the existing PhishForge
pipeline (core/, models/, config/) without modifying it. Ensures the repo
root is importable as top-level packages (core, models, config), mirroring
the sys.path convention already used by cli.py and evaluation/*.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
