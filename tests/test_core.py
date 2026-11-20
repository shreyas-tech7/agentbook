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


class FakeOpener:
    """Stands in for urllib's opener. It records each request and plays back answers."""

    def __init__(self, answers):
        self.answers, self.requests = list(answers), []

    def open(self, req, timeout):
        import io
        self.requests.append(req)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return io.BytesIO(json.dumps(answer).encode())


OK = {"choices": [{"message": {"content": "ok"}}]}


def http_error(code):
    import urllib.error
    return urllib.error.HTTPError("https://provider.test", code, "error", {}, None)


def adapter(url, answers, **kw):
    model = OpenAICompatModel(url, "m", **kw)
    model.opener = FakeOpener(answers)
    return model


def test_record_adapter_retries_on_429_with_doubling_waits():
    waits = []
    model = adapter("https://provider.test/v1", [http_error(429), http_error(429), OK],
                    sleep=waits.append)
    assert model.complete([{"role": "user", "content": "hi"}]).text == "ok"
    assert waits == [2.0, 4.0]
    assert model.opener.requests[0].full_url == "https://provider.test/v1/chat/completions"


def test_record_adapter_raises_a_server_error_at_once():
    model = adapter("https://provider.test/v1", [http_error(500), OK], sleep=lambda s: None)
    with pytest.raises(Exception, match="500"):
        model.complete([{"role": "user", "content": "hi"}])
    assert len(model.opener.requests) == 1


@pytest.mark.parametrize("url,sent", [("https://provider.test/v1", True),
                                      ("http://localhost:8080/v1", True),
                                      ("http://provider.test/v1", False)])
def test_key_goes_only_over_https_or_to_this_machine(monkeypatch, url, sent):
    """Broken case: plain http to another host must not carry the key."""
    monkeypatch.setenv("AGENTBOOK_API_KEY", "fake-key-for-test")
    model = adapter(url, [OK])
    model.complete([{"role": "user", "content": "hi"}])
    assert model.opener.requests[0].has_header("Authorization") is sent


def test_adapter_refuses_redirects():
    """A redirect could carry the key to another host, so the adapter follows none."""
    import urllib.request
    model = OpenAICompatModel("https://provider.test/v1", "m")
    handler = next(h for h in model.opener.handlers
                   if isinstance(h, urllib.request.HTTPRedirectHandler))
    req = urllib.request.Request("https://provider.test/v1/chat/completions")
    assert handler.redirect_request(req, None, 302, "Found", {}, "https://other.test/") is None


def test_bad_tool_arguments_do_not_crash():
    data = {"choices": [{"message": {"tool_calls": [
        {"function": {"name": "add", "arguments": "{not json"}}]}}]}
    reply = parse_reply(data)
    assert reply.tool_call.name == "add"
    assert reply.tool_call.args == {"_bad_arguments": "{not json"}


def test_parse_json_strips_a_one_line_fence():
    assert parse_json('```["a"]```') == ["a"]
    assert parse_json('```json\n{"x": 1}\n```') == {"x": 1}
    assert parse_json("not json", default="none") == "none"
