#!/usr/bin/env python3
"""The offline suite without a POSIX shell: every chapter's harness and exercises.

Same order and same totals as `run_offline.sh`, one chapter at a time, using this
interpreter for every child so it works from PowerShell on Windows.

Usage:
    python run_offline.py            # every chapter
    python run_offline.py chapter20  # one chapter
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHAPTERS = ROOT / "chapters"
PY = sys.executable


def run(command: list[str], cwd: Path, env: dict[str, str]) -> int:
    return subprocess.run(command, cwd=cwd, env=env).returncode


def chapter_gate(chapter_id: str) -> int:
    directory = CHAPTERS / chapter_id / "files"
    number = int(chapter_id.removeprefix("chapter"))
    failures = 0
    print(f"== {chapter_id}")

    base = dict(os.environ)
    harness = directory / f"run_ex{number}.py"
    if harness.exists():
        failures += run([PY, harness.name], directory, {**base, "PYTHONPATH": "."}) != 0

    exercises = directory / "exercises" / "run_exercises.py"
    if exercises.exists():
        failures += run([PY, "run_exercises.py"], exercises.parent, {**base, "PYTHONPATH": f"..{os.pathsep}."}) != 0

    return failures


def main() -> int:
    specs = sorted(CHAPTERS.glob("chapter*/spec.yaml"))
    if not specs:
        raise SystemExit(f"no chapter contracts under {CHAPTERS}")

    chosen = sys.argv[1:]
    chapters = chosen or [spec.parent.name for spec in specs]

    failures = 0
    for chapter_id in chapters:
        if not (CHAPTERS / chapter_id / "spec.yaml").exists():
            raise SystemExit(f"no spec for {chapter_id}")
        failures += chapter_gate(chapter_id)

    if failures:
        print(f"\n{failures} gate(s) failed")
        return 1
    print("\nall chapters green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
