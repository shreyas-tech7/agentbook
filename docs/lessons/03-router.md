# Lesson 3. Router

Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) calls this pattern routing. One small decision sends each request to the right place.

## The problem

Different requests need different handling. A billing question needs billing rules. A technical problem needs step-by-step help. One giant prompt that covers every case gets long and confused. We want each case to have its own short prompt.

## The idea

One cheap call reads the request and picks a label from a fixed list. Our code looks up the handler for that label. The handler does the real work. A handler can call the model with its own instructions. It can also be plain code with no model call.

## The code

<!-- quote: agentbook/patterns/router.py#L21-L33 -->
```python
def route(model: Model, request: str, handlers: dict[str, Handler],
          default: str = "general") -> Outcome:
    if default not in handlers:
        raise ValueError(f"default handler {default!r} is missing")
    labels = ", ".join(handlers)
    prompt = f"Pick the best label for the request. Reply with one word from: {labels}."
    label = model.complete([system(prompt), user(request)]).text.strip().lower().rstrip(".")
    if label in handlers:
        chosen, stop = label, "done"
    else:
        chosen, stop = default, "fallback"
    return Outcome(handlers[chosen](request), stop, steps=1,
                   extra={"label": label, "route": chosen})
```

Read it line by line:

1. The default handler must exist. Otherwise the router refuses to start.
2. The prompt lists every label and asks for one word.
3. Our code cleans the reply. It strips spaces, lowers the case and drops a final dot.
4. A known label picks its handler. The stop reason is `done`.
5. Anything else goes to the default handler. The stop reason is `fallback`.
6. The outcome records the raw label and the route it took.

Handlers are plain functions. This helper makes a handler that calls the model.

<!-- quote: agentbook/patterns/router.py#L36-L38 -->
```python
def answer_with(model: Model, instructions: str) -> Handler:
    """Make a handler that answers with the model under its own instructions."""
    return lambda request: model.complete([system(instructions), user(request)]).text
```

## The example

The request is "Why was I charged twice this month?". The routing call returns `billing`. The billing handler makes the second call and answers. That is two calls in total.

```bash
python -m agentbook router
```

## The failure case and its guard

Models do not always follow the format. In the failure case, the model rambles. It says "Hmm, this could be billing or maybe technical, hard to say!" That is not a label.

<!-- quote: agentbook/patterns/router.py#L57-L62 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The model rambles instead of giving a label. The default handler takes over."""
    fake = FakeModel(["Hmm, this could be billing or maybe technical, hard to say!"])
    counter = CallCounter(fake)
    result = route(counter, "Something is wrong with my account.", support_desk(counter))
    return result, counter
```

The guard is the default handler. Our code does not guess. An unknown label goes to `general`, and the stop reason says `fallback`. You can count fallbacks in your logs. Many fallbacks mean the routing prompt needs work.

The guard has a cost. A request that really was about billing gets the general answer. That is safer than a wrong guess, but it is still a miss.

## When to use it

- Requests fall into a few clear groups.
- Each group needs different instructions, tools or models.
- You want a cheap model for the decision and a stronger one for some answers.

## When not to use it

- Every request needs the same handling.
- The groups overlap so much that a label is often wrong.
- One request needs several handlers at once. Use fan-out (lesson 5).

## Typical call count

Typical call count: example 2, failure case 1.

The rule is one call to route, plus whatever the chosen handler costs. The general handler here costs nothing.

## Exercises

Try the [exercises for this lesson](../../exercises/03-router.md) before you read the solutions.
