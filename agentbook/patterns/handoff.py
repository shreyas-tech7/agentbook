"""Pattern 10. Handoff.

Several agents share one model. Each agent has its own instructions.
An agent can call the `handoff` tool to pass the task, with a note, to another agent.
The new agent sees the whole conversation so far, plus the note.

Failure: two agents keep handing the task back and forth.
Guard: `max_handoffs` ends the run. A handoff to an agent that is not allowed also stops it.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model, call, say
from agentbook.tools import Outcome, system, user

HANDOFF_SPEC = {"name": "handoff", "description": "Pass the task to another agent.",
                "parameters": {"type": "object", "required": ["to", "note"], "properties": {
                    "to": {"type": "string"}, "note": {"type": "string"}}}}


@dataclass
class Agent:
    name: str
    instructions: str
    can_hand_to: tuple[str, ...] = ()


def run_handoffs(model: Model, agents: dict[str, Agent], start: str, task: str,
                 max_handoffs: int = 3) -> Outcome:
    current, path, shared = start, [start], [user(task)]
    for handoffs in range(max_handoffs + 1):
        agent = agents[current]
        hint = f" You may hand off to: {', '.join(agent.can_hand_to)}." if agent.can_hand_to else ""
        tools = [HANDOFF_SPEC] if agent.can_hand_to else None
        reply = model.complete([system(agent.instructions + hint)] + shared, tools)
        if reply.tool_call is None or reply.tool_call.name != "handoff":
            return Outcome(reply.text, "done", steps=handoffs + 1, extra={"path": path})
        if handoffs == max_handoffs:
            break
        target = reply.tool_call.args.get("to", "")
        if target not in agent.can_hand_to or target not in agents:
            return Outcome(None, "bad_target", steps=handoffs + 1,
                           extra={"path": path, "target": target})
        note = reply.tool_call.args.get("note", "")
        shared.append({"role": "assistant", "content": f"[{current} -> {target}] {note}"})
        current = target
        path.append(target)
    return Outcome(None, "max_handoffs", steps=max_handoffs + 1, extra={"path": path})


DESK = {
    "triage": Agent("triage", "You greet the customer and find the right team.",
                    ("refunds", "shipping")),
    "refunds": Agent("refunds", "You handle refunds only.", ("shipping",)),
    "shipping": Agent("shipping", "You handle delivery problems only.", ("refunds",)),
}


def example() -> tuple[Outcome, CallCounter]:
    """Triage hands off to refunds once. Refunds answers. Two calls."""
    fake = FakeModel([
        call("handoff", to="refunds", note="Order 1182 arrived broken. Customer wants money back."),
        say("I refunded order 1182. The money arrives in 3 to 5 days."),
    ])
    counter = CallCounter(fake)
    return run_handoffs(counter, DESK, "triage", "My order 1182 came broken."), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """Refunds and shipping pass the task back and forth. The guard stops after 3 handoffs."""
    def ping_pong(messages):
        me = "refunds" if "refunds only" in messages[0]["content"] else "shipping"
        other = "shipping" if me == "refunds" else "refunds"
        return call("handoff", to=other, note=f"Not a {me} problem.")
    counter = CallCounter(FakeModel(respond=ping_pong))
    return run_handoffs(counter, DESK, "refunds", "My parcel came late and broken."), counter
