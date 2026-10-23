# Simple Python Microservice for German Compound-Words Splitting

A small FastAPI service that splits German compound words into their
components. It wraps

- german_compound_splitter, Copyright 2020 by repodiac, see https://github.com/repodiac for updates and further information
- compound-split (PyPI), a packaging of https://github.com/dtuggener/CharSplit

## Install

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

To remove the virtual environment and dictionary files:

```sh
make uninstall
```

Leave the environment with `deactivate`.

### pipx

The package has no console script of its own, so run `uvicorn` from an
isolated pipx environment:

```sh
pipx run --spec . uvicorn german_word_splitter.main:app
```

Or install it persistently and expose `uvicorn` from its dependencies:

```sh
pipx install --include-deps .
uvicorn german_word_splitter.main:app
```

## Dictionary

`german_compound_splitter` needs an external dictionary. Download the
[Free German Dictionary](https://sourceforge.net/projects/germandict/files/latest/download),
extract it and convert it to UTF-8 with Unix line breaks (`german_utf8_linux.dic`):

```sh
make dictionary
```

This requires `curl`, `7z` (p7zip) and `iconv`. `make clean-dictionary` removes the dictionary files.

## Run

```sh
uvicorn german_word_splitter.main:app --reload
```

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
pytest
```

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `GERMAN_WORD_SPLITTER_DICTIONARY` | `german_utf8_linux.dic` | Dictionary file used by `german_compound_splitter` (created by `make dictionary`). |

## Migration notes

`app.py` was removed; use `german_word_splitter.main:app` instead.
