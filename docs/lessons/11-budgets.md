# Lesson 11. Budgets and stop rules

Every earlier lesson had one limit, such as `max_steps` or `max_rounds`. Real agents need several limits at once. Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) advises stop conditions, such as a maximum number of steps. This lesson puts steps, tokens and time in one place.

## The problem

An agent can fail in quiet ways. It can take a thousand steps. It can make ten calls that each send a huge history. It can wait on a slow tool for an hour. A step limit alone catches only the first. We want every limit checked, and a clear reason when one is hit.

## The idea

A budget holds three limits: steps, tokens and seconds. Before every model call, our code checks all three. The first limit that is used up ends the run. The stop reason names that limit. The token count comes from the call counter.

## The code

A budget is a frozen record, so nobody changes it in the middle of a run.

<!-- quote: agentbook/patterns/budgets.py#L34-L37 -->
```python
class Budget:
    max_steps: int = 10
    max_tokens: int = 2_000
    max_seconds: float = 60.0
```

One small function checks the limits in a fixed order.

<!-- quote: agentbook/patterns/budgets.py#L40-L48 -->
```python
def over_budget(budget: Budget, steps: int, tokens: int, seconds: float) -> str | None:
    """Return the name of the first limit that is used up, or None."""
    if steps >= budget.max_steps:
        return "max_steps"
    if tokens >= budget.max_tokens:
        return "max_tokens"
    if seconds >= budget.max_seconds:
        return "max_seconds"
    return None
```

The loop checks the budget before each call.

<!-- quote: agentbook/patterns/budgets.py#L51-L65 -->
```python
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
```

Read it line by line:

1. We wrap the model in a counter, unless it already is one.
2. `clock` gives the time. Tests pass a fake clock.
3. Before each call, `over_budget` checks steps, tokens and time.
4. A used-up limit returns at once, with its name as the stop reason.
5. The outcome carries the counter's summary, so you see what the run cost.
6. The rest is the tool loop from lesson 1.

## The example

The question is "When does the shop open?". The model reads one note, then answers. Two calls stay well inside every limit.

```bash
python -m agentbook budgets
```

## The failure case and its guard

In the failure case, the model reads note after note and never answers. Each note adds about 120 tokens to the history. Each call sends the whole history again.

<!-- quote: agentbook/patterns/budgets.py#L80-L85 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The model reads note after note and never answers. The token budget stops it."""
    reads = iter(range(1, 100))
    counter = CallCounter(FakeModel(respond=lambda m: call("read_note", id=str(next(reads)))))
    budget = Budget(max_steps=50, max_tokens=1_500, max_seconds=30)
    return run_with_budget(counter, "When does the shop open?", NOTES, budget), counter
```

The step limit is 50, so it would not help soon. The token limit is 1,500. After five calls the counter passes 1,500 tokens. The run stops with `max_tokens`. Note how fast tokens grow. The fifth call alone costs more than the first two together.

A second test uses a fake clock. Each call moves the clock 10 seconds ahead. The time limit is 25 seconds, so the run stops after three calls with `max_seconds`. The test takes no real time.

## When to use it

- Always, in any loop where the model decides when to stop.
- When you pay per token, set a token budget, not only a step budget.
- When a person waits for the answer, set a time budget.

## When not to use it

- A fixed chain with a known number of calls does not need a step budget. A token budget can still help.
- Do not set limits so tight that normal tasks fail. Measure normal runs first with the counter.

## Typical call count

Typical call count: example 2, failure case 5.

The budget sets the most you can pay. The counter tells you what you did pay.

## Exercises

Try the [exercises for this lesson](../../exercises/11-budgets.md) before you read the solutions.
