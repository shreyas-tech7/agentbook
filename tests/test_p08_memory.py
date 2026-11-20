from agentbook.counter import estimate_tokens
from agentbook.patterns import memory as p
from agentbook.tools import system, user


class NaiveMemory(p.Memory):
    """The broken version: no pinning and no cut. Everything is an ordinary turn."""

    def add(self, message):
        self.turns.append(message)


def test_example_keeps_everything():
    outcome, counter = p.example()
    assert outcome.extra["dropped"] == 0
    assert outcome.extra["pinned_kept"]
    assert counter.calls == 5


def test_oldest_turns_drop_first():
    memory = p.Memory(max_tokens=20)
    for n in range(10):
        memory.add(user(f"message number {n} here"))
    window = memory.window()
    assert window[-1]["content"] == "message number 9 here"
    assert "message number 0 here" not in [m["content"] for m in window]
    assert memory.dropped > 0


def test_failure_case_naive_memory_loses_the_system_prompt():
    """Broken case: a 6,000-character paste. Naive memory then shows the model nothing."""
    naive = NaiveMemory(max_tokens=200)
    naive.add(system("You are a cooking helper. The user is vegetarian."))
    naive.add(user("error line\n" * 545))
    assert naive.window() == []  # the paste does not fit, and nothing older is kept


def test_failure_case_guard_cuts_the_paste_and_keeps_pins():
    outcome, counter = p.failure_example()
    assert outcome.extra["cut"] == 1
    assert outcome.extra["pinned_kept"]
    assert outcome.extra["window_tokens"] <= 200
    assert counter.calls == 3


def test_a_cut_message_fits_in_half_the_cap():
    memory = p.Memory(max_tokens=100)
    memory.add(user("x" * 5000))
    assert estimate_tokens(memory.turns[0]["content"]) <= 50
    assert memory.turns[0]["content"].endswith("[cut]")
