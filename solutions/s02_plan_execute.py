"""Solutions for lesson 2, plan and execute."""

import re

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel
from agentbook.patterns.plan_execute import PLAN, plan_and_execute


def solution_1():
    """The check is your own code. Any rule you can write in Python works."""
    def no_todo(step, output):
        return "TODO" not in output

    outcome = plan_and_execute(FakeModel([PLAN, "TODO later"]), "Pack", no_todo)
    assert outcome.stop == "check_failed"
    return outcome.stop


def solution_2():
    """Only the planning call runs. The plan is rejected before any step."""
    plan = "\n".join(f"{n}. step {n}" for n in range(1, 8))
    counter = CallCounter(FakeModel([plan]))
    outcome = plan_and_execute(counter, "goal", lambda s, o: True, max_plan=6)
    assert (outcome.stop, counter.calls) == ("plan_too_long", 1)
    return counter.calls


def solution_3():
    """One regular expression with two choices covers both forms."""
    def parse_steps(text):
        found = []
        for line in text.splitlines():
            match = re.match(r"\s*(?:step\s+)?\d+\s*[.):]\s*(.+)", line, re.I)
            if match:
                found.append(match.group(1).strip())
        return found

    steps = parse_steps("Step 1: shirts\n2. socks\nnote\nstep 3) soap")
    assert steps == ["shirts", "socks", "soap"]
    return steps


if __name__ == "__main__":
    _run.run(globals())
