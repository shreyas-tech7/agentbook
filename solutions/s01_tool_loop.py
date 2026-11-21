"""Solutions for lesson 1, the tool loop."""

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, call, say
from agentbook.patterns.tool_loop import CALCULATOR, add, tool_loop
from agentbook.tools import Tool, toolbox


def solution_1():
    """A new tool is one Tool record. The loop needs no change."""
    tools = toolbox(*CALCULATOR.values(),
                    Tool("multiply", "Multiply two whole numbers.",
                         lambda a, b: str(int(a) * int(b)), {"a": "first", "b": "second"}))
    fake = FakeModel([call("multiply", a="6", b="7"), say("6 times 7 is 42")])
    outcome = tool_loop(fake, "What is 6 times 7?", tools)
    assert outcome.trace[3] == {"role": "tool", "name": "multiply", "content": "42"}
    return outcome.answer


def solution_2():
    """One step is spent on the tool call. No step is left for the answer."""
    counter = CallCounter(FakeModel([call("add", a="1", b="2"), say("3")]))
    outcome = tool_loop(counter, "1 + 2?", CALCULATOR, max_steps=1)
    assert (outcome.stop, counter.calls) == ("max_steps", 1)
    return outcome.stop, counter.calls


def solution_3():
    """The model reads the last message. A tool result means it is time to answer."""
    def respond(messages):
        last = messages[-1]
        if last["role"] == "tool":
            return say(f"The answer is {last['content']}.")
        return call("add", a="40", b="2")

    outcome = tool_loop(FakeModel(respond=respond), "40 + 2?", CALCULATOR)
    assert outcome.answer == f"The answer is {add('40', '2')}."
    return outcome.answer


if __name__ == "__main__":
    _run.run(globals())
