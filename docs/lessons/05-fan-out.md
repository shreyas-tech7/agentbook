# Lesson 5. Fan-out and fan-in

Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) calls this pattern parallelization. We split work into independent parts and run them at the same time. Then we join the results.

## The problem

Some jobs have parts that do not depend on each other. A review can check grammar, clarity and tone. Doing them one after another wastes time. One prompt that does all three often forgets one of them.

## The idea

You list the parts before the run starts. Each part becomes one model call in its own thread. That is the fan-out. When all parts finish, one more call merges them. That is the fan-in.

## The code

<!-- quote: agentbook/patterns/fan_out.py#L22-L44 -->
```python
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
```

Read it line by line:

1. `work` makes one review call for one angle.
2. The thread pool starts one job for each angle. The jobs run side by side.
3. `wait` gives all the workers one shared deadline of `timeout` seconds. Three hung workers still cost one timeout, not three.
4. We shut the pool down without waiting, so the merge does not wait for a hung worker.
5. We read the results in the order of `angles`, so the output is stable.
6. A crash, or a worker that is not done by the deadline, becomes a line that says `MISSING`.
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

<!-- quote: agentbook/patterns/fan_out.py#L73-L76 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The tone worker crashes. The merge still runs and reports the gap."""
    counter = CallCounter(FakeModel(respond=reviewer(broken="tone")))
    return fan_out(counter, TEXT, ANGLES), counter
```

Without a guard, one error would crash the whole run. A hung worker would make the merge wait forever. The guard catches each failure and writes `tone: MISSING (ConnectionError)`. The merge still runs and can say that one review is missing. The stop reason `partial` tells your code that the answer is not complete.

A test also makes one worker hang for a second, with a timeout of 0.1 seconds. The run ends quickly and lists that worker as missing. Another test hangs all three workers and checks that the run still takes about one timeout. One limit stays. Python cannot kill a thread, so a hung worker keeps running in the background. It can delay the end of the program until it finishes.

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

The rule is one call for each part, plus one call to merge. A crashed call costs nothing in our count. A call that timed out may still finish later, and a real provider still bills it.

## Exercises

Try the [exercises for this lesson](../../exercises/05-fan-out.md) before you read the solutions.
