from agentbook.model import FakeModel
from agentbook.patterns import orchestrator as p


def test_example_lead_workers_join():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert outcome.extra["plan"] == ["update app.py", "update tests/test_app.py"]
    assert counter.calls == 4


def test_workers_get_the_whole_task_and_their_part():
    fake = FakeModel(['["part A"]', "did A", "joined"])
    p.orchestrate(fake, "big task")
    assert fake.seen[1][1]["content"] == "Whole task: big task\nYour part: part A"


def test_failure_case_too_many_workers_stops_before_any_worker():
    """Broken case: the lead asks for 40 workers. That would be 41 more calls."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "too_many_workers"
    assert outcome.extra["asked_for"] == 40
    assert counter.calls == 1


def test_unreadable_plan_stops_the_run():
    """Broken case: the lead replies with prose instead of a JSON list."""
    for bad in ["I would first look at app.py.", '{"a": 1}', "[]", "[1, 2]"]:
        assert p.orchestrate(FakeModel([bad]), "task").stop == "bad_plan"
