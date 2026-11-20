"""Small helpers that every pattern shares: messages, tools and the Outcome record."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agentbook.model import Message, Reply, ToolCall


def system(text: str) -> Message:
    return {"role": "system", "content": text}


def user(text: str) -> Message:
    return {"role": "user", "content": text}


def assistant(reply: Reply) -> Message:
    """Store a reply in the history. A tool call is stored as readable text."""
    if reply.tool_call:
        args = json.dumps(reply.tool_call.args, sort_keys=True)
        return {"role": "assistant", "content": f"CALL {reply.tool_call.name} {args}"}
    return {"role": "assistant", "content": reply.text}


def tool_result(name: str, text: str) -> Message:
    return {"role": "tool", "name": name, "content": text}


@dataclass
class Tool:
    """A function the model may ask for. `params` maps each argument name to a description."""

    name: str
    description: str
    fn: Callable[..., Any]
    params: dict[str, str] = field(default_factory=dict)
    risky: bool = False

    def spec(self) -> dict:
        props = {k: {"type": "string", "description": v} for k, v in self.params.items()}
        return {"name": self.name, "description": self.description,
                "parameters": {"type": "object", "properties": props, "required": list(props)}}


def toolbox(*tools: Tool) -> dict[str, Tool]:
    return {t.name: t for t in tools}


def specs(tools: dict[str, Tool]) -> list[dict]:
    return [t.spec() for t in tools.values()]


def run_tool(tools: dict[str, Tool], call: ToolCall) -> str:
    """Run one tool call. Errors come back as text, so the model can read them and recover."""
    tool = tools.get(call.name)
    if tool is None:
        return f"error: unknown tool {call.name!r}. Known tools: {', '.join(tools)}"
    try:
        return str(tool.fn(**call.args))
    except Exception as err:  # the model sees the error instead of the program crashing
        return f"error: {type(err).__name__}: {err}"


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


@dataclass
class Outcome:
    """What every pattern returns. `stop` always says why the run ended."""

    answer: Any
    stop: str
    steps: int = 0
    trace: list[Message] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
