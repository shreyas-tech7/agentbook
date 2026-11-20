"""Test setup. The network guard makes every test fail if it opens a non-local connection."""

import socket

import pytest

LOCAL = {"127.0.0.1", "::1", "localhost"}
_real_connect = socket.socket.connect


class NetworkBlocked(RuntimeError):
    pass


def _guarded_connect(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if isinstance(host, str) and (host in LOCAL or self.family == socket.AF_UNIX):
        return _real_connect(self, address)
    raise NetworkBlocked(f"tests must run offline, blocked connection to {address!r}")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    monkeypatch.setattr(socket, "create_connection", _blocked_create_connection)
    yield


def _blocked_create_connection(address, *args, **kwargs):
    host = address[0]
    if host in LOCAL:
        return _real_create_connection(address, *args, **kwargs)
    raise NetworkBlocked(f"tests must run offline, blocked connection to {address!r}")


_real_create_connection = socket.create_connection
