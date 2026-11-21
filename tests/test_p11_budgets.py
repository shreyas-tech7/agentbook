from agentbook.model import FakeModel, call
from agentbook.patterns import budgets as p


def test_over_budget_names_the_first_limit():
    budget = p.Budget(max_steps=3, max_tokens=100, max_seconds=5)
    assert p.over_budget(budget, 0, 0, 0) is None
    assert p.over_budget(budget, 3, 0, 0) == "max_steps"
    assert p.over_budget(budget, 0, 100, 0) == "max_tokens"
    assert p.over_budget(budget, 0, 0, 5) == "max_seconds"


def test_example_finishes_inside_the_budget():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert counter.calls == 2


def test_failure_case_token_budget_stops_a_chatty_model():
    """Broken case: the model reads note after note and never answers."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "max_tokens"
    assert counter.tokens >= 1_500
    assert counter.calls < 50  # the step limit was not what stopped it


def test_time_budget_with_a_fake_clock():
    """Broken case: each call takes 10 fake seconds. The time limit is 25 seconds."""
    now = [0.0]

    def clock():
        return now[0]

    def slow(messages):
        now[0] += 10
        return call("read_note", id="1")

    budget = p.Budget(max_steps=100, max_tokens=10**9, max_seconds=25)
    outcome = p.run_with_budget(FakeModel(respond=slow), "q", p.NOTES, budget, clock=clock)
    assert outcome.stop == "max_seconds"
    assert outcome.steps == 3


def test_step_budget():
    fake = FakeModel(respond=lambda m: call("read_note", id="1"))
    outcome = p.run_with_budget(fake, "q", p.NOTES, p.Budget(max_steps=2, max_tokens=10**9))
    assert outcome.stop == "max_steps"
