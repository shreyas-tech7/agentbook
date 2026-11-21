# Lesson 1. Tool loop

This is the heart of every agent. Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) calls a model that uses tools in a loop an agent. This lesson builds that loop in about ten lines.

## The problem

A model can only write text. It cannot add numbers reliably, read a file or check the time. We want the model to ask our code for help, and then use the answer.

## The idea

The model gets a list of tools. Each tool has a name and a short description. The model can reply in one of two ways. It can write a plain answer. Or it can ask for a tool, with arguments. Our code runs the tool and puts the result in the conversation. Then we call the model again. We stop when the model writes a plain answer.

## The code

<!-- quote: agentbook/patterns/tool_loop.py#L29-L38 -->
```python
def tool_loop(model: Model, task: str, tools: dict[str, Tool], max_steps: int = 8) -> Outcome:
    messages = [system(SYSTEM), user(task)]
    for step in range(1, max_steps + 1):
        reply = model.complete(messages, specs(tools))
        messages.append(assistant(reply))
        if reply.tool_call is None:
            return Outcome(reply.text, "done", steps=step, trace=messages)
        result = run_tool(tools, reply.tool_call)
        messages.append(tool_result(reply.tool_call.name, result))
    return Outcome(None, "max_steps", steps=max_steps, trace=messages)
```

Read it line by line:

1. `messages` starts with the instructions and the task.
2. Each pass of the `for` loop is one model call.
3. `specs(tools)` tells the model which tools exist.
4. We save the reply in `messages`, so the model sees its own history next time.
5. No tool call means the model is done. We return its text.
6. A tool call means work for us. `run_tool` runs the function.
7. The result goes back into `messages` as a `tool` message.
8. The loop goes around again.

`run_tool` lives in the tools helper. It never crashes the loop. An unknown tool or an error comes back as text. The model can read that text and try something else.

<!-- quote: agentbook/tools.py#L58-L66 -->
```python
def run_tool(tools: dict[str, Tool], call: ToolCall) -> str:
    """Run one tool call. Errors come back as text, so the model can read them and recover."""
    tool = tools.get(call.name)
    if tool is None:
        return f"error: unknown tool {call.name!r}. Known tools: {', '.join(tools)}"
    try:
        return str(tool.fn(**call.args))
    except Exception as err:  # the model sees the error instead of the program crashing
        return f"error: {type(err).__name__}: {err}"
```

## The example

The task is "What is 19 + 23?". The scripted model first asks for `add` with 19 and 23. Our code returns "42". The model then answers "19 + 23 = 42". That is two model calls.

```bash
python -m agentbook tool_loop
```

## The failure case and its guard

A model can get stuck. It asks for the same tool again and again. It never writes an answer. Without a limit, the loop runs forever and the bill grows with every pass.

<!-- quote: agentbook/patterns/tool_loop.py#L56-L60 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """A stuck model asks for the same tool forever. The step limit stops it."""
    fake = FakeModel(respond=lambda messages: call("add", a="1", b="1"))
    counter = CallCounter(fake)
    return tool_loop(counter, "What is 1 + 1?", CALCULATOR, max_steps=5), counter
```

The guard is `max_steps`. The loop runs at most that many times. Then it returns with the stop reason `max_steps` and no answer. The test `test_failure_case_step_limit_stops_a_stuck_model` shows exactly five calls. A second test raises the limit to eleven and sees eleven calls. So the limit is what stops the run.

Always read the stop reason. An answer of `None` with `max_steps` is a failure, not a quiet success.

## When to use it

- The model must decide which tools to use, and in which order.
- You cannot know the number of steps before you start.
- The task needs fresh facts or real actions, such as a search or a calculation.

## When not to use it

- You already know the steps. Use a prompt chain (lesson 4). It is cheaper and easier to test.
- One model call can do the whole job.
- A wrong tool call could cause harm. Add human approval first (lesson 9).

## Typical call count

Typical call count: example 2, failure case 5.

The rule is one call for each tool use, plus one call for the answer. The step limit is the most you can pay.

## Exercises

Try the [exercises for this lesson](../../exercises/01-tool-loop.md) before you read the solutions.
