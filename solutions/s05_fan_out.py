"""Solutions for lesson 5, fan-out and fan-in."""

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel
from agentbook.patterns.fan_out import ANGLES, MERGE, REVIEWS, TEXT, fan_out, reviewer


def solution_1():
    """Four workers plus one merge make five calls."""
    REVIEWS_PLUS = {**REVIEWS, "length": "Fine at one line."}

    def respond(messages):
        prompt = messages[0]["content"]
        if prompt == MERGE:
            return "merged"
        return REVIEWS_PLUS[prompt.removeprefix("Review the text for ").removesuffix(" only.")]

    counter = CallCounter(FakeModel(respond=respond))
    outcome = fan_out(counter, TEXT, ANGLES + ["length"])
    assert (outcome.stop, counter.calls) == ("done", 5)
    return counter.calls


def solution_2():
    """One good worker is enough for a merge. The stop reason is still partial."""
    good = reviewer()

    def respond(messages):
        if messages[0]["content"].endswith(("clarity only.", "tone only.")):
            raise TimeoutError("slow worker")
        return good(messages)

    outcome = fan_out(FakeModel(respond=respond), TEXT, ANGLES)
    assert (outcome.stop, outcome.extra["missing"]) == ("partial", ["clarity", "tone"])
    return outcome.extra["missing"]


def solution_3():
    """The answer is the same. Only the time changes, because the workers run one by one."""
    fast = fan_out(FakeModel(respond=reviewer()), TEXT, ANGLES)
    serial = fan_out(FakeModel(respond=reviewer()), TEXT, ANGLES, max_parallel=1)
    assert fast.answer == serial.answer
    return serial.answer


if __name__ == "__main__":
    _run.run(globals())
