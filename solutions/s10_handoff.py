"""Solutions for lesson 10, handoff."""

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, call
from agentbook.patterns.handoff import DESK, Agent, run_handoffs


def solution_1():
    """A new agent is one record, plus its name in triage's list."""
    agents = {**DESK, "billing": Agent("billing", "You fix billing errors.")}
    agents["triage"] = Agent("triage", DESK["triage"].instructions,
                             DESK["triage"].can_hand_to + ("billing",))
    fake = FakeModel([call("handoff", to="billing", note="charged twice"), "Refunded one charge."])
    outcome = run_handoffs(fake, agents, "triage", "I was charged twice.")
    assert outcome.extra["path"] == ["triage", "billing"]
    return outcome.extra["path"]


def solution_2():
    """One handoff is allowed. The second attempt stops the run. Two calls."""
    def ping_pong(messages):
        me = "refunds" if "refunds only" in messages[0]["content"] else "shipping"
        return call("handoff", to="shipping" if me == "refunds" else "refunds", note="not mine")

    counter = CallCounter(FakeModel(respond=ping_pong))
    outcome = run_handoffs(counter, DESK, "refunds", "late and broken", max_handoffs=1)
    assert (outcome.stop, outcome.extra["path"], counter.calls) == \
        ("max_handoffs", ["refunds", "shipping"], 2)
    return outcome.extra["path"], counter.calls


def solution_3():
    """The last message is the handoff line with the note."""
    fake = FakeModel([call("handoff", to="shipping", note="parcel 9 is lost"), "Found it."])
    run_handoffs(fake, DESK, "triage", "Where is parcel 9?")
    last = fake.seen[1][-1]["content"]
    assert last == "[triage -> shipping] parcel 9 is lost"
    return last


if __name__ == "__main__":
    _run.run(globals())
