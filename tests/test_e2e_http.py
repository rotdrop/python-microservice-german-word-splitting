"""End-to-end tests talking real HTTP over TCP and Unix domain sockets."""

import http.client
import json
import socket
import sys
import threading
import time

import pytest
import uvicorn

from german_word_splitter.api.routes import get_service
from german_word_splitter.main import create_app


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path: str) -> None:
        super().__init__("localhost")
        self._path = path

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self._path)


def _serve(service, **kwargs):
    app = create_app()
    app.dependency_overrides[get_service] = lambda: service
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning", **kwargs))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started:
        if not thread.is_alive() or time.time() > deadline:
            raise RuntimeError("server failed to start")
        time.sleep(0.02)
    return server, thread


@pytest.fixture
def tcp_connection(service):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server, thread = _serve(service, host="127.0.0.1", port=port)
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    yield conn
    conn.close()
    server.should_exit = True
    thread.join(10)


@pytest.fixture
def uds_connection(service, tmp_path):
    if not hasattr(socket, "AF_UNIX") or sys.platform == "win32":
        pytest.skip("Unix domain sockets unavailable")
    path = str(tmp_path / "splitter.sock")
    server, thread = _serve(service, uds=path)
    conn = UnixHTTPConnection(path)
    conn.timeout = 10
    yield conn
    conn.close()
    server.should_exit = True
    thread.join(10)


def _post(conn, payload):
    conn.request(
        "POST",
        "/split",
        body=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    return resp.status, json.loads(resp.read())


@pytest.fixture(params=["tcp", "uds"])
def conn(request):
    return request.getfixturevalue(f"{request.param}_connection")


def test_split_over_socket(conn):
    status, body = _post(conn, {"word": " Haustür "})
    assert status == 200
    assert body["word"] == "Haustür"
    assert body["splittable"] is True
    assert body["components"] == ["Haus", "Tür"]


def test_errors_over_socket(conn):
    assert _post(conn, {"word": "  "})[0] == 400
    status, body = _post(conn, {"word": "Haustür", "method": "nope"})
    assert status == 400
    assert "nope" in body["detail"]
