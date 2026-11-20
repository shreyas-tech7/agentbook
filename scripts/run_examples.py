"""Run every pattern's example and failure case with the FakeModel. Write results/call_counts.json.

    python scripts/run_examples.py          write the file
    python scripts/run_examples.py --check  fail if the file is out of date

The runs are scripted, so the counts are fixed numbers with no sampling error.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentbook.patterns import ORDER, load  # noqa: E402

OUT = ROOT / "results" / "call_counts.json"


def measure() -> dict:
    patterns = []
    for number, (name, title) in enumerate(ORDER, 1):
        module = load(name)
        row = {"number": number, "name": name, "title": title}
        for label, run in (("example", module.example), ("failure", module.failure_example)):
            outcome, counter = run()
            row[label] = {"stop": outcome.stop, **counter.summary()}
        patterns.append(row)
    return {"source": "FakeModel scripted runs (no real model)", "seed": "none (deterministic)",
            "token_estimate": "characters / 4, rounded up", "patterns": patterns}


def main(argv: list[str]) -> int:
    data = measure()
    if "--check" in argv:
        old = json.loads(OUT.read_text())
        old.pop("generated_on", None)
        if old != data:
            print("results/call_counts.json is out of date. Run scripts/run_examples.py")
            return 1
        print("results/call_counts.json is up to date")
        return 0
    data["generated_on"] = datetime.date.today().isoformat()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
