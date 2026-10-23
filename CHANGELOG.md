# Changelog

All notable changes to this project are documented in this file. Entries follow
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and released versions
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- FastAPI service with a `POST /split` endpoint for splitting German compound
  words using `charsplit` or `german_compound_splitter`.

## Release numbering

- **MAJOR** versions include incompatible API changes.
- **MINOR** versions add functionality in a backward-compatible manner.
- **PATCH** versions include backward-compatible bug fixes.

Before a release, move the relevant changes from `Unreleased` into a dated
version section.
