# Lesson 4. Prompt chain with gates

Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) calls this pattern prompt chaining. It is often the best first choice, because it is easy to test.

## The problem

One big prompt that does five things at once is hard to get right. When it fails, you cannot tell which part failed. We want small steps, each easy to check.

## The idea

You write the steps yourself, in a fixed order. Each step is one model call. Its output becomes the input of the next step. Between steps, a gate checks the output. A gate is a small function that returns true or false. A false gate stops the chain.

## The code

A step has a name, a prompt template and an optional gate.

<!-- quote: agentbook/patterns/prompt_chain.py#L21-L24 -->
```python
class Step:
    name: str
    prompt: str  # a template with {input}
    gate: Callable[[str], bool] | None = None
```

The chain runs the steps in order.

<!-- quote: agentbook/patterns/prompt_chain.py#L27-L36 -->
```python
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
```

Read it line by line:

1. `current` starts as the input text.
2. Each step fills `{input}` in its prompt with `current`.
3. The reply becomes the new `current`.
4. We keep every output by step name, so you can see the whole chain later.
5. A failed gate returns at once with `gate_failed` and the name of the step.
6. If every gate passes, the last output is the answer.

The gates in the example are plain code.

<!-- quote: agentbook/patterns/prompt_chain.py#L39-L40 -->
```python
def max_words(limit: int) -> Callable[[str], bool]:
    return lambda text: 0 < len(text.split()) <= limit
```

## The example

A meeting note goes in. Step 1 writes a summary of at most 25 words. Step 2 writes a title of at most 6 words with no final dot. Both gates pass. That is two calls.

```bash
python -m agentbook prompt_chain
```

## The failure case and its guard

In the failure case, the summary has 48 words. It breaks the rule of step 1.

<!-- quote: agentbook/patterns/prompt_chain.py#L61-L66 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The summary is far too long. The first gate fails, so the title step never runs."""
    long_summary = " ".join(["The meeting covered many details about the launch."] * 6)
    fake = FakeModel([long_summary, "This title is never requested"])
    counter = CallCounter(fake)
    return run_chain(counter, NOTE, SUMMARY_THEN_TITLE), counter
```

The guard is the gate after step 1. It sees 48 words and stops the chain. The stop reason is `gate_failed`, and `failed_gate` is `summary`. The title step never runs. So a bad summary never turns into a bad title.

Without the gate, the chain would carry the error forward. Each later step would look fine on its own, and the final answer would still be wrong.

## When to use it

- You know the steps before you start.
- Each step has an output you can check with code.
- You want the cheapest and most predictable pattern.

A plain chain often beats an agent loop. It makes a fixed number of calls. Every test can check each step. Nothing decides to run forever.

## When not to use it

- The steps depend on what the model finds along the way. Use the tool loop (lesson 1).
- The steps do not depend on each other. Run them side by side with fan-out (lesson 5).

## Typical call count

Typical call count: example 2, failure case 1.

The rule is one call for each step that runs. A failed gate saves the calls of every later step.

## Exercises

Try the [exercises for this lesson](../../exercises/04-prompt-chain.md) before you read the solutions.
