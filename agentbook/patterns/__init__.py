"""The twelve patterns, in reading order. Each name maps to its module."""

from importlib import import_module
from types import ModuleType

ORDER = [
    ("tool_loop", "Tool loop"),
    ("plan_execute", "Plan and execute"),
    ("router", "Router"),
    ("prompt_chain", "Prompt chain with gates"),
    ("fan_out", "Fan-out and fan-in"),
    ("orchestrator", "Orchestrator and workers"),
    ("evaluator_optimizer", "Evaluator and optimizer"),
    ("memory", "Memory"),
    ("human_approval", "Human approval"),
    ("handoff", "Handoff"),
    ("budgets", "Budgets and stop rules"),
    ("retrieval", "Retrieval as a tool"),
]


def load(name: str) -> ModuleType:
    return import_module(f"agentbook.patterns.{name}")
