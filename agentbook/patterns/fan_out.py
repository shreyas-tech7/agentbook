"""Pattern 5. Fan-out and fan-in.

Independent subtasks run side by side in threads. Then one call merges the results.
The subtasks are known before the run starts. That is the difference from pattern 6.

Failure: one worker crashes or hangs, and the merge step waits or breaks.
Guard: all workers share one deadline. A failed worker becomes a "MISSING" line,
so the merge still runs and the stop reason says "partial".
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Message, Model
from agentbook.tools import Outcome, system, user

MERGE = "Merge these reviews into one short list. Mention any missing review."


def fan_out(model: Model, text: str, angles: list[str], max_parallel: int = 4,
            timeout: float = 30.0) -> Outcome:
    def work(angle: str) -> str:
        return model.complete([system(f"Review the text for {angle} only."), user(text)]).text

    pool = ThreadPoolExecutor(max_workers=max_parallel)
    futures = [pool.submit(work, angle) for angle in angles]
    wait(futures, timeout=timeout)  # one shared deadline for all workers
    pool.shutdown(wait=False, cancel_futures=True)  # do not wait for a hung worker
    parts, missing = [], []
    for angle, future in zip(angles, futures, strict=True):
        if not future.done() or future.cancelled() or future.exception():
            why = "Timeout" if not future.done() or future.cancelled() else \
                type(future.exception()).__name__
            missing.append(angle)
            parts.append(f"{angle}: MISSING ({why})")
        else:
            parts.append(f"{angle}: {future.result()}")
    if len(missing) == len(angles):
        return Outcome(None, "all_failed", extra={"missing": missing})
    merged = model.complete([system(MERGE), user("\n".join(parts))]).text
    stop = "partial" if missing else "done"
    return Outcome(merged, stop, steps=len(angles) + 1, extra={"parts": parts, "missing": missing})


ANGLES = ["grammar", "clarity", "tone"]
TEXT = "Their going to ship the update next week, its mostly ready and honestly fine."
REVIEWS = {"grammar": "Use 'They're' and 'it's'.", "clarity": "Say which update.",
           "tone": "Drop 'honestly'."}


def reviewer(broken: str | None = None):
    """A fake reviewer that answers by angle. The `broken` angle raises an error."""
    def respond(messages: list[Message]) -> str:
        prompt = messages[0]["content"]
        if prompt == MERGE:
            return "Fix: " + " ".join(line.split(": ", 1)[1] for line in
                                      messages[1]["content"].splitlines())
        angle = prompt.removeprefix("Review the text for ").removesuffix(" only.")
        if angle == broken:
            raise ConnectionError(f"{angle} worker lost its connection")
        return REVIEWS[angle]
    return respond


def example() -> tuple[Outcome, CallCounter]:
    """Three reviews run in parallel, then one merge call. Four calls in total."""
    counter = CallCounter(FakeModel(respond=reviewer()))
    return fan_out(counter, TEXT, ANGLES), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The tone worker crashes. The merge still runs and reports the gap."""
    counter = CallCounter(FakeModel(respond=reviewer(broken="tone")))
    return fan_out(counter, TEXT, ANGLES), counter
