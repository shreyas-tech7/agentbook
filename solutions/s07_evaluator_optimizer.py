"""Solutions for lesson 7, evaluator and optimizer."""

import re

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel
from agentbook.patterns.evaluator_optimizer import TASK, optimize, read_score


def solution_1():
    """The first review already scores 5, so the first draft wins after two calls."""
    counter = CallCounter(FakeModel(["Tools for everyone.", "SCORE: 5\nNOTES: vague"]))
    outcome = optimize(counter, TASK, threshold=5)
    assert (outcome.stop, outcome.answer, counter.calls) == ("accepted", "Tools for everyone.", 2)
    return outcome.answer, counter.calls


def solution_2():
    """One round means one review and no rewrite."""
    counter = CallCounter(FakeModel(["draft", "SCORE: 2"]))
    outcome = optimize(counter, TASK, max_rounds=1)
    assert (outcome.stop, counter.calls) == ("max_rounds", 2)
    return outcome.stop, counter.calls


def solution_3():
    """The pattern is case sensitive, so it finds nothing and returns 0. re.I fixes that."""
    def read_score_any_case(review):
        match = re.search(r"score:\s*(\d+)", review, re.I)
        return min(int(match.group(1)), 10) if match else 0

    assert read_score("Score: 9") == 0
    assert read_score_any_case("Score: 9") == 9
    return read_score_any_case("Score: 9")


if __name__ == "__main__":
    _run.run(globals())
