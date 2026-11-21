"""Solutions for lesson 12, retrieval as a tool."""

import _run

from agentbook.model import FakeModel, call, say
from agentbook.patterns.retrieval import HANDBOOK, Index, answer_with_search


def solution_1():
    """A new document is one more dict entry. It shares two words with the query."""
    index = Index({**HANDBOOK.docs, "d4": "Sick leave needs a note after three days."})
    hits = index.search("sick leave")
    assert hits[0] == "d4"
    return hits


def solution_2():
    """The search returned nothing, so no citation can be valid."""
    fake = FakeModel([call("search", query="pizza"), say("Pizza on Fridays [d1].")])
    outcome = answer_with_search(fake, "Is there pizza?", HANDBOOK)
    assert outcome.stop == "bad_citation" and outcome.extra["returned"] == []
    return outcome.stop


def solution_3():
    """Both score 1. Ties sort by id, so d1 comes before d2."""
    hits = HANDBOOK.search("leave")
    assert hits == ["d1", "d2"]
    return hits


if __name__ == "__main__":
    _run.run(globals())
