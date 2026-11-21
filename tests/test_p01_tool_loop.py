from agentbook.counter import CallCounter
from agentbook.model import FakeModel, call, say
from agentbook.patterns import tool_loop as p


def test_example_uses_the_tool_then_answers():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert outcome.answer == "19 + 23 = 42"
    assert {"role": "tool", "name": "add", "content": "42"} in outcome.trace
    assert counter.calls == 2


def test_tool_errors_go_back_to_the_model():
    fake = FakeModel([call("multiply", a="2", b="3"), say("I only have add.")])
    outcome = p.tool_loop(fake, "2 times 3?", p.CALCULATOR)
    assert "unknown tool 'multiply'" in outcome.trace[3]["content"]
    assert outcome.stop == "done"


def test_failure_case_step_limit_stops_a_stuck_model():
    """Broken case: the model asks for `add` forever. Without max_steps the loop never ends."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "max_steps"
    assert outcome.answer is None
    assert counter.calls == 5


def test_step_limit_is_what_stops_it():
    """The same stuck model runs longer when the limit is higher, so the limit is the guard."""
    counter = CallCounter(FakeModel(respond=lambda m: call("add", a="1", b="1")))
    assert p.tool_loop(counter, "1+1?", p.CALCULATOR, max_steps=11).stop == "max_steps"
    assert counter.calls == 11
