"""Run all 36 solutions. A solution checks its own answer with assert."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "solutions"))

FILES = sorted(p.stem for p in (ROOT / "solutions").glob("s[0-9][0-9]_*.py"))


def test_there_are_twelve_solution_files():
    assert len(FILES) == 12


@pytest.mark.parametrize("number", [1, 2, 3])
@pytest.mark.parametrize("stem", FILES)
def test_solution_runs(stem, number):
    module = importlib.import_module(stem)
    getattr(module, f"solution_{number}")()
