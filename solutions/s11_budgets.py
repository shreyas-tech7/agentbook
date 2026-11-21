"""Solutions for lesson 11, budgets and stop rules."""

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, call, say
from agentbook.patterns.budgets import NOTES, Budget, run_with_budget


def example_model():
    return FakeModel([call("read_note", id="1"), say("The shop opens at 9.")])


def solution_1():
    """One step is spent on the tool call. The check before call 2 stops the run."""
    counter = CallCounter(example_model())
    outcome = run_with_budget(counter, "When does the shop open?", NOTES, Budget(max_steps=1))
    assert (outcome.stop, counter.calls) == ("max_steps", 1)
    return outcome.stop, counter.calls


def solution_2():
    """The check before call 2 needs tokens < max_tokens. So the answer is the cost of
    call 1, plus one. We find it by search, then confirm it with that rule."""
    for limit in range(1, 2_000):
        counter = CallCounter(example_model())
        outcome = run_with_budget(counter, "When does the shop open?", NOTES,
                                  Budget(max_tokens=limit))
        if outcome.stop == "done":
            break
    one_call = run_with_budget(example_model(), "When does the shop open?", NOTES,
                               Budget(max_steps=1))
    assert limit == one_call.extra["tokens"] + 1
    return limit


def solution_3():
    """The checks happen at 0, 7, 14 and 21 seconds. 21 is over 20, so three calls ran."""
    now = [0.0]

    def slow(messages):
        now[0] += 7
        return call("read_note", id="1")

    counter = CallCounter(FakeModel(respond=slow))
    outcome = run_with_budget(counter, "q", NOTES, Budget(max_steps=99, max_tokens=10**9,
                                                          max_seconds=20), clock=lambda: now[0])
    assert (outcome.stop, counter.calls) == ("max_seconds", 3)
    return counter.calls


if __name__ == "__main__":
    _run.run(globals())
