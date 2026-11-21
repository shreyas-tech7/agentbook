# Lesson 8. Memory

A model remembers nothing between calls. Every call must carry the history it needs. Anthropic's post ["Building effective agents"](https://www.anthropic.com/research/building-effective-agents) lists memory as part of the augmented model. This lesson shows the simplest useful memory: a window with a size cap.

## The problem

A chat sends the whole history with every call. The history grows with each turn. Sooner or later it is too big for the model, or too expensive. We must drop something. But some things must never drop, such as the system prompt.

## The idea

Memory has two parts. Pinned messages stay forever. Turns are the normal back and forth. Before each call, we build a window. It holds the pinned messages and the newest turns that still fit under the cap. The oldest turns drop first.

## The code

<!-- quote: agentbook/patterns/memory.py#L21-L56 -->
```python
class Memory:
    def __init__(self, max_tokens: int = 200):
        self.max_tokens = max_tokens
        self.pinned: list[Message] = []
        self.turns: list[Message] = []
        self.dropped = 0
        self.cut = 0

    def pin(self, message: Message) -> None:
        if self.size(self.pinned + [message]) > self.max_tokens // 2:
            raise ValueError("pinned messages may use at most half the cap")
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
```

Read it line by line:

1. `max_tokens` is the cap for the whole window. We use the estimate from the counter.
2. `pin` adds a message that never drops. Pinned messages may use at most half the cap, so the chat always has room.
3. `add` adds a turn. A turn bigger than half the cap is cut and marked `[cut]`.
4. `window` starts with the room left after the pinned messages.
5. It walks the turns from newest to oldest and keeps each one that fits.
6. It stops at the first turn that does not fit, so the kept turns stay in order.
7. `dropped` records how many turns were left out.

One chat turn adds the user text, calls the model with the window and saves the reply.

<!-- quote: agentbook/patterns/memory.py#L59-L63 -->
```python
def chat_turn(model: Model, memory: Memory, text: str) -> str:
    memory.add(user(text))
    reply = model.complete(memory.window())
    memory.add(assistant(reply))
    return reply.text
```

## The example

A cooking helper chats for five short turns. The pinned system message says the user is vegetarian. Everything fits under the cap of 200 tokens. Nothing drops. That is five calls, one per turn.

```bash
python -m agentbook memory
```

## The failure case and its guard

In the failure case, the user pastes a log of 6,000 characters. That is about 1,500 tokens.

<!-- quote: agentbook/patterns/memory.py#L87-L94 -->
```python
def failure_example() -> tuple[Outcome, CallCounter]:
    """The user pastes a 6,000-character log. It is cut, and the pinned facts survive."""
    memory = Memory(max_tokens=200)
    memory.pin(system("You are a cooking helper. The user is vegetarian."))
    fake = FakeModel(["Hi!", "That log is long. I read the start.", "Still vegetarian: yes."])
    counter = CallCounter(fake)
    texts = ["Hello", "error line\n" * 545, "Am I still vegetarian?"]
    return run_chat(counter, memory, texts), counter
```

A naive memory has no pins and no cut. The test `test_failure_case_naive_memory_loses_the_system_prompt` shows what happens. The paste does not fit, so the window keeps nothing older than it. The window is empty. The model would forget that the user is vegetarian.

Our memory has two guards. Pinned messages never drop. A single turn can use at most half the cap, so the paste is cut. After the paste, the window still holds the system prompt and stays under 200 tokens. The stop reason is `cut`. It warns your code that the model saw only part of one turn.

## When to use it

- A conversation runs for many turns.
- Some facts must survive every turn.
- You need a hard limit on the size of each call.

## When not to use it

- Each request stands alone. Send only that request.
- Old turns matter as much as new ones. Then you need a summary or a search over the history (lesson 12), not a window.

## Typical call count

Typical call count: example 5, failure case 3.

Memory adds no calls of its own. It changes how many tokens each call costs. That is why the cap matters.

## Exercises

Try the [exercises for this lesson](../../exercises/08-memory.md) before you read the solutions.
