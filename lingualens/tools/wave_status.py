#!/usr/bin/env python3
"""Where every course stands, across the worktrees the course agents use.

    .venv/bin/python tools/wave_status.py A1          # gate + content to A1, every course
    .venv/bin/python tools/wave_status.py B1 fr de    # just these

Finds each course in the git worktrees (the branch that last changed
server/course/<code>/ wins over main), runs the gate with
--fluency <BAND> there, and prints one line per course. The orchestrator of
the expansion waves (docs/EXPAND_COURSE.md) runs this at every checkpoint.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "bin" / "python"


def worktrees() -> list:
    out = subprocess.run(["git", "-C", str(ROOT), "worktree", "list", "--porcelain"],
                         capture_output=True, text=True).stdout
    paths, branch = [], {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line.split(" ", 1)[1]))
        elif line.startswith("branch ") and paths:
            branch[paths[-1]] = line.split("refs/heads/", 1)[-1]
    return [(p, branch.get(p, "")) for p in paths]


def where(code: str) -> tuple:
    """(lingualens dir, branch) of the checkout working on a course: the
    worktree whose branch changed server/course/<code>/ most recently,
    else the main checkout."""
    best = None
    main_dir = None
    for path, branch in worktrees():
        d = path / "lingualens"
        if main_dir is None:
            main_dir = (d, branch)
        if not branch or not (d / "server" / "course" / code / "meta.py").exists():
            continue
        r = subprocess.run(["git", "-C", str(path), "log", "-1", "--format=%ct", "main..HEAD",
                            "--", f"lingualens/server/course/{code}"],
                           capture_output=True, text=True).stdout.strip()
        if r and (best is None or int(r) > best[0]):
            best = (int(r), d, branch)
    if best:
        return best[1], best[2]
    if main_dir and (main_dir[0] / "server" / "course" / code / "meta.py").exists():
        return main_dir
    return None, ""


def main() -> int:
    band = (sys.argv[1] if len(sys.argv) > 1 else "A1").upper()
    codes = sys.argv[2:] or ["es", "fr", "de", "it", "pt", "ko", "ru", "ar", "hi", "zh", "ja"]
    failed = 0
    for code in codes:
        d, branch = where(code)
        if not d:
            print(f"{code:3} --   no checkout has this course")
            failed += 1
            continue
        lenient = ["--lenient"] if code in ("zh", "ja") else []
        r = subprocess.run([str(PY), "tools/validate_course.py", code, "--fluency", band, *lenient],
                           cwd=d, capture_output=True, text=True)
        lines = r.stdout.splitlines()
        head = next((l for l in lines if " content to " in l), lines[0] if lines else r.stderr[-200:])
        gaps = [l.strip() for l in lines if l.strip().startswith("x ")][:2]
        mark = "OK " if r.returncode == 0 else "-- "
        print(f"{code:3} {mark} {branch:32} {head.strip()}")
        for g in gaps:
            print(f"{'':42}{g}")
        failed += r.returncode != 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
