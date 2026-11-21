"""Pattern 12. Retrieval as a tool.

Search is one more tool. The model decides when to search and what to search for.
Our search is a small keyword index, so it runs offline and you can read every line.
The answer must cite the documents it used, such as [d2].

Failure: the model cites a document that the search never returned. It made up a source.
Guard: our code compares the citations with the ids the search returned.
An unknown citation gives "bad_citation". An answer with no citation gives "no_citation".
"""

from __future__ import annotations

import re

from agentbook.counter import CallCounter
from agentbook.model import FakeModel, Model, call, say
from agentbook.tools import (
    Outcome,
    Tool,
    assistant,
    run_tool,
    specs,
    system,
    tool_result,
    toolbox,
    user,
)

SYSTEM = "Search before you answer. Cite each document you use like [d1]."


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class Index:
    def __init__(self, docs: dict[str, str]):
        self.docs = docs

    def search(self, query: str, k: int = 2) -> list[str]:
        """Rank documents by how many query words they share. Ties go to the lower id."""
        wanted = words(query)
        scored = [(len(wanted & words(text)), doc_id) for doc_id, text in self.docs.items()]
        hits = sorted((s for s in scored if s[0] > 0), key=lambda s: (-s[0], s[1]))
        return [doc_id for _, doc_id in hits[:k]]


def answer_with_search(model: Model, question: str, index: Index, max_steps: int = 4) -> Outcome:
    returned: set[str] = set()

    def search(query: str) -> str:
        ids = index.search(query)
        returned.update(ids)
        return "\n".join(f"[{i}] {index.docs[i]}" for i in ids) or "no results"

    tools = toolbox(Tool("search", "Search the documents.", search, {"query": "search words"}))
    messages = [system(SYSTEM), user(question)]
    for step in range(1, max_steps + 1):
        reply = model.complete(messages, specs(tools))
        messages.append(assistant(reply))
        if reply.tool_call is not None:
            messages.append(tool_result("search", run_tool(tools, reply.tool_call)))
            continue
        cited = set(re.findall(r"\[(d\d+)\]", reply.text))
        extra = {"cited": sorted(cited), "returned": sorted(returned)}
        if not cited:
            return Outcome(reply.text, "no_citation", steps=step, trace=messages, extra=extra)
        if not cited <= returned:
            extra["unknown"] = sorted(cited - returned)
            return Outcome(reply.text, "bad_citation", steps=step, trace=messages, extra=extra)
        return Outcome(reply.text, "done", steps=step, trace=messages, extra=extra)
    return Outcome(None, "max_steps", steps=max_steps, trace=messages)


HANDBOOK = Index({
    "d1": "Staff get 25 days of paid leave each year.",
    "d2": "Unused leave carries over for up to 5 days into the next year.",
    "d3": "The office closes on public holidays.",
})


def example() -> tuple[Outcome, CallCounter]:
    """The model searches once, then answers with citations the search returned. Two calls."""
    fake = FakeModel([call("search", query="unused leave next year"),
                      say("Up to 5 unused days carry over to next year [d2].")])
    counter = CallCounter(fake)
    return answer_with_search(counter, "Can I keep unused leave?", HANDBOOK), counter


def failure_example() -> tuple[Outcome, CallCounter]:
    """The model cites [d7]. No search returned d7, so the guard flags the answer."""
    fake = FakeModel([call("search", query="unused leave"),
                      say("You can carry over all of it [d2][d7].")])
    counter = CallCounter(fake)
    return answer_with_search(counter, "Can I keep unused leave?", HANDBOOK), counter
