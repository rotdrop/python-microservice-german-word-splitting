"""Integration tests for the PHP reverse proxy."""

import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROXY = ROOT / "php" / "proxy.php"


def _php_available() -> bool:
    if os.name != "posix":
        return False
    php = shutil.which("php")
    if php is None:
        return False
    result = subprocess.run(
        [php, "-m"], capture_output=True, check=True, text=True
    )
    return "curl" in result.stdout.lower()


pytestmark = pytest.mark.skipif(
    not _php_available(), reason="PHP CLI and the cURL extension are required"
)


class RecordingHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    last_request = None

    def _handle(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        type(self).last_request = {
            "method": self.command,
            "path": self.path,
            "body": self.rfile.read(length),
            "headers": self.headers,
        }
        body = b"upstream response"
        self.send_response(202)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("X-Upstream", "present")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    do_GET = _handle
    do_POST = _handle
    do_PATCH = _handle

    def log_message(self, format, *args) -> None:
        pass


@pytest.fixture
def upstream():
    RecordingHandler.last_request = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), RecordingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_port
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def proxy_server(tmp_path, upstream):
    yield from _start_proxy(tmp_path, upstream)


@pytest.fixture
def proxy_without_upstream(tmp_path):
    yield from _start_proxy(tmp_path, _free_port())


@pytest.fixture
def proxy_with_launchable_service(tmp_path):
    service_port = _free_port()
    executable = tmp_path / "fake-service"
    executable.write_text(
        f"""#!{sys.executable}
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"started service"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        threading.Timer(0.1, self.server.shutdown).start()

    def log_message(self, format, *args):
        pass

server = ThreadingHTTPServer(
    ("127.0.0.1", int(os.environ["GERMAN_WORD_SPLITTER_PORT"])), Handler
)
server.serve_forever()
"""
    )
    executable.chmod(0o755)
    yield from _start_proxy(tmp_path, service_port, executable)


def _start_proxy(tmp_path, service_port, executable=None):
    php = shutil.which("php")
    server_port = _free_port()
    env = os.environ.copy()
    env.update(
        {
            "GERMAN_WORD_SPLITTER_PORT": str(service_port),
            "GERMAN_WORD_SPLITTER_BIN": str(
                executable or tmp_path / "missing-service"
            ),
            "GERMAN_WORD_SPLITTER_LOG": str(tmp_path / "service.log"),
            "GERMAN_WORD_SPLITTER_SOCKET": "",
        }
    )
    process = subprocess.Popen(
        [php, "-S", f"127.0.0.1:{server_port}", "-t", str(PROXY.parent)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail("PHP built-in server exited before becoming ready")
        try:
            with socket.create_connection(("127.0.0.1", server_port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.02)
    else:
        process.terminate()
        pytest.fail("PHP built-in server did not become ready")

    yield server_port
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _request(port: int, target: str, method: str = "GET", body: bytes = b""):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(
            method,
            target,
            body=body,
            headers={"X-Client": "forwarded", "Accept-Encoding": "identity"},
        )
        response = conn.getresponse()
        return response.status, response.headers, response.read()
    finally:
        conn.close()


def test_forwards_method_path_query_headers_and_body(proxy_server):
    body = b'{"word":"Haust\xc3\xbcr"}'
    status, headers, response_body = _request(
        proxy_server,
        "/proxy.php?path=%2Fsplit%2Fword&lang=de&limit=2",
        method="PATCH",
        body=body,
    )

    assert status == 202
    assert response_body == b"upstream response"
    assert headers["X-Upstream"] == "present"
    assert RecordingHandler.last_request["method"] == "PATCH"
    assert RecordingHandler.last_request["path"] == "/split/word?lang=de&limit=2"
    assert RecordingHandler.last_request["body"] == body
    assert RecordingHandler.last_request["headers"]["X-Client"] == "forwarded"
    assert RecordingHandler.last_request["headers"]["Accept-Encoding"] is None


def test_uses_path_info_for_upstream_path(proxy_server):
    status, _, body = _request(proxy_server, "/proxy.php/split?method=charsplit")

    assert status == 202
    assert body == b"upstream response"
    assert RecordingHandler.last_request["path"] == "/split?method=charsplit"


def test_returns_bad_gateway_when_executable_is_missing(proxy_without_upstream):
    status, headers, body = _request(
        proxy_without_upstream, "/proxy.php?path=%2Fsplit"
    )

    assert status == 502
    assert headers.get_content_type() == "application/json"
    assert json.loads(body) == {
        "detail": "Service executable not found or not executable."
    }


def test_launches_service_when_upstream_is_unavailable(proxy_with_launchable_service):
    status, _, body = _request(
        proxy_with_launchable_service, "/proxy.php?path=%2Fhealth"
    )

    assert status == 200
    assert body == b"started service"
