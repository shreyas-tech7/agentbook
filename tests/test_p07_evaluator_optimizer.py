from agentbook.model import FakeModel
from agentbook.patterns import evaluator_optimizer as p


def test_read_score():
    assert p.read_score("SCORE: 7\nNOTES: ok") == 7
    assert p.read_score("SCORE: 99") == 10
    assert p.read_score("Looks great!") == 0


def test_example_accepts_the_rewrite():
    outcome, counter = p.example()
    assert outcome.stop == "accepted"
    assert outcome.answer == "Borrow the drill. Keep the money."
    assert outcome.extra["scores"] == [5, 9]
    assert counter.calls == 4


def test_rewrite_sees_the_review():
    fake = FakeModel(["d1", "SCORE: 2\nNOTES: add verbs", "d2", "SCORE: 9"])
    p.optimize(fake, "task")
    assert "add verbs" in fake.seen[2][1]["content"]


def test_failure_case_round_limit_returns_the_best_draft():
    """Broken case: the critic never scores 8 or more, so the loop would never end."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "max_rounds"
    assert outcome.answer == "Borrow tools here."
    assert outcome.extra["best_score"] == 6
    assert counter.calls == 6


def test_a_critic_with_no_score_never_accepts():
    """Broken case: the critic replies 'Perfect!' with no score line."""
    fake = FakeModel(respond=lambda m: "Perfect!")
    outcome = p.optimize(fake, "task", max_rounds=2)
    assert outcome.stop == "max_rounds"
    assert outcome.extra["scores"] == [0, 0]
