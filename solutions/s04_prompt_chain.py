"""Solutions for lesson 4, the prompt chain."""

import _run

from agentbook.counter import CallCounter
from agentbook.model import FakeModel
from agentbook.patterns.prompt_chain import NOTE, SUMMARY_THEN_TITLE, Step, max_words, run_chain


def solution_1():
    """A new step is one more Step in the list."""
    steps = SUMMARY_THEN_TITLE + [Step("french", "Translate into French:\n{input}",
                                       gate=lambda t: bool(t.strip()))]
    fake = FakeModel(["Launch moves to March.", "Launch Moves To March", "Le lancement en mars"])
    outcome = run_chain(fake, NOTE, steps)
    assert outcome.stop == "done" and outcome.answer == "Le lancement en mars"
    return outcome.answer


def solution_2():
    """The title gate rejects a final dot. Both steps ran, so there were two calls."""
    counter = CallCounter(FakeModel(["Launch moves to March.", "Launch moves to March."]))
    outcome = run_chain(counter, NOTE, SUMMARY_THEN_TITLE)
    assert (outcome.extra["failed_gate"], counter.calls) == ("title", 2)
    return outcome.extra["failed_gate"], counter.calls


def solution_3():
    """Gates combine like any boolean functions."""
    def short_and_mentions_march(text):
        return max_words(25)(text) and "march" in text.lower()

    steps = [Step("summary", SUMMARY_THEN_TITLE[0].prompt, gate=short_and_mentions_march)]
    bad = run_chain(FakeModel(["The launch moves to spring."]), NOTE, steps)
    good = run_chain(FakeModel(["The launch moves to March."]), NOTE, steps)
    assert (bad.stop, good.stop) == ("gate_failed", "done")
    return bad.stop, good.stop


if __name__ == "__main__":
    _run.run(globals())
