# Lesson 10. Handoff

A router picks a handler once, at the start. A handoff lets an agent change its mind in the middle. One agent passes the task, with a note, to another agent. This idea is not one of the named workflows in Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents). It builds on routing and tool use from that post.

## The problem

A help desk has teams for refunds and for shipping. The first agent cannot always tell which team a request needs. Sometimes the right team only becomes clear after a question or two. We want an agent to pass the task on, and the next agent to know what happened so far.

## The idea

Each agent has a name, its own instructions and a list of agents it may hand off to. An agent that may hand off gets one tool, `handoff`, with a target and a note. Our code switches to the target agent. The shared conversation carries over, plus a line with the note. An agent that answers in plain text ends the run.

## The code

An agent is a small record.

<!-- quote: agentbook/patterns/handoff.py#L25-L28 -->
```python
class Agent:
    name: str
    instructions: str
    can_hand_to: tuple[str, ...] = ()
```

The run passes the task from agent to agent.

<!-- quote: agentbook/patterns/handoff.py#L31-L51 -->
```python
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
```

Read it line by line:

1. `current` is the agent in charge. `path` records every agent that held the task.
2. `shared` is the conversation that every agent sees.
3. Each agent's system prompt lists the agents it may hand off to.
4. A plain answer ends the run with `done`.
5. A handoff after the limit stops the run with `max_handoffs`.
6. A handoff to an agent that is not on the list stops with `bad_target`.
7. A good handoff adds the note to `shared` and changes `current`.

## The example

A customer writes "My order 1182 came broken." Triage hands off to refunds with a note about the order. Refunds answers with the refund. The path is triage, then refunds. That is two calls.

```bash
python -m agentbook handoff
```

## The failure case and its guard

In the failure case, the request is about a parcel that came late and broken. Refunds thinks it is a shipping problem. Shipping thinks it is a refunds problem. They hand it back and forth.

<!-- quote: agentbook/patterns/handoff.py#L72-L79 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """Refunds and shipping pass the task back and forth. The guard stops after 3 handoffs."""
    def ping_pong(messages):
        me = "refunds" if "refunds only" in messages[0]["content"] else "shipping"
        other = "shipping" if me == "refunds" else "refunds"
        return call("handoff", to=other, note=f"Not a {me} problem.")
    counter = CallCounter(FakeModel(respond=ping_pong))
    return run_handoffs(counter, DESK, "refunds", "My parcel came late and broken."), counter
```

Without a guard, the two agents would loop forever. The guard is `max_handoffs`. After three handoffs, the fourth attempt stops the run with `max_handoffs`. The path shows the ping-pong: refunds, shipping, refunds, shipping. A person can read that path and see the gap in the team rules.

A second guard checks the target. A test asks triage to hand off to `admin`. That agent is not on the list, so the run stops with `bad_target`.

## When to use it

- Different agents need different instructions or tools.
- The right agent only becomes clear during the conversation.
- The next agent needs the context of what came before.

## When not to use it

- One decision at the start is enough. Use a router (lesson 3). It is cheaper.
- One agent with a few more tools can do the whole job.
- The agents' areas overlap a lot. Then ping-pong is likely.

## Typical call count

Typical call count: example 2, failure case 4.

The rule is one call for each agent that holds the task. The most you pay is `max_handoffs + 1` calls.

## Exercises

Try the [exercises for this lesson](../../exercises/10-handoff.md) before you read the solutions.
