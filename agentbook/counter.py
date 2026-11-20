"""A call counter. It wraps any model and counts calls and estimated tokens.

The token count is an estimate: about four characters per token.
It is good enough to compare patterns. It is not a bill.
"""

from __future__ import annotations

import json
import threading

from agentbook.model import Message, Model, Reply


def estimate_tokens(text: str) -> int:
    """About four characters per token. Empty text costs nothing."""
    return (len(text) + 3) // 4 if text else 0


class CallCounter:
    """Wrap a model. Every call goes through here and gets counted."""

    def __init__(self, model: Model):
        self.model = model
        self.calls = 0
        self.tokens_in = 0
        self.tokens_out = 0
        self._lock = threading.Lock()

    def complete(self, messages: list[Message], tools: list[dict] | None = None) -> Reply:
        cost_in = sum(estimate_tokens(m.get("content", "")) for m in messages)
        if tools:
            cost_in += estimate_tokens(json.dumps(tools))
        reply = self.model.complete(messages, tools)
        cost_out = estimate_tokens(reply.text)
        if reply.tool_call:
            cost_out += estimate_tokens(reply.tool_call.name + json.dumps(reply.tool_call.args))
        with self._lock:
            self.calls += 1
            self.tokens_in += cost_in
            self.tokens_out += cost_out
        return reply

    @property
    def tokens(self) -> int:
        return self.tokens_in + self.tokens_out

    def summary(self) -> dict[str, int]:
        return {"calls": self.calls, "tokens_in": self.tokens_in,
                "tokens_out": self.tokens_out, "tokens": self.tokens}
