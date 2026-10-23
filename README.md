# Simple Python Microservice for German Compound-Words Splitting

A small FastAPI service that splits German compound words into their
components. It wraps

- german_compound_splitter, Copyright 2020 by repodiac, see https://github.com/repodiac for updates and further information
- https://github.com/dtuggener/CharSplit.git

## Install

```sh
pip install -e ".[test]"
```

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
| `GERMAN_WORD_SPLITTER_DICTIONARY` | `german.dic` | Dictionary file used by `german_compound_splitter`. |

## Migration notes

`app.py` was removed; use `german_word_splitter.main:app` instead.
