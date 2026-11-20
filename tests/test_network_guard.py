import socket
import urllib.request

import pytest
from conftest import NetworkBlocked

from agentbook.model import OpenAICompatModel


def test_guard_blocks_a_real_connection():
    """Broken case: without the guard this test would try to reach the internet."""
    with pytest.raises(NetworkBlocked):
        socket.create_connection(("example.org", 80), timeout=1)


def test_guard_blocks_urllib_and_the_record_adapter():
    """Broken case: the record-mode adapter would call a real provider from a test."""
    with pytest.raises(NetworkBlocked):
        urllib.request.urlopen("http://example.org", timeout=1)  # noqa: S310
    model = OpenAICompatModel("http://example.org/v1", "any-model", tries=1)
    with pytest.raises(NetworkBlocked):
        model.complete([{"role": "user", "content": "hi"}])


def test_adapter_refuses_other_url_schemes():
    with pytest.raises(ValueError):
        OpenAICompatModel("file:///etc/passwd", "m")


def test_local_connections_still_work():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    client = socket.create_connection(server.getsockname(), timeout=1)
    client.close()
    server.close()
