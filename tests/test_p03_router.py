import pytest

from agentbook.model import FakeModel
from agentbook.patterns import router as p


def test_example_routes_to_billing():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert outcome.extra["route"] == "billing"
    assert counter.calls == 2


def test_label_is_cleaned_before_matching():
    fake = FakeModel(["Technical.", "Restart the router."])
    outcome = p.route(fake, "Wifi is down", p.support_desk(fake))
    assert outcome.extra["route"] == "technical"


def test_failure_case_unknown_label_falls_back_to_default():
    """Broken case: the model rambles instead of giving one label from the list."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "fallback"
    assert outcome.extra["route"] == "general"
    assert counter.calls == 1  # the general handler needs no model call


def test_router_refuses_to_start_without_its_default():
    with pytest.raises(ValueError):
        p.route(FakeModel(["x"]), "hi", {"billing": str}, default="general")
