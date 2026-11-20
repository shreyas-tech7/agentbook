# Lesson 6. Orchestrator and workers

Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) calls this pattern orchestrator-workers. It looks like fan-out, with one big difference. Here a model decides the parts at run time.

## The problem

Some tasks cannot be split before you see them. "Rename this function" might touch two files or twenty. You cannot write the list of parts in advance. We want a model to make the list, and then hand each part to a worker.

## The idea

A lead call reads the task and returns a list of subtasks as JSON. Our code checks that list. Then each subtask goes to a worker call. A last call joins the workers' results into one answer.

## The code

<!-- quote: agentbook/patterns/orchestrator.py#L23-L34 -->
```python
def orchestrate(model: Model, task: str, max_workers: int = 4) -> Outcome:
    plan = parse_json(model.complete([system(LEAD), user(task)]).text)
    if not isinstance(plan, list) or not plan or not all(isinstance(p, str) for p in plan):
        return Outcome(None, "bad_plan", steps=1)
    if len(plan) > max_workers:
        return Outcome(None, "too_many_workers", steps=1, extra={"asked_for": len(plan)})
    parts = []
    for subtask in plan:
        prompt = f"Whole task: {task}\nYour part: {subtask}"
        parts.append(f"{subtask}: {model.complete([system(WORKER), user(prompt)]).text}")
    answer = model.complete([system(JOIN), user("\n".join(parts))]).text
    return Outcome(answer, "done", steps=len(plan) + 2, extra={"plan": plan, "parts": parts})
```

Read it line by line:

1. The lead call returns text. `parse_json` turns it into Python data.
2. The plan must be a non-empty list of strings. Anything else stops with `bad_plan`.
3. A plan longer than `max_workers` stops with `too_many_workers`.
4. Each subtask gets one worker call. The worker sees the whole task and its own part.
5. One join call turns the parts into the answer.

`parse_json` is in the tools helper. It also strips a code fence, because models often wrap JSON in one.

<!-- quote: agentbook/tools.py#L68-L77 -->
```python
def parse_json(text: str, default: Any = None) -> Any:
    """Read JSON from a model reply. Strip a code fence if there is one."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return default
```

## The example

The task is to rename `load_cfg` to `load_config`. The lead finds two files. Two workers change one file each. The join call reports both changes. That is four calls.

```bash
python -m agentbook orchestrator
```

## The failure case and its guard

The lead is a model, so its plan can be wild. In the failure case, it asks for forty workers.

<!-- quote: agentbook/patterns/orchestrator.py#L52-L56 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The lead asks for 40 workers. The guard stops the run after one call."""
    huge_plan = "[" + ", ".join(f'"check file {n}"' for n in range(40)) + "]"
    counter = CallCounter(FakeModel([huge_plan]))
    return orchestrate(counter, TASK), counter
```

Without a guard, our code would make forty worker calls and one join call. The guard checks the plan before any worker runs. Forty is more than `max_workers`, so the run stops after one call with `too_many_workers`. The outcome records how many workers the lead wanted. A second test feeds the lead prose, an object, an empty list and a list of numbers. Each one stops with `bad_plan`.

Check the plan in code before you pay for it. This is the main lesson of the pattern.

## When to use it

- The parts depend on the task, and you cannot list them in advance.
- Each part is small enough for one worker call.
- You can write a simple rule for a sane plan, such as a maximum size.

## When not to use it

- You know the parts in advance. Use fan-out (lesson 5). It saves the lead call.
- The parts need to talk to each other while they work.
- A wrong plan is costly and hard to check.

## Typical call count

Typical call count: example 4, failure case 1.

The rule is one lead call, plus one call per subtask, plus one join call.

## Exercises

Try the [exercises for this lesson](../../exercises/06-orchestrator.md) before you read the solutions.
