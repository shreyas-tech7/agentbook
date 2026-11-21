"""Pattern 9. Human approval.

Some tools change the world: they delete, send or pay. We mark those tools as risky.
Before a risky tool runs, the agent pauses and asks a person. Only a yes lets it run.

Failure: the model asks for a risky action that the person did not want.
Guard: a "no" stops the run before the tool runs. With no approver at all,
the answer is always no.
"""

from __future__ import annotations

from collections.abc import Callable

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model, ToolCall, call, say
from agentbook.tools import (
    Outcome,
    Tool,
    assistant,
    run_tool,
    specs,
    system,
    tool_result,
    toolbox,
    user,
)

Approver = Callable[[ToolCall], bool]
SYSTEM = "You manage files with tools. Answer in plain text when you are done."


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


def ask_in_terminal(tool_call: ToolCall) -> bool:
    """A real approver for the command line. Tests use plain functions instead."""
    answer = input(f"Allow {tool_call.name} {tool_call.args}? Type yes to allow: ")
    return answer.strip().lower() == "yes"


def file_tools(files: dict[str, str]) -> dict[str, Tool]:
    """Tools over a dict that stands in for a folder, so nothing real is deleted."""
    def delete(name: str) -> str:
        files.pop(name)
        return f"deleted {name}"
    return toolbox(
        Tool("list_files", "List the files.", lambda: ", ".join(sorted(files))),
        Tool("delete_file", "Delete one file.", delete, {"name": "file name"}, risky=True),
    )


def example() -> tuple[Outcome, CallCounter]:
    """The person says yes, so old.log is deleted. Three calls."""
    files = {"old.log": "...", "notes.txt": "..."}
    fake = FakeModel([call("list_files"), call("delete_file", name="old.log"),
                      say("I deleted old.log.")])
    counter = CallCounter(fake)
    result = run_with_approval(counter, "Delete the log file.", file_tools(files),
                               approve=lambda c: c.args.get("name") == "old.log")
    result.extra["files_left"] = sorted(files)
    return result, counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The model wants to delete notes.txt. The person says no. The file stays."""
    files = {"old.log": "...", "notes.txt": "..."}
    fake = FakeModel([call("list_files"), call("delete_file", name="notes.txt")])
    counter = CallCounter(fake)
    result = run_with_approval(counter, "Clean up the folder.", file_tools(files),
                               approve=lambda c: False)
    result.extra["files_left"] = sorted(files)
    return result, counter
