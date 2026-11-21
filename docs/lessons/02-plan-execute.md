# Lesson 2. Plan and execute

The tool loop decides one step at a time. Sometimes it is better to think first. This pattern writes the whole plan, then runs it step by step. The idea is close to the planning agents that Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) describes.

## The problem

A long task has many steps. If one early step goes wrong, every later step builds on the mistake. We want to see the plan before we spend money on it. We also want to catch a bad step at once.

## The idea

The first call asks for a numbered plan. Our code reads the numbered lines. Then each step gets its own call. After each call, a check in plain code looks at the output. A failed check stops the run.

## The code

First, our code turns the plan text into a list of steps.

<!-- quote: agentbook/patterns/plan_execute.py#L24-L31 -->
```python
def parse_plan(text: str) -> list[str]:
    """Keep the lines that start with a number, such as '1. Pack shirts'."""
    steps = []
    for line in text.splitlines():
        match = re.match(r"\s*\d+[.)]\s*(.+)", line)
        if match:
            steps.append(match.group(1).strip())
    return steps
```

Then the main function plans, runs and checks.

<!-- quote: agentbook/patterns/plan_execute.py#L34-L50 -->
```python
def plan_and_execute(model: Model, goal: str, check: Callable[[str, str], bool],
                     max_plan: int = 6) -> Outcome:
    plan = parse_plan(model.complete([system(PLANNER), user(goal)]).text)
    if not plan:
        return Outcome(None, "empty_plan")
    if len(plan) > max_plan:
        return Outcome(None, "plan_too_long", extra={"plan": plan})
    results: list[str] = []
    for number, step in enumerate(plan, 1):
        done = "\n".join(f"- {r}" for r in results) or "(nothing yet)"
        prompt = f"Goal: {goal}\nDone so far:\n{done}\nYour step: {step}"
        output = model.complete([system(EXECUTOR), user(prompt)]).text
        if not check(step, output):
            return Outcome(results, "check_failed", steps=number,
                           extra={"plan": plan, "failed_step": step, "bad_output": output})
        results.append(output)
    return Outcome(results, "done", steps=len(plan), extra={"plan": plan})
```

Read it line by line:

1. One call writes the plan. `parse_plan` keeps only numbered lines.
2. An empty plan stops the run with `empty_plan`.
3. A plan longer than `max_plan` stops the run with `plan_too_long`.
4. Each step gets one call. The prompt shows the goal, the work so far and this step.
5. `check` is your own function. It gets the step and its output.
6. A failed check returns at once. The results so far come back with it.
7. If every step passes, the stop reason is `done`.

## The example

The goal is "Pack for a two-day trip". The plan has three steps: clothes, toiletries and documents. Each step returns a short list. The check wants text under 120 characters. All three pass. That is four calls: one plan and three steps.

```bash
python -m agentbook plan_execute
```

## The failure case and its guard

In the failure case, step 2 returns an empty string. Step 3 would build on nothing.

<!-- quote: agentbook/patterns/plan_execute.py#L69-L73 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """Step 2 returns nothing. The check stops the run before step 3 is called."""
    fake = FakeModel([PLAN, "2 shirts, 1 pair of jeans, socks", "", "ID card, train ticket"])
    counter = CallCounter(fake)
    return plan_and_execute(counter, "Pack for a two-day trip", short_and_not_empty), counter
```

The guard is `check`. It sees the empty output and stops the run at step 2. The stop reason is `check_failed`. The outcome names the failed step. Step 3 never runs, so we pay for three calls, not four. The second guard, `max_plan`, stops a plan with twenty steps after one call.

A check is plain code, not another model call. It costs nothing and it never gets tired.

## When to use it

- The task has several steps, and you want to see them up front.
- You can check each step's output with simple code.
- A bad early step would waste the rest of the run.

## When not to use it

- The next step depends on what you just learned. Use the tool loop (lesson 1).
- The steps never change. Write them down yourself and use a prompt chain (lesson 4).
- You cannot write a useful check. Then the plan gives you little safety.

## Typical call count

Typical call count: example 4, failure case 3.

The rule is one call for the plan, plus one call for each step that runs.

## Exercises

Try the [exercises for this lesson](../../exercises/02-plan-execute.md) before you read the solutions.
