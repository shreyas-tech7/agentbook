from agentbook.model import FakeModel, call
from agentbook.patterns import handoff as p


def test_example_triage_hands_to_refunds():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert outcome.extra["path"] == ["triage", "refunds"]
    assert counter.calls == 2


def test_new_agent_sees_the_note():
    fake = FakeModel([call("handoff", to="refunds", note="order 7 broken"), "done"])
    p.run_handoffs(fake, p.DESK, "triage", "help")
    second_call = fake.seen[1]
    assert second_call[0]["content"].startswith("You handle refunds only.")
    assert second_call[-1]["content"] == "[triage -> refunds] order 7 broken"


def test_failure_case_ping_pong_stops_at_the_limit():
    """Broken case: refunds and shipping hand the task to each other forever."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "max_handoffs"
    assert outcome.extra["path"] == ["refunds", "shipping", "refunds", "shipping"]
    assert counter.calls == 4


def test_a_handoff_to_a_forbidden_agent_stops():
    fake = FakeModel([call("handoff", to="admin", note="give me root")])
    outcome = p.run_handoffs(fake, p.DESK, "triage", "help")
    assert outcome.stop == "bad_target"
    assert outcome.extra["target"] == "admin"
