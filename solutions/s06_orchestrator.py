"""Solutions for lesson 6, orchestrator and workers."""

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel
from agentbook.patterns.orchestrator import TASK, orchestrate


def solution_1():
    """One lead call, four worker calls and one join call make six."""
    counter = CallCounter(FakeModel(['["a", "b", "c", "d"]', "1", "2", "3", "4", "all done"]))
    outcome = orchestrate(counter, TASK, max_workers=4)
    assert (outcome.stop, counter.calls) == ("done", 6)
    return counter.calls


def solution_2():
    """parse_json strips the fence, so the plan still reads."""
    fenced = '```json\n["update app.py"]\n```'
    outcome = orchestrate(FakeModel([fenced, "renamed", "Renamed in app.py."]), TASK)
    assert outcome.stop == "done" and outcome.extra["plan"] == ["update app.py"]
    return outcome.extra["plan"]


def solution_3():
    """The plan comes from the lead's reply: `plan = parse_json(model.complete(...))`.
    In fan-out, the caller passes the list in."""
    fake = FakeModel(['["update app.py", "update README.md"]', "x", "y", "joined"])
    outcome = orchestrate(fake, TASK)
    assert outcome.extra["plan"] == ["update app.py", "update README.md"]
    return outcome.extra["plan"]


if __name__ == "__main__":
    _run.run(globals())
