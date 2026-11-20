"""The Model interface, a scripted FakeModel and an adapter for OpenAI-compatible APIs.

The interface is tiny on purpose. Messages go in. A Reply comes out.
A Reply holds either text or one tool call.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

Message = dict[str, Any]  # {"role": "system" | "user" | "assistant" | "tool", "content": str}


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Reply:
    text: str = ""
    tool_call: ToolCall | None = None


def say(text: str) -> Reply:
    """A reply with plain text."""
    return Reply(text=text)


def call(tool: str, /, **args: Any) -> Reply:
    """A reply that asks for a tool. `tool` is positional, so a tool may take a `name` argument."""
    return Reply(tool_call=ToolCall(tool, args))


class Model(Protocol):
    def complete(self, messages: list[Message], tools: list[dict] | None = None) -> Reply: ...


class ScriptExhausted(RuntimeError):
    """The FakeModel has no replies left. A test asked for more calls than it planned."""


class FakeModel:
    """A model that replays a script. Every test uses it, so every test runs offline.

    Give it a list of replies (str or Reply), used in order.
    Or give it a function that looks at the messages and returns a reply.
    """

    def __init__(
        self,
        script: list[str | Reply] | None = None,
        respond: Callable[[list[Message]], str | Reply] | None = None,
    ):
        self.script = list(script or [])
        self.respond = respond
        self.seen: list[list[Message]] = []
        self._lock = threading.Lock()

    def complete(self, messages: list[Message], tools: list[dict] | None = None) -> Reply:
        with self._lock:
            self.seen.append([dict(m) for m in messages])
            if self.respond is None:
                if not self.script:
                    raise ScriptExhausted(f"no reply left for call {len(self.seen)}")
                out = self.script.pop(0)
        if self.respond is not None:
            out = self.respond(messages)  # outside the lock, so slow fakes can run in parallel
        return Reply(text=out) if isinstance(out, str) else out


def to_wire(message: Message) -> dict[str, str]:
    """Turn one of our messages into a plain chat message any endpoint accepts.

    Tool results travel as user messages. This avoids tool_call_id bookkeeping.
    """
    role, content = message["role"], message.get("content", "")
    if role == "tool":
        return {"role": "user", "content": f"Tool result from {message.get('name', '?')}: {content}"}
    return {"role": role, "content": content}


def parse_reply(data: dict) -> Reply:
    """Read the first choice of an OpenAI-style chat response."""
    msg = data["choices"][0]["message"]
    calls = msg.get("tool_calls") or []
    if calls:
        fn = calls[0]["function"]
        args = fn.get("arguments") or "{}"
        return Reply(tool_call=ToolCall(fn["name"], json.loads(args) if isinstance(args, str) else args))
    return Reply(text=msg.get("content") or "")


class OpenAICompatModel:
    """Record mode only. Calls any OpenAI-compatible /chat/completions endpoint.

    It uses the standard library. It reads the key from an environment variable.
    """

    def __init__(self, base_url: str, model: str, key_env: str = "AGENTBOOK_API_KEY",
                 timeout: float = 60, tries: int = 5, sleep: Callable[[float], None] = time.sleep):
        self.base_url, self.model, self.key_env = base_url.rstrip("/"), model, key_env
        self.timeout, self.tries, self.sleep = timeout, tries, sleep

    def complete(self, messages: list[Message], tools: list[dict] | None = None) -> Reply:
        body: dict[str, Any] = {"model": self.model, "messages": [to_wire(m) for m in messages]}
        if tools:
            body["tools"] = [{"type": "function", "function": t} for t in tools]
        headers = {"Content-Type": "application/json"}
        key = os.environ.get(self.key_env)
        if key:
            headers["Authorization"] = f"Bearer {key}"
        req = urllib.request.Request(f"{self.base_url}/chat/completions",
                                     data=json.dumps(body).encode(), headers=headers)
        wait = 2.0
        for attempt in range(self.tries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                    return parse_reply(json.load(resp))
            except urllib.error.HTTPError as err:
                if err.code != 429 or attempt == self.tries - 1:
                    raise
                self.sleep(wait)
                wait *= 2
        raise RuntimeError("unreachable")
