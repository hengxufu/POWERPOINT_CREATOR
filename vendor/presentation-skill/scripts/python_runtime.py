#!/usr/bin/env python3
"""Run a repository Python command with the pinned project runtime when present."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def project_python() -> Path:
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/python_runtime.py <script-or--m> [args...]", file=sys.stderr)
        return 2
    runtime = project_python()
    executable = str(runtime) if runtime.is_file() else sys.executable
    os.execv(executable, [executable, *sys.argv[1:]])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
