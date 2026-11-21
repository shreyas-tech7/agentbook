"""Pattern 4. Prompt chain with gates.

Fixed steps run in a fixed order. Each step's output is the next step's input.
A gate is plain code that checks an output before the chain goes on.

Failure: one step returns output that breaks a rule, such as a summary that is too long.
Guard: the gate stops the chain at that step. Later steps never run.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model
from agentbook.tools import Outcome, user


@dataclass
class Step:
    name: str
    prompt: str  # a template with {input}
    gate: Callable[[str], bool] | None = None


def run_chain(model: Model, text: str, steps: list[Step]) -> Outcome:
    current = text
    outputs: dict[str, str] = {}
    for number, step in enumerate(steps, 1):
        current = model.complete([user(step.prompt.format(input=current))]).text.strip()
        outputs[step.name] = current
        if step.gate is not None and not step.gate(current):
            return Outcome(current, "gate_failed", steps=number,
                           extra={"failed_gate": step.name, "outputs": outputs})
    return Outcome(current, "done", steps=len(steps), extra={"outputs": outputs})


def max_words(limit: int) -> Callable[[str], bool]:
    return lambda text: 0 < len(text.split()) <= limit


SUMMARY_THEN_TITLE = [
    Step("summary", "Summarize this note in at most 25 words:\n{input}", gate=max_words(25)),
    Step("title", "Write a title of at most 6 words for this summary:\n{input}",
         gate=lambda t: max_words(6)(t) and not t.endswith(".")),
]

NOTE = ("The team met on Monday. We agreed to move the launch to March because the "
        "payment tests still fail on two banks. Priya will fix the tests this week.")


def example() -> tuple[Outcome, CallCounter]:
    """A note becomes a short summary, then a title. Both gates pass."""
    fake = FakeModel(["The launch moves to March because payment tests fail. Priya fixes "
                      "them this week.", "Launch Moves To March"])
    counter = CallCounter(fake)
    return run_chain(counter, NOTE, SUMMARY_THEN_TITLE), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The summary is far too long. The first gate fails, so the title step never runs."""
    long_summary = " ".join(["The meeting covered many details about the launch."] * 6)
    fake = FakeModel([long_summary, "This title is never requested"])
    counter = CallCounter(fake)
    return run_chain(counter, NOTE, SUMMARY_THEN_TITLE), counter
