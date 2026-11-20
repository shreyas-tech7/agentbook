"""Pattern 2. Plan and execute.

One call writes a numbered plan. Then each step runs, one at a time.
Our code checks each step's output before the next step starts.

Failure: a step returns bad output, and later steps would build on it.
Guard: `check` stops the run at the bad step, so no more calls are spent.
A second guard, `max_plan`, rejects a plan with too many steps.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model
from agentbook.tools import Outcome, system, user

PLANNER = "Write a short numbered plan. One step per line. No other text."
EXECUTOR = "Do only the step you are given. Reply with the result of that step."


def parse_plan(text: str) -> list[str]:
    """Keep the lines that start with a number, such as '1. Pack shirts'."""
    steps = []
    for line in text.splitlines():
        match = re.match(r"\s*\d+[.)]\s*(.+)", line)
        if match:
            steps.append(match.group(1).strip())
    return steps


def plan_and_execute(model: Model, goal: str, check: Callable[[str, str], bool],
                     max_plan: int = 6) -> Outcome:
    plan = parse_plan(model.complete([system(PLANNER), user(goal)]).text)
    if not plan:
        return Outcome(None, "empty_plan")
    if len(plan) > max_plan:
        return Outcome(None, "plan_too_long", extra={"plan": plan})
    results: list[str] = []
    for number, step in enumerate(plan, 1):
        done = "\n".join(f"- {r}" for r in results) or "(nothing yet)"
        prompt = f"Goal: {goal}\nDone so far:\n{done}\nYour step: {step}"
        output = model.complete([system(EXECUTOR), user(prompt)]).text
        if not check(step, output):
            return Outcome(results, "check_failed", steps=number,
                           extra={"plan": plan, "failed_step": step, "bad_output": output})
        results.append(output)
    return Outcome(results, "done", steps=len(plan), extra={"plan": plan})


def short_and_not_empty(step: str, output: str) -> bool:
    """The check used in the examples: the output has text and stays under 120 characters."""
    return 0 < len(output.strip()) < 120


PLAN = "1. List clothes for two days\n2. List toiletries\n3. List documents"


def example() -> tuple[Outcome, CallCounter]:
    """A three-step packing plan where every step passes its check."""
    fake = FakeModel([PLAN, "2 shirts, 1 pair of jeans, socks", "toothbrush, paste, soap",
                      "ID card, train ticket"])
    counter = CallCounter(fake)
    return plan_and_execute(counter, "Pack for a two-day trip", short_and_not_empty), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """Step 2 returns nothing. The check stops the run before step 3 is called."""
    fake = FakeModel([PLAN, "2 shirts, 1 pair of jeans, socks", "", "ID card, train ticket"])
    counter = CallCounter(fake)
    return plan_and_execute(counter, "Pack for a two-day trip", short_and_not_empty), counter
