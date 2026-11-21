"""Copy the current code into every lesson quote.

    python scripts/fill_quotes.py          rewrite lessons in place
    python scripts/fill_quotes.py --check  only report quotes that drifted

Use it after you write a lesson with `#def:name` markers. Run --check in CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from quotes import ROOT, check_text, fill_text  # noqa: E402


def main(argv: list[str]) -> int:
    lessons = sorted((ROOT / "docs" / "lessons").glob("*.md"))
    problems = []
    for lesson in lessons:
        text = lesson.read_text()
        if "--check" in argv:
            problems += [f"{lesson.name}: {p}" for p in check_text(text)]
        else:
            lesson.write_text(fill_text(text))
    for problem in problems:
        print(problem)
    print(f"{len(lessons)} lessons, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
