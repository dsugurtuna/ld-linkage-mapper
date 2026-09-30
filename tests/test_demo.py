"""Smoke test: the README quickstart demo runs and prints what the README shows."""

import runpy
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent / "examples" / "demo.py"


def test_demo_output(capsys):
    runpy.run_path(str(DEMO), run_name="__main__")
    out = capsys.readouterr().out
    assert "rs9000001: kept 1 (rs9000011); blocklisted 1" in out
    assert "rs9000001: 2 of 5 participants" in out
    assert "rs9000002: 1 of 5 participants" in out
