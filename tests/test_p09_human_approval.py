from agentbook.model import FakeModel, call, say
from agentbook.patterns import human_approval as p


def test_example_runs_after_a_yes():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert outcome.extra["files_left"] == ["notes.txt"]
    assert counter.calls == 3


def test_failure_case_a_no_blocks_the_delete():
    """Broken case: the model tries to delete notes.txt, which the person wants to keep."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "denied"
    assert outcome.extra["blocked_call"].args == {"name": "notes.txt"}
    assert outcome.extra["files_left"] == ["notes.txt", "old.log"]
    assert counter.calls == 2


def test_no_approver_means_no():
    files = {"a.txt": "", "b.txt": ""}
    fake = FakeModel([call("delete_file", name="a.txt")])
    outcome = p.run_with_approval(fake, "delete a.txt", p.file_tools(files), approve=None)
    assert outcome.stop == "denied"
    assert sorted(files) == ["a.txt", "b.txt"]


def test_safe_tools_never_ask():
    asked = []
    fake = FakeModel([call("list_files"), say("a.txt")])
    p.run_with_approval(fake, "list", p.file_tools({"a.txt": ""}),
                        approve=lambda c: asked.append(c) or True)
    assert asked == []


def test_terminal_approver_needs_the_word_yes(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    assert p.ask_in_terminal(call("delete_file", name="a").tool_call) is False
    monkeypatch.setattr("builtins.input", lambda prompt: " YES ")
    assert p.ask_in_terminal(call("delete_file", name="a").tool_call) is True
