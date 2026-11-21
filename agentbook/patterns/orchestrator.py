"""Pattern 6. Orchestrator and workers.

A lead call reads the task and decides the subtasks at run time.
Workers do one subtask each. A last call joins their work.
Use it when you cannot list the subtasks before you see the task.

Failure: the lead asks for far too many workers, or returns a plan our code cannot read.
Guard: our code checks the plan first. A bad plan or more than `max_workers`
subtasks stops the run before any worker is paid for.
"""

from __future__ import annotations

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model
from agentbook.tools import Outcome, parse_json, system, user

LEAD = 'Split the task into subtasks. Reply with a JSON list of strings, like ["a", "b"].'
WORKER = "Do your part of the task. Reply with the result only."
JOIN = "Join the parts into one answer. Keep it short."


def orchestrate(model: Model, task: str, max_workers: int = 4) -> Outcome:
    plan = parse_json(model.complete([system(LEAD), user(task)]).text)
    if not isinstance(plan, list) or not plan or not all(isinstance(p, str) for p in plan):
        return Outcome(None, "bad_plan", steps=1)
    if len(plan) > max_workers:
        return Outcome(None, "too_many_workers", steps=1, extra={"asked_for": len(plan)})
    parts = []
    for subtask in plan:
        prompt = f"Whole task: {task}\nYour part: {subtask}"
        parts.append(f"{subtask}: {model.complete([system(WORKER), user(prompt)]).text}")
    answer = model.complete([system(JOIN), user("\n".join(parts))]).text
    return Outcome(answer, "done", steps=len(plan) + 2, extra={"plan": plan, "parts": parts})


TASK = "Rename the function load_cfg to load_config in this small project."


def example() -> tuple[Outcome, CallCounter]:
    """The lead finds two files to change. Two workers, then one join. Four calls."""
    fake = FakeModel([
        '["update app.py", "update tests/test_app.py"]',
        "app.py: renamed the definition and one call",
        "tests/test_app.py: renamed two calls",
        "Renamed load_cfg to load_config in app.py and tests/test_app.py.",
    ])
    counter = CallCounter(fake)
    return orchestrate(counter, TASK), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The lead asks for 40 workers. The guard stops the run after one call."""
    huge_plan = "[" + ", ".join(f'"check file {n}"' for n in range(40)) + "]"
    counter = CallCounter(FakeModel([huge_plan]))
    return orchestrate(counter, TASK), counter
