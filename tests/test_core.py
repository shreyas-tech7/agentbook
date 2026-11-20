import json

import pytest

from agentbook.counter import CallCounter, estimate_tokens
from agentbook.model import (
    FakeModel,
    OpenAICompatModel,
    Reply,
    ScriptExhausted,
    ToolCall,
    call,
    parse_reply,
    say,
    to_wire,
)
from agentbook.tools import Tool, assistant, parse_json, run_tool, toolbox


def test_fake_model_replays_the_script_in_order():
    fake = FakeModel(["one", call("add", a="1")])
    assert fake.complete([]).text == "one"
    assert fake.complete([]).tool_call == ToolCall("add", {"a": "1"})


def test_fake_model_raises_when_the_script_runs_out():
    """Broken case: a pattern makes more calls than the test planned."""
    fake = FakeModel(["only one"])
    fake.complete([])
    with pytest.raises(ScriptExhausted):
        fake.complete([])


def test_call_accepts_a_tool_argument_named_name():
    """Broken case: call("delete_file", name="x") used to clash with call's own `name`."""
    assert call("delete_file", name="x").tool_call == ToolCall("delete_file", {"name": "x"})


def test_fake_model_records_what_it_saw():
    fake = FakeModel(respond=lambda m: say(m[-1]["content"].upper()))
    assert fake.complete([{"role": "user", "content": "hi"}]).text == "HI"
    assert fake.seen == [[{"role": "user", "content": "hi"}]]


def test_estimate_tokens_is_about_four_characters():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2


def test_counter_counts_calls_and_tokens():
    counter = CallCounter(FakeModel(["abcdefgh", call("t", x="y")]))
    counter.complete([{"role": "user", "content": "abcd"}])
    counter.complete([{"role": "user", "content": "abcd"}])
    assert counter.calls == 2
    assert counter.tokens_in == 2
    assert counter.tokens_out == 2 + estimate_tokens("t" + json.dumps({"x": "y"}))
    assert counter.summary()["tokens"] == counter.tokens


def test_run_tool_turns_errors_into_text():
    tools = toolbox(Tool("div", "Divide.", lambda a, b: int(a) / int(b), {"a": "", "b": ""}))
    assert run_tool(tools, ToolCall("div", {"a": "6", "b": "3"})) == "2.0"
    assert run_tool(tools, ToolCall("div", {"a": "1", "b": "0"})).startswith("error: ZeroDivision")
    assert "unknown tool 'nope'" in run_tool(tools, ToolCall("nope"))


def test_tool_spec_lists_required_params():
    spec = Tool("add", "Add.", lambda a, b: a, {"a": "x", "b": "y"}).spec()
    assert spec["parameters"]["required"] == ["a", "b"]


def test_assistant_message_shows_tool_calls_as_text():
    assert assistant(call("add", b="2", a="1"))["content"] == 'CALL add {"a": "1", "b": "2"}'


def test_parse_json_strips_code_fences():
    assert parse_json('```json\n["a"]\n```') == ["a"]
    assert parse_json("not json", default=[]) == []


def test_parse_reply_reads_text_and_tool_calls():
    text = {"choices": [{"message": {"content": "hello"}}]}
    tool = {"choices": [{"message": {"content": None, "tool_calls": [
        {"function": {"name": "add", "arguments": '{"a": "1"}'}}]}}]}
    assert parse_reply(text) == Reply(text="hello")
    assert parse_reply(tool) == Reply(tool_call=ToolCall("add", {"a": "1"}))


def test_to_wire_sends_tool_results_as_user_text():
    assert to_wire({"role": "tool", "name": "add", "content": "3"}) == {
        "role": "user", "content": "Tool result from add: 3"}


def test_record_adapter_retries_on_429_with_doubling_waits(monkeypatch):
    import io
    import urllib.error
    import urllib.request

    waits, attempts = [], []

    def fake_urlopen(req, timeout):
        attempts.append(req.full_url)
        if len(attempts) < 3:
            raise urllib.error.HTTPError(req.full_url, 429, "slow down", {}, None)
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    model = OpenAICompatModel("https://provider.test/v1", "m", sleep=waits.append)
    assert model.complete([{"role": "user", "content": "hi"}]).text == "ok"
    assert waits == [2.0, 4.0]
    assert attempts[0] == "https://provider.test/v1/chat/completions"
