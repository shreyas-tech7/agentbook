# Lesson 9. Human approval

Some actions cannot be undone. A deleted file, a sent email or a payment stays done. Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) suggests checkpoints where a person can step in. This lesson builds one.

## The problem

A tool loop runs whatever tool the model asks for. Most tools are harmless, such as a list or a search. A few tools change the world. A model that misreads the task could delete the wrong file. We want a person to say yes before those tools run.

## The idea

Each tool has a `risky` flag. The loop works like the tool loop in lesson 1. When the model asks for a risky tool, the loop pauses. It asks an approver, which is a function. Only a true answer lets the tool run. No approver means no.

## The code

<!-- quote: agentbook/patterns/human_approval.py#L33-L47 -->
```python
def run_with_approval(model: Model, task: str, tools: dict[str, Tool],
                      approve: Approver | None = None, max_steps: int = 6) -> Outcome:
    messages = [system(SYSTEM), user(task)]
    for step in range(1, max_steps + 1):
        reply = model.complete(messages, specs(tools))
        messages.append(assistant(reply))
        if reply.tool_call is None:
            return Outcome(reply.text, "done", steps=step, trace=messages)
        tool = tools.get(reply.tool_call.name)
        if tool is not None and tool.risky:
            if approve is None or not approve(reply.tool_call):
                return Outcome(None, "denied", steps=step, trace=messages,
                               extra={"blocked_call": reply.tool_call})
        messages.append(tool_result(reply.tool_call.name, run_tool(tools, reply.tool_call)))
    return Outcome(None, "max_steps", steps=max_steps, trace=messages)
```

Read it line by line:

1. The loop starts like the tool loop, with instructions and the task.
2. A plain answer ends the run with `done`.
3. For a tool call, we look up the tool.
4. If the tool is risky, we ask the approver.
5. No approver, or a false answer, stops the run with `denied`. The tool never runs.
6. The outcome keeps the blocked call, so you can show it to the person.
7. A safe tool, or an approved risky tool, runs as usual.

In a real program, the approver can ask in the terminal. It needs the full word "yes".

<!-- quote: agentbook/patterns/human_approval.py#L50-L53 -->
```python
def ask_in_terminal(tool_call: ToolCall) -> bool:
    """A real approver for the command line. Tests use plain functions instead."""
    answer = input(f"Allow {tool_call.name} {tool_call.args}? Type yes to allow: ")
    return answer.strip().lower() == "yes"
```

## The example

The task is "Delete the log file." The model lists the files, then asks to delete `old.log`. The approver says yes. The file goes. The model confirms. That is three calls.

```bash
python -m agentbook human_approval
```

The example tools work on a Python dict, not on real files. Nothing on your disk changes.

## The failure case and its guard

In the failure case, the task is vague: "Clean up the folder." The model decides to delete `notes.txt`. The person wants to keep it.

<!-- quote: agentbook/patterns/human_approval.py#L79-L87 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The model wants to delete notes.txt. The person says no. The file stays."""
    files = {"old.log": "...", "notes.txt": "..."}
    fake = FakeModel([call("list_files"), call("delete_file", name="notes.txt")])
    counter = CallCounter(fake)
    result = run_with_approval(counter, "Clean up the folder.", file_tools(files),
                               approve=lambda c: False)
    result.extra["files_left"] = sorted(files)
    return result, counter
```

The guard is the approver. It says no. The run stops with `denied`, and `notes.txt` is still there. The test checks the files that are left, not only the stop reason. That proves the delete function never ran.

The guard also covers a missing approver. If you forget to pass one, every risky call is denied. A safe default matters more than a clever one.

## When to use it

- A tool deletes, sends, pays or changes something outside your program.
- A mistake would cost more than a short wait for a person.
- A person is around to answer.

## When not to use it

- Every tool is read-only. Then there is nothing to approve.
- Nobody can answer in time. Then make the agent draft the action and stop, instead of waiting.
- You ask for approval so often that people click yes without reading. That gives you no safety.

## Typical call count

Typical call count: example 3, failure case 2.

Approval adds no model calls. It adds human time. A denied action ends the run early, so it saves calls.

## Exercises

Try the [exercises for this lesson](../../exercises/09-human-approval.md) before you read the solutions.
