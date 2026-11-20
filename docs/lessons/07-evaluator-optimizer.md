# Lesson 7. Evaluator and optimizer

Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) calls this pattern evaluator-optimizer. One call writes. Another call judges. The writer tries again with the notes.

## The problem

A first draft is often weak. A person improves a draft by reading it, noting problems and rewriting it. We want the model to do the same. We also want the loop to end.

## The idea

The writer makes a draft. The critic gives a score from 0 to 10 and some notes. A score at or above the threshold ends the loop. A lower score sends the draft and the notes back to the writer. A round limit stops the loop if the critic is never happy.

## The code

Our code reads the score from the critic's reply.

<!-- quote: agentbook/patterns/evaluator_optimizer.py#L23-L25 -->
```python
def read_score(review: str) -> int:
    match = re.search(r"SCORE:\s*(\d+)", review)
    return min(int(match.group(1)), 10) if match else 0
```

The loop writes, scores and rewrites.

<!-- quote: agentbook/patterns/evaluator_optimizer.py#L28-L44 -->
```python
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
```

Read it line by line:

1. The first call writes a draft.
2. Each round makes one critic call and reads the score.
3. We remember the best draft so far, and its score.
4. A score at or above `threshold` returns the draft with `accepted`.
5. In the last round, we skip the rewrite. Nobody would score it.
6. Otherwise the writer gets the draft, the review and a request to rewrite.
7. After the last round, we return the best draft with `max_rounds`.

`read_score` caps the score at 10. A reply with no score line counts as 0. So a broken critic can never accept a draft.

## The example

The task is a slogan for a library that lends tools. The first draft is "Tools for everyone." It scores 5. The rewrite is "Borrow the drill. Keep the money." It scores 9 and is accepted. That is four calls.

```bash
python -m agentbook evaluator_optimizer
```

## The failure case and its guard

In the failure case, the critic never gives more than 6. The threshold is 8.

<!-- quote: agentbook/patterns/evaluator_optimizer.py#L62-L70 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The critic never gives more than 6. The loop stops after 3 rounds with the best draft."""
    fake = FakeModel([
        "Tools for everyone.", "SCORE: 4\nNOTES: Vague.",
        "Borrow tools here.", "SCORE: 6\nNOTES: Better, still flat.",
        "Your street's shed.", "SCORE: 3\nNOTES: Confusing.",
    ])
    counter = CallCounter(fake)
    return optimize(counter, TASK), counter
```

Without a guard, the loop would rewrite forever. The guard is `max_rounds`. After three rounds the loop stops with `max_rounds`. It returns the best draft, "Borrow tools here.", with its score of 6. Note that the last draft scored only 3. Returning the best draft, not the last one, protects you from a rewrite that made things worse.

## When to use it

- You can say clearly what a good result looks like.
- A critic can find real problems that a rewrite can fix.
- A better answer is worth two or more extra calls per round.

## When not to use it

- Code can check the result. Use a gate in a prompt chain (lesson 4). It is cheaper and exact.
- The critic is as weak as the writer. Then the scores mean little.
- The first draft is usually good enough.

## Typical call count

Typical call count: example 4, failure case 6.

The rule is one call for the first draft. Then each round costs one review and one rewrite. The last round has a review only. So the most you pay is `2 * max_rounds` calls.

## Exercises

Try the [exercises for this lesson](../../exercises/07-evaluator-optimizer.md) before you read the solutions.
