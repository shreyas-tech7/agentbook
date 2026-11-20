"""Solutions for lesson 8, memory."""

import _run

from agentbook.counter import estimate_tokens
from agentbook.patterns.memory import Memory
from agentbook.tools import system, user


def solution_1():
    """Pinned messages never drop, however many turns follow."""
    memory = Memory(max_tokens=60)
    facts = [system("You are a cooking helper."), system("The user has a nut allergy.")]
    for fact in facts:
        memory.pin(fact)
    for n in range(30):
        memory.add(user(f"turn {n}"))
    window = memory.window()
    assert all(fact in window for fact in facts) and memory.dropped > 0
    return memory.dropped


def solution_2():
    """'hello there friend' has 18 characters, so 5 tokens. 40 // 5 = 8 turns fit."""
    memory = Memory(max_tokens=40)
    for _ in range(10):
        memory.add(user("hello there friend"))
    assert estimate_tokens("hello there friend") == 5
    assert len(memory.window()) == 8
    return len(memory.window())


def solution_3():
    """A subclass keeps the size rule and adds a count rule."""
    class LastFour(Memory):
        def window(self):
            full = super().window()
            pins, turns = full[:len(self.pinned)], full[len(self.pinned):]
            return pins + turns[-4:]

    memory = LastFour(max_tokens=500)
    for n in range(10):
        memory.add(user(f"turn {n}"))
    assert [m["content"] for m in memory.window()] == ["turn 6", "turn 7", "turn 8", "turn 9"]
    return len(memory.window())


if __name__ == "__main__":
    _run.run(globals())
