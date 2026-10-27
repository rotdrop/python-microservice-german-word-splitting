import importlib
import os

import pytest
import uvicorn

from german_word_splitter import config, main


def test_get_socket_unset(monkeypatch):
    monkeypatch.delenv(config.SOCKET_ENV, raising=False)
    monkeypatch.setattr(config, "DEFAULT_SOCKET", None)
    assert config.get_socket() is None


def test_get_socket_env_overrides_default(monkeypatch):
    monkeypatch.setattr(config, "DEFAULT_SOCKET", "venv/run/x.sock")
    monkeypatch.setenv(config.SOCKET_ENV, "/tmp/a.sock")
    assert config.get_socket() == "/tmp/a.sock"


def test_get_socket_generated_default(monkeypatch):
    monkeypatch.delenv(config.SOCKET_ENV, raising=False)
    monkeypatch.setattr(config, "DEFAULT_SOCKET", "venv/run/x.sock")
    assert config.get_socket() == "venv/run/x.sock"


def test_get_socket_empty_env_uses_generated_default(monkeypatch):
    monkeypatch.setenv(config.SOCKET_ENV, "")
    monkeypatch.setattr(config, "DEFAULT_SOCKET", "venv/run/x.sock")
    assert config.get_socket() == "venv/run/x.sock"


def test_get_port_unset_uses_generated_default(monkeypatch):
    monkeypatch.delenv(config.PORT_ENV, raising=False)
    monkeypatch.setattr(config, "DEFAULT_PORT", 8123)
    assert config.get_port() == 8123


def test_get_port_env_overrides_default(monkeypatch):
    monkeypatch.setattr(config, "DEFAULT_PORT", 8123)
    monkeypatch.setenv(config.PORT_ENV, "9000")
    assert config.get_port() == 9000


def test_get_settings_unset_uses_default_dictionary(monkeypatch):
    monkeypatch.delenv(config.DICTIONARY_ENV, raising=False)
    assert config.get_settings().dictionary_path == config.DEFAULT_DICTIONARY


def test_get_settings_env_overrides_default_dictionary(monkeypatch):
    monkeypatch.setenv(config.DICTIONARY_ENV, "/data/custom.dic")
    assert config.get_settings().dictionary_path == "/data/custom.dic"


def test_transliteration_locales_default_empty(monkeypatch):
    monkeypatch.delenv(config.LOCALES_ENV, raising=False)
    assert config.get_settings().transliteration_locales == ()


@pytest.mark.parametrize(
    "value", ["de_DE.UTF-8,en_US.UTF-8", "de_DE.UTF-8 en_US.UTF-8", " de_DE.UTF-8, en_US.UTF-8 "]
)
def test_transliteration_locales_from_env(monkeypatch, value):
    monkeypatch.setenv(config.LOCALES_ENV, value)
    assert config.get_settings().transliteration_locales == (
        "de_DE.UTF-8",
        "en_US.UTF-8",
    )


def test_generated_default_module_is_used(monkeypatch):
    import sys

    module = type(sys)("german_word_splitter._default_socket")
    module.DEFAULT_SOCKET = "s.sock"
    monkeypatch.setitem(sys.modules, "german_word_splitter._default_socket", module)
    try:
        importlib.reload(config)
        assert config.DEFAULT_SOCKET == "s.sock"
    finally:
        monkeypatch.delitem(sys.modules, "german_word_splitter._default_socket")
        importlib.reload(config)


def test_get_port_file(monkeypatch):
    monkeypatch.delenv(config.PORT_FILE_ENV, raising=False)
    assert config.get_port_file() is None
    monkeypatch.setenv(config.PORT_FILE_ENV, "/run/x/port")
    assert config.get_port_file() == "/run/x/port"


def test_get_socket_mode(monkeypatch):
    monkeypatch.delenv(config.SOCKET_MODE_ENV, raising=False)
    assert config.get_socket_mode() == 0o660
    monkeypatch.setenv(config.SOCKET_MODE_ENV, "666")
    assert config.get_socket_mode() == 0o666


def test_run_uses_socket(monkeypatch):
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(kw))
    monkeypatch.setattr(main, "get_socket", lambda: "/tmp/s.sock")
    monkeypatch.setattr(main, "get_socket_mode", lambda: 0o666)
    old = os.umask(0o022)
    try:
        main.run()
        assert os.umask(old) == 0o111
    finally:
        os.umask(old)
    assert calls == [{"uds": "/tmp/s.sock"}]


class FakeServer:
    instances = []

    def __init__(self, config):
        self.config = config
        self.sockets = None
        FakeServer.instances.append(self)

    def run(self, sockets=None):
        self.sockets = sockets


def _run_tcp(monkeypatch, port, port_file):
    FakeServer.instances = []
    monkeypatch.setattr(uvicorn, "Server", FakeServer)
    monkeypatch.setattr(main, "get_socket", lambda: None)
    monkeypatch.setattr(main, "get_port", lambda: port)
    monkeypatch.setattr(main, "get_port_file", lambda: port_file)
    main.run()
    server = FakeServer.instances[0]
    bound = server.sockets[0]
    try:
        return server.config, bound.getsockname()[1]
    finally:
        bound.close()


def test_run_uses_tcp_with_auto_port_and_port_file(monkeypatch, tmp_path):
    port_file = tmp_path / "port"
    cfg, port = _run_tcp(monkeypatch, 0, str(port_file))
    assert port != 0
    assert cfg.port == port
    assert cfg.host == "127.0.0.1"
    assert port_file.read_text() == f"{port}\n"


def test_run_uses_tcp_without_port_file(monkeypatch):
    cfg, port = _run_tcp(monkeypatch, 0, None)
    assert cfg.port == port
