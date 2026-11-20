from agentbook.model import FakeModel
from agentbook.patterns import prompt_chain as p


def test_example_passes_both_gates():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert outcome.answer == "Launch Moves To March"
    assert counter.calls == 2


def test_each_step_gets_the_last_output():
    fake = FakeModel(["short summary", "Short Title"])
    p.run_chain(fake, "note", p.SUMMARY_THEN_TITLE)
    assert "short summary" in fake.seen[1][0]["content"]


def test_failure_case_gate_stops_the_chain():
    """Broken case: the summary has 48 words, far over the 25-word limit."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "gate_failed"
    assert outcome.extra["failed_gate"] == "summary"
    assert counter.calls == 1  # the title step never ran


def test_title_gate_rejects_a_sentence():
    fake = FakeModel(["fine summary", "This is a sentence."])
    assert p.run_chain(fake, "note", p.SUMMARY_THEN_TITLE).extra["failed_gate"] == "title"
