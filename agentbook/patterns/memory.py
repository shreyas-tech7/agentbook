"""Pattern 8. Memory.

A chat keeps its history between turns. History grows, but the model's window does not.
This memory keeps pinned facts forever and keeps the newest turns that fit a size cap.
It drops the oldest turns first.

Failure: one huge message pushes the system prompt and every fact out of the window.
Guard: pinned messages never drop, and one message can use at most half the cap.
A longer message is cut and marked "[cut]".
"""

from __future__ import annotations

from agentbook.counter import CallCounter, estimate_tokens
from agentbook.model import FakeModel, Message, Model
from agentbook.tools import Outcome, assistant, system, user

CUT = " [cut]"


class Memory:
    def __init__(self, max_tokens: int = 200):
        self.max_tokens = max_tokens
        self.pinned: list[Message] = []
        self.turns: list[Message] = []
        self.dropped = 0
        self.cut = 0

    def pin(self, message: Message) -> None:
        self.pinned.append(message)

    def add(self, message: Message) -> None:
        limit = self.max_tokens // 2
        if estimate_tokens(message["content"]) > limit:
            keep = limit * 4 - len(CUT)
            message = {**message, "content": message["content"][:keep] + CUT}
            self.cut += 1
        self.turns.append(message)

    def size(self, messages: list[Message]) -> int:
        return sum(estimate_tokens(m["content"]) for m in messages)

    def window(self) -> list[Message]:
        """Pinned messages, then the newest turns that still fit under the cap."""
        room = self.max_tokens - self.size(self.pinned)
        kept: list[Message] = []
        for message in reversed(self.turns):
            cost = estimate_tokens(message["content"])
            if cost > room:
                break
            kept.insert(0, message)
            room -= cost
        self.dropped = len(self.turns) - len(kept)
        return self.pinned + kept


def chat_turn(model: Model, memory: Memory, text: str) -> str:
    memory.add(user(text))
    reply = model.complete(memory.window())
    memory.add(assistant(reply))
    return reply.text


def run_chat(model: Model, memory: Memory, texts: list[str]) -> Outcome:
    answers = [chat_turn(model, memory, text) for text in texts]
    window = memory.window()
    return Outcome(answers[-1], "done", steps=len(texts),
                   extra={"window_tokens": memory.size(window), "dropped": memory.dropped,
                          "cut": memory.cut,
                          "pinned_kept": all(p in window for p in memory.pinned)})


def example() -> tuple[Outcome, CallCounter]:
    """Five short turns fit under the cap. Nothing drops. Five calls."""
    memory = Memory(max_tokens=200)
    memory.pin(system("You are a cooking helper. The user is vegetarian."))
    fake = FakeModel(["Hi!", "Try lentil soup.", "About 30 minutes.", "Yes, add cumin.",
                      "Serve it with bread."])
    counter = CallCounter(fake)
    texts = ["Hello", "Dinner idea?", "How long?", "Any spice?", "What on the side?"]
    return run_chat(counter, memory, texts), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The user pastes a 6,000-character log. It is cut, and the pinned facts survive."""
    memory = Memory(max_tokens=200)
    memory.pin(system("You are a cooking helper. The user is vegetarian."))
    fake = FakeModel(["Hi!", "That log is long. I read the start.", "Still vegetarian: yes."])
    counter = CallCounter(fake)
    texts = ["Hello", "error line\n" * 545, "Am I still vegetarian?"]
    return run_chat(counter, memory, texts), counter
