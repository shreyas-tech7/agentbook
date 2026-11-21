"""Pattern 7. Evaluator and optimizer.

One call writes a draft. Another call scores it and gives notes.
The writer rewrites with the notes. The loop stops on a good score or a round limit.

Failure: the critic is never happy, so the loop would run forever.
Guard: `max_rounds` ends the loop. We return the best draft we saw and its score.
An unreadable score counts as 0, so a broken critic can never accept a draft.
"""

from __future__ import annotations

import re

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model
from agentbook.tools import Outcome, system, user

WRITER = "Write what the task asks. Reply with the text only."
CRITIC = "Score the draft from 0 to 10. Reply as 'SCORE: n' then 'NOTES: ...'."


def read_score(review: str) -> int:
    match = re.search(r"SCORE:\s*(\d+)", review)
    return min(int(match.group(1)), 10) if match else 0


def optimize(model: Model, task: str, threshold: int = 8, max_rounds: int = 3) -> Outcome:
    draft = model.complete([system(WRITER), user(task)]).text
    best_draft, best_score, scores = draft, -1, []
    for round_number in range(1, max_rounds + 1):
        review = model.complete([system(CRITIC), user(f"Task: {task}\nDraft: {draft}")]).text
        score = read_score(review)
        scores.append(score)
        if score > best_score:
            best_draft, best_score = draft, score
        if score >= threshold:
            return Outcome(draft, "accepted", steps=round_number, extra={"scores": scores})
        if round_number == max_rounds:
            break
        prompt = f"Task: {task}\nDraft: {draft}\nReview: {review}\nRewrite the draft."
        draft = model.complete([system(WRITER), user(prompt)]).text
    return Outcome(best_draft, "max_rounds", steps=max_rounds,
                   extra={"scores": scores, "best_score": best_score})


TASK = "Write a one-line slogan for a library that lends tools."


def example() -> tuple[Outcome, CallCounter]:
    """The first draft scores 5. The rewrite scores 9 and is accepted. Four calls."""
    fake = FakeModel([
        "Tools for everyone.",
        "SCORE: 5\nNOTES: Too vague. Say that people borrow tools.",
        "Borrow the drill. Keep the money.",
        "SCORE: 9\nNOTES: Clear and short.",
    ])
    counter = CallCounter(fake)
    return optimize(counter, TASK), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The critic never gives more than 6. The loop stops after 3 rounds with the best draft."""
    fake = FakeModel([
        "Tools for everyone.", "SCORE: 4\nNOTES: Vague.",
        "Borrow tools here.", "SCORE: 6\nNOTES: Better, still flat.",
        "Your street's shed.", "SCORE: 3\nNOTES: Confusing.",
    ])
    counter = CallCounter(fake)
    return optimize(counter, TASK), counter
