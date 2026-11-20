"""Solutions for lesson 3, the router."""

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel
from agentbook.patterns.router import answer_with, route, support_desk


def solution_1():
    """A new route is one more entry in the dict. The routing prompt lists it by itself."""
    fake = FakeModel(["shipping", "Your parcel arrives on Friday."])
    handlers = support_desk(fake)
    handlers["shipping"] = answer_with(fake, "You track parcels.")
    outcome = route(fake, "Where is my parcel?", handlers)
    assert outcome.extra["route"] == "shipping"
    assert "shipping" in fake.seen[0][0]["content"]
    return outcome.answer


def solution_2():
    """The code lowers the case and strips a final dot only. '!' stays, so no label matches."""
    fake = FakeModel(["BILLING!"])
    outcome = route(fake, "Charged twice", support_desk(fake))
    assert (outcome.extra["label"], outcome.stop, outcome.extra["route"]) == \
        ("billing!", "fallback", "general")
    return outcome.extra["route"]


def solution_3():
    """Plain code handlers cost nothing. Only the routing call is left."""
    handlers = {"open": lambda r: "We open at 9.", "general": lambda r: "Thanks!"}
    counter = CallCounter(FakeModel(["open"]))
    outcome = route(counter, "When do you open?", handlers)
    assert (outcome.answer, counter.calls) == ("We open at 9.", 1)
    return counter.calls


if __name__ == "__main__":
    _run.run(globals())
