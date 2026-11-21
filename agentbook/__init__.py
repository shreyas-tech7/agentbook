"""agentbook: twelve agent patterns as small, plain, tested Python files."""

from agentbook.counter import CallCounter, estimate_tokens
from agentbook.model import FakeModel, Model, OpenAICompatModel, Reply, ToolCall, call, say

__all__ = ["CallCounter", "FakeModel", "Model", "OpenAICompatModel", "Reply", "ToolCall",
           "call", "estimate_tokens", "say"]
__version__ = "0.1.0rc1"
