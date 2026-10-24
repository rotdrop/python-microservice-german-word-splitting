# Simple Python Microservice for German Compound-Words Splitting

[![codecov](https://codecov.io/gh/rotdrop/python-microservice-german-word-splitting/graph/badge.svg)](https://codecov.io/gh/rotdrop/python-microservice-german-word-splitting)

A small FastAPI service that splits German compound words into their
components. It wraps

- german_compound_splitter, Copyright 2020 by repodiac, see https://github.com/repodiac for updates and further information
- compound-split (PyPI), a packaging of https://github.com/dtuggener/CharSplit

## Install

### Prerequisites

`make install` (and `make dictionary`) needs `curl`, `7z` (p7zip) and `iconv`.
`iconv` is normally already present. Install the others with your
distribution's package manager:

**Debian / Ubuntu**

```sh
sudo apt install curl p7zip-full
```

**Fedora / RHEL** (7z is provided by p7zip in EPEL on RHEL)

```sh
sudo dnf install curl p7zip p7zip-plugins
```

**Arch Linux**

```sh
sudo pacman -S curl p7zip
```

**Gentoo**

```sh
sudo emerge --ask net-misc/curl app-arch/p7zip
```

### Virtual environment

```sh
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[test]"
```

Or in one step, which also builds the dictionary (see below):

```sh
make install
```

To create the virtual environment with access to system-installed Python
packages, use:

```sh
make venv SYSTEM_SITE_PACKAGES=1
```

This option applies when the environment is created. Run `make uninstall`
first to recreate an existing environment with a different setting.

The virtual environment lives in `venv` by default; use `make install VENV=/path/to/env`
to put it elsewhere (pass the same `VENV` to every `make` call).

To remove the virtual environment, dictionary and `build/`:

```sh
make uninstall
```

Leave the environment with `deactivate`.

### pipx

Run the service from an isolated pipx environment:

```sh
pipx run --spec . german-word-splitter
```

Or install it persistently:

```sh
pipx install --include-deps .
german-word-splitter
```

## Dictionary

`german_compound_splitter` needs an external dictionary. Download the
[Free German Dictionary](https://sourceforge.net/projects/germandict/files/latest/download),
extract it and convert it to UTF-8 with Unix line breaks (`german_utf8_linux.dic`).
The download and extraction happen in `build/`; the converted dictionary is stored in
`$(VENV)/share/german-word-splitter/` (`venv/share/german-word-splitter/` by default):

```sh
make dictionary
```

This requires `curl`, `7z` (p7zip) and `iconv`, see [Prerequisites](#prerequisites). `make clean` removes `build/` (the downloaded archive and intermediate file) but keeps the virtual environment and the converted dictionary. `make install` records the absolute dictionary path as the default.

## Run

```sh
venv/bin/german-word-splitter
```

## Port

The server port is read from `GERMAN_WORD_SPLITTER_PORT` and defaults to 8000.
`make install PORT=9000` changes the default (the env variable still wins).

## Unix domain socket

As an alternative to TCP, enable a default Unix socket during installation:

```sh
make install SOCKET=1
python -m german_word_splitter.main
curl --unix-socket venv/run/german-word-splitter.sock http://localhost/docs
```

This creates `venv/run` and sets the default socket path to
`venv/run/german-word-splitter.sock`. The `GERMAN_WORD_SPLITTER_SOCKET`
environment variable overrides the default.

Or directly with uvicorn: `uvicorn german_word_splitter.main:app --uds /path/to.sock`.

## API

`POST /split` with `word` and optional `method` (`charsplit` (default) or
`german_compound_splitter`).

```sh
curl -X POST http://127.0.0.1:8000/split \
  -H 'Content-Type: application/json' \
  -d '{"word": "Haustür", "method": "charsplit"}'
```

```json
{"word": "Haustür", "splittable": true, "components": ["Haus", "Tür"]}
```

An empty word or unknown method yields HTTP 400.

## Tests

```sh
make test
```

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `GERMAN_WORD_SPLITTER_DICTIONARY` | `$(VENV)/share/german-word-splitter/german_utf8_linux.dic` (set by `make install`) | Dictionary file used by `german_compound_splitter` (created by `make dictionary`). |

## systemd service

`make install-service` (uses `sudo`, override with `SUDO=`) installs the service under
`/opt/german-word-splitter` (`PREFIX=`), creates the system user and group
`german-word-splitter`, and installs `contrib/german-word-splitter.service`. Environment
variables are read from `/etc/default/german-word-splitter`, which is created from
`contrib/german-word-splitter.default` if missing. Then:

```sh
sudo systemctl enable --now german-word-splitter
```
