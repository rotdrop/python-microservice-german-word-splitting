import importlib

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


def test_run_uses_socket(monkeypatch):
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(kw))
    monkeypatch.setattr(main, "get_socket", lambda: "/tmp/s.sock")
    main.run()
    assert calls == [{"uds": "/tmp/s.sock"}]


def test_run_uses_tcp(monkeypatch):
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(kw))
    monkeypatch.setattr(main, "get_socket", lambda: None)
    monkeypatch.setattr(main, "get_port", lambda: 1234)
    main.run()
    assert calls == [{"host": "127.0.0.1", "port": 1234}]
