# Lesson 5. Fan-out and fan-in

Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) calls this pattern parallelization. We split work into independent parts and run them at the same time. Then we join the results.

## The problem

Some jobs have parts that do not depend on each other. A review can check grammar, clarity and tone. Doing them one after another wastes time. One prompt that does all three often forgets one of them.

## The idea

You list the parts before the run starts. Each part becomes one model call in its own thread. That is the fan-out. When all parts finish, one more call merges them. That is the fan-in.

## The code

<!-- quote: agentbook/patterns/fan_out.py#L22-L41 -->
```python
def fan_out(model: Model, text: str, angles: list[str], max_parallel: int = 4,
            timeout: float = 30.0) -> Outcome:
    def work(angle: str) -> str:
        return model.complete([system(f"Review the text for {angle} only."), user(text)]).text

    pool = ThreadPoolExecutor(max_workers=max_parallel)
    futures = [pool.submit(work, angle) for angle in angles]
    parts, missing = [], []
    for angle, future in zip(angles, futures, strict=True):
        try:
            parts.append(f"{angle}: {future.result(timeout=timeout)}")
        except Exception as err:  # a crash or a timeout
            missing.append(angle)
            parts.append(f"{angle}: MISSING ({type(err).__name__})")
    pool.shutdown(wait=False, cancel_futures=True)  # do not wait for a hung worker
    if len(missing) == len(angles):
        return Outcome(None, "all_failed", extra={"missing": missing})
    merged = model.complete([system(MERGE), user("\n".join(parts))]).text
    stop = "partial" if missing else "done"
    return Outcome(merged, stop, steps=len(angles) + 1, extra={"parts": parts, "missing": missing})
```

Read it line by line:

1. `work` makes one review call for one angle.
2. The thread pool starts one job for each angle. The jobs run side by side.
3. We collect the results in the order of `angles`, so the output is stable.
4. Each result waits at most `timeout` seconds.
5. A crash or a timeout becomes a line that says `MISSING`.
6. We shut the pool down without waiting. A hung worker cannot block us.
7. If every worker failed, we skip the merge and stop with `all_failed`.
8. Otherwise one call merges the parts. One or more missing parts give `partial`.

Python's `ThreadPoolExecutor` comes with the standard library. Model calls spend most of their time waiting on the network, so threads are enough.

## The example

The text has three problems: a grammar slip, a vague subject and a filler word. Three workers each review one angle. The merge call joins their notes. That is four calls.

```bash
python -m agentbook fan_out
```

## The failure case and its guard

In the failure case, the tone worker loses its connection and raises an error.

<!-- quote: agentbook/patterns/fan_out.py#L70-L73 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The tone worker crashes. The merge still runs and reports the gap."""
    counter = CallCounter(FakeModel(respond=reviewer(broken="tone")))
    return fan_out(counter, TEXT, ANGLES), counter
```

Without a guard, one error would crash the whole run. A hung worker would make the merge wait forever. The guard catches each failure and writes `tone: MISSING (ConnectionError)`. The merge still runs and can say that one review is missing. The stop reason `partial` tells your code that the answer is not complete.

A test also makes one worker hang for a second, with a timeout of 0.1 seconds. The run ends quickly and lists that worker as missing.

## When to use it

- The parts are independent. No part needs another part's output.
- You know the parts before you start.
- Speed matters, or you want each part to get full attention.

## When not to use it

- The parts depend on each other. Use a prompt chain (lesson 4).
- You cannot list the parts in advance. Use orchestrator and workers (lesson 6).
- Your provider has a tight rate limit. Parallel calls hit it sooner.

## Typical call count

Typical call count: example 4, failure case 3.

The rule is one call for each part, plus one call to merge. The failed part costs nothing in our count, because its call never returned.

## Exercises

Try the [exercises for this lesson](../../exercises/05-fan-out.md) before you read the solutions.
