from agentbook.model import FakeModel
from agentbook.patterns import plan_execute as p


def test_parse_plan_keeps_numbered_lines():
    assert p.parse_plan("Plan:\n1. a\n2) b\nnote\n3. c") == ["a", "b", "c"]


def test_example_runs_every_step():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert len(outcome.answer) == 3
    assert counter.calls == 4


def test_each_step_sees_what_was_done_before():
    outcome, _ = p.example()
    assert outcome.stop == "done"
    fake = FakeModel([p.PLAN, "a", "b", "c"])
    p.plan_and_execute(fake, "goal", p.short_and_not_empty)
    assert "- a\n- b" in fake.seen[3][1]["content"]


def test_failure_case_check_stops_at_the_bad_step():
    """Broken case: step 2 returns an empty string. Step 3 would build on nothing."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "check_failed"
    assert outcome.extra["failed_step"] == "List toiletries"
    assert counter.calls == 3  # the plan, step 1 and step 2. Step 3 never ran.


def test_a_plan_that_is_too_long_is_rejected():
    plan = "\n".join(f"{n}. step {n}" for n in range(1, 21))
    fake = FakeModel([plan])
    outcome = p.plan_and_execute(fake, "goal", p.short_and_not_empty, max_plan=6)
    assert outcome.stop == "plan_too_long"
    assert len(fake.seen) == 1


def test_an_empty_plan_stops_early():
    assert p.plan_and_execute(FakeModel(["Sure!"]), "g", p.short_and_not_empty).stop == \
        "empty_plan"
