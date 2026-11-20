"""Record mode: run three patterns against a real OpenAI-compatible endpoint.

    python scripts/record_demo.py --status   say whether record mode can run
    python scripts/record_demo.py            run it and write results/live/*.json

Needs AGENTBOOK_BASE_URL and AGENTBOOK_MODEL. AGENTBOOK_API_KEY is read from the
environment and never printed. Send only synthetic text: free tiers may train on prompts.
"""

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agentbook.counter import CallCounter  # noqa: E402
from agentbook.model import OpenAICompatModel  # noqa: E402
from agentbook.patterns import evaluator_optimizer, router, tool_loop  # noqa: E402

LIVE = ROOT / "results" / "live"


def runs(model):
    yield "tool_loop", "Tool loop", lambda m: tool_loop.tool_loop(
        m, "What is 19 + 23? Use the add tool.", tool_loop.CALCULATOR)
    yield "router", "Router", lambda m: router.route(
        m, "Why was I charged twice this month?", router.support_desk(m))
    yield "evaluator_optimizer", "Evaluator and optimizer", lambda m: \
        evaluator_optimizer.optimize(m, evaluator_optimizer.TASK)


def main(argv: list[str]) -> int:
    base, name = os.environ.get("AGENTBOOK_BASE_URL"), os.environ.get("AGENTBOOK_MODEL")
    if "--status" in argv:
        recorded = sorted(p.name for p in LIVE.glob("*.json"))
        print(f"configured: {bool(base and name)}. recorded: {recorded or 'none'}")
        return 0
    if not (base and name):
        print("set AGENTBOOK_BASE_URL and AGENTBOOK_MODEL first (see .env.example)")
        return 2
    model = OpenAICompatModel(base, name)
    LIVE.mkdir(parents=True, exist_ok=True)
    for key, title, run in runs(model):
        counter = CallCounter(model)
        outcome = run(counter)
        record = {"pattern": key, "title": title, "date": datetime.date.today().isoformat(),
                  "model": name, "stop": outcome.stop, "answer": str(outcome.answer),
                  **counter.summary()}
        (LIVE / f"{key}.json").write_text(json.dumps(record, indent=2) + "\n")
        print(f"{title}: {outcome.stop}, {counter.calls} calls")
    print("now run scripts/gen_readme.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
