"""Solutions for lesson 9, human approval."""

import _run

from agentbook.model import FakeModel, call, say
from agentbook.patterns.human_approval import file_tools, run_with_approval
from agentbook.tools import Tool, toolbox


def solution_1():
    """The first call asks for list_files, which is now risky. The run stops at step 1."""
    tools = file_tools({"a.txt": ""})
    tools["list_files"].risky = True
    outcome = run_with_approval(FakeModel([call("list_files")]), "list", tools,
                                approve=lambda c: False)
    assert (outcome.stop, outcome.steps) == ("denied", 1)
    return outcome.steps


def solution_2():
    """The approver reads the arguments of the call it is asked about."""
    def logs_only(tool_call):
        return tool_call.name == "delete_file" and tool_call.args.get("name", "").endswith(".log")

    files = {"old.log": "", "notes.txt": ""}
    fake = FakeModel([call("delete_file", name="old.log"), call("delete_file", name="notes.txt")])
    outcome = run_with_approval(fake, "clean up", file_tools(files), approve=logs_only)
    assert outcome.stop == "denied" and sorted(files) == ["notes.txt"]
    return sorted(files)


def solution_3():
    """With no approver every risky call is denied. The outbox list stays empty."""
    outbox = []
    tools = toolbox(Tool("send_email", "Send an email.", lambda to, body: outbox.append(to),
                         {"to": "address", "body": "text"}, risky=True))
    fake = FakeModel([call("send_email", to="boss@company.test", body="I quit"), say("sent")])
    outcome = run_with_approval(fake, "email my boss", tools)
    assert outcome.stop == "denied" and outbox == []
    return outcome.stop


if __name__ == "__main__":
    _run.run(globals())
