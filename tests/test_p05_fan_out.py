import threading
import time

from agentbook.counter import CallCounter
from agentbook.model import FakeModel
from agentbook.patterns import fan_out as p


def test_example_merges_three_reviews():
    outcome, counter = p.example()
    assert outcome.stop == "done"
    assert counter.calls == 4
    assert "They're" in outcome.answer and "honestly" in outcome.answer


def test_workers_really_run_side_by_side():
    seen_threads = set()
    respond = p.reviewer()

    def slow(messages):
        seen_threads.add(threading.get_ident())
        time.sleep(0.05)
        return respond(messages)

    start = time.monotonic()
    p.fan_out(FakeModel(respond=slow), p.TEXT, p.ANGLES)
    assert time.monotonic() - start < 0.05 * 4  # serial would take 4 sleeps
    assert len(seen_threads) >= 2


def test_failure_case_crashed_worker_becomes_a_missing_line():
    """Broken case: the tone worker raises ConnectionError in the middle of the run."""
    outcome, counter = p.failure_example()
    assert outcome.stop == "partial"
    assert outcome.extra["missing"] == ["tone"]
    assert "tone: MISSING (ConnectionError)" in outcome.extra["parts"]
    assert counter.calls == 3  # two reviews and the merge


def test_a_hung_worker_times_out():
    """Broken case: one worker hangs. Without the timeout the merge would wait for it."""
    respond = p.reviewer()

    def hang_on_clarity(messages):
        if "clarity" in messages[0]["content"]:
            time.sleep(1.0)
        return respond(messages)

    start = time.monotonic()
    outcome = p.fan_out(FakeModel(respond=hang_on_clarity), p.TEXT, p.ANGLES, timeout=0.1)
    assert time.monotonic() - start < 0.9
    assert outcome.extra["missing"] == ["clarity"]


def test_all_workers_failing_skips_the_merge():
    def broken(messages):
        raise ConnectionError("down")

    counter = CallCounter(FakeModel(respond=broken))
    assert p.fan_out(counter, p.TEXT, p.ANGLES).stop == "all_failed"
    assert counter.calls == 0


def test_hung_workers_share_one_deadline():
    """Broken case: three hung workers. One timeout each would take three times as long."""
    def hang(messages):
        if "Merge" not in messages[0]["content"]:
            time.sleep(0.5)
        return "merged"

    start = time.monotonic()
    outcome = p.fan_out(FakeModel(respond=hang), p.TEXT, p.ANGLES, timeout=0.15)
    assert time.monotonic() - start < 0.4
    assert outcome.stop == "all_failed"
