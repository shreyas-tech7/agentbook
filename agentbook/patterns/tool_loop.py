"""Pattern 1. Tool loop.

The model asks for a tool. Our code runs it. The result goes back to the model.
This repeats until the model answers in plain text.

Failure: the model never stops asking for tools.
Guard: `max_steps` ends the loop with the stop reason "max_steps".
"""

from __future__ import annotations

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model, call, say
from agentbook.tools import (
    Outcome,
    Tool,
    assistant,
    run_tool,
    specs,
    system,
    tool_result,
    toolbox,
    user,
)

SYSTEM = "You can call tools. When you know the answer, reply with plain text."


def tool_loop(model: Model, task: str, tools: dict[str, Tool], max_steps: int = 8) -> Outcome:
    messages = [system(SYSTEM), user(task)]
    for step in range(1, max_steps + 1):
        reply = model.complete(messages, specs(tools))
        messages.append(assistant(reply))
        if reply.tool_call is None:
            return Outcome(reply.text, "done", steps=step, trace=messages)
        result = run_tool(tools, reply.tool_call)
        messages.append(tool_result(reply.tool_call.name, result))
    return Outcome(None, "max_steps", steps=max_steps, trace=messages)


def add(a: str, b: str) -> str:
    return str(int(a) + int(b))


CALCULATOR = toolbox(Tool("add", "Add two whole numbers.", add, {"a": "first number",
                                                                  "b": "second number"}))


def example() -> tuple[Outcome, CallCounter]:
    """The model adds two numbers with a tool, then answers."""
    fake = FakeModel([call("add", a="19", b="23"), say("19 + 23 = 42")])
    counter = CallCounter(fake)
    return tool_loop(counter, "What is 19 + 23?", CALCULATOR), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """A stuck model asks for the same tool forever. The step limit stops it."""
    fake = FakeModel(respond=lambda messages: call("add", a="1", b="1"))
    counter = CallCounter(fake)
    return tool_loop(counter, "What is 1 + 1?", CALCULATOR, max_steps=5), counter
