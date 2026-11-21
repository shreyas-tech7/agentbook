"""Pattern 11. Budgets and stop rules.

An agent loop needs limits on steps, tokens and time.
Before every model call, we check all three. The first limit that is reached ends the run,
and the stop reason names it.

Failure: a chatty model keeps calling tools and burns tokens without an answer.
Guard: the token budget stops it with "max_tokens". The time budget uses a clock
that tests can control, so the time stop is tested without waiting.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

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


@dataclass(frozen=True)
class Budget:
    max_steps: int = 10
    max_tokens: int = 2_000
    max_seconds: float = 60.0


def over_budget(budget: Budget, steps: int, tokens: int, seconds: float) -> str | None:
    """Return the name of the first limit that is used up, or None."""
    if steps >= budget.max_steps:
        return "max_steps"
    if tokens >= budget.max_tokens:
        return "max_tokens"
    if seconds >= budget.max_seconds:
        return "max_seconds"
    return None


def run_with_budget(model: Model, task: str, tools: dict[str, Tool], budget: Budget,
                    clock: Callable[[], float] = time.monotonic) -> Outcome:
    counter = model if isinstance(model, CallCounter) else CallCounter(model)
    start, steps = clock(), 0
    messages = [system("Use tools if you need them. Then answer in plain text."), user(task)]
    while True:
        stop = over_budget(budget, steps, counter.tokens, clock() - start)
        if stop:
            return Outcome(None, stop, steps=steps, trace=messages, extra=counter.summary())
        reply = counter.complete(messages, specs(tools))
        steps += 1
        messages.append(assistant(reply))
        if reply.tool_call is None:
            return Outcome(reply.text, "done", steps=steps, trace=messages, extra=counter.summary())
        messages.append(tool_result(reply.tool_call.name, run_tool(tools, reply.tool_call)))


NOTES = toolbox(Tool("read_note", "Read the note with this id.",
                     lambda id: f"Note {id}: " + "the shop opens at nine. " * 20,
                     {"id": "note id"}))


def example() -> tuple[Outcome, CallCounter]:
    """One tool call, then an answer. Well inside every limit. Two calls."""
    counter = CallCounter(FakeModel([call("read_note", id="1"), say("The shop opens at 9.")]))
    budget = Budget(max_steps=5, max_tokens=2_000, max_seconds=30)
    return run_with_budget(counter, "When does the shop open?", NOTES, budget), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The model reads note after note and never answers. The token budget stops it."""
    reads = iter(range(1, 100))
    counter = CallCounter(FakeModel(respond=lambda m: call("read_note", id=str(next(reads)))))
    budget = Budget(max_steps=50, max_tokens=1_500, max_seconds=30)
    return run_with_budget(counter, "When does the shop open?", NOTES, budget), counter
