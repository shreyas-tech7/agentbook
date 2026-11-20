from agentbook.model import FakeModel, call, say
from agentbook.patterns import retrieval as p


def test_search_ranks_by_shared_words():
    assert p.HANDBOOK.search("unused leave next year") == ["d2", "d1"]
    assert p.HANDBOOK.search("pizza") == []


def test_example_cites_what_it_found():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert outcome.extra["cited"] == ["d2"]
    assert counter.calls == 2


def test_failure_case_made_up_citation_is_flagged():
    """Broken case: the answer cites [d7], a document that no search returned."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "bad_citation"
    assert outcome.extra["unknown"] == ["d7"]


def test_an_answer_with_no_citation_is_flagged():
    fake = FakeModel([say("You get 25 days.")])
    assert p.answer_with_search(fake, "How much leave?", p.HANDBOOK).stop == "no_citation"


def test_citing_without_searching_is_flagged():
    """Broken case: the model skips the search and cites [d1] from thin air."""
    fake = FakeModel([say("25 days [d1].")])
    assert p.answer_with_search(fake, "How much leave?", p.HANDBOOK).stop == "bad_citation"


def test_empty_search_says_no_results():
    fake = FakeModel([call("search", query="pizza"), say("I found nothing [d1].")])
    outcome = p.answer_with_search(fake, "pizza?", p.HANDBOOK)
    assert outcome.trace[3]["content"] == "no results"
    assert outcome.stop == "bad_citation"
