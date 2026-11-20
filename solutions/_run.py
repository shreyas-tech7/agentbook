"""Run the three solutions in a file and print their answers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def run(namespace: dict) -> None:
    for number in (1, 2, 3):
        print(f"solution_{number}: {namespace[f'solution_{number}']()}")
