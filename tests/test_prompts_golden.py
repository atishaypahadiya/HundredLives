"""Prompt wording is part of the experiment: a changed prompt makes runs incomparable. This renders
every agent-, referee- and contact-facing prompt (scripts/render_prompts.py, no model calls) and
compares sha256s with tests/golden/prompts.txt.

A failure means a prompt changed. If that was meant, say so in the commit message and refresh:

    UPDATE_GOLDEN=1 uv run pytest tests/test_prompts_golden.py

and diff the texts with `scripts/render_prompts.py --full` on both commits to see what moved.
"""

import hashlib
import os

import orchestrator.run as R
from scripts.render_prompts import renders
from tests.harness import ROOT

PAIRS = [("maya.yaml", "openings.yaml"), ("self.yaml", "student.yaml"), ("self.yaml", "student-v3.yaml"),
         ("self.yaml", "student-hiddenstreak.yaml"), ("self-nosolo.yaml", "student.yaml"),
         ("self-socialgoal.yaml", "student.yaml"), ("self-goalonly.yaml", "student.yaml")]
GOLDEN = ROOT / "tests/golden/prompts.txt"


def current() -> str:
    runs_dir = R.RUNS_DIR
    lines = []
    try:
        for p, w in PAIRS:
            for sandbox in (True, False):
                for k, v in renders(ROOT / "agents/personas" / p, ROOT / "world" / w, sandbox).items():
                    lines.append(f"{hashlib.sha256(v.encode()).hexdigest()[:16]}  {p} {w} "
                                 f"{'sandbox' if sandbox else 'nosandbox'} {k}")
    finally:
        R.RUNS_DIR = runs_dir
    return "\n".join(lines) + "\n"


def test_prompts_unchanged():
    got = current()
    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(got)
    want = GOLDEN.read_text()
    changed = sorted({line.split("  ", 1)[1] for line in set(got.splitlines()) ^ set(want.splitlines())})
    assert not changed, "prompts changed:\n  " + "\n  ".join(changed)


def test_maya_prompts_do_not_depend_on_student_world_features():
    # The student-world mechanics switch on only from their own world keys, so Maya's prompts
    # never mention them.
    text = "\n".join(renders(ROOT / "agents/personas/maya.yaml", ROOT / "world/openings.yaml", False).values())
    for word in ("semester", "visa", "hackathon", "streak", "mock web", "invest_personal"):
        assert word not in text.lower(), word
