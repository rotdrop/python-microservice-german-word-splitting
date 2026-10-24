# Changelog

All notable changes to this project are documented in this file. Entries follow
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and released versions
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-10-24

### Added

- Automatic TCP port selection and configurable Unix socket mode.

## [0.3.0] - 2026-10-24

### Added

- The APT repository and Gentoo overlay retain packages for the three most
  recent releases.

### Changed

- Align the minimum supported Python version and package metadata with the
  Python 3.13+ test matrix.
- Limit signed APT repository builds and setup instructions to Debian Trixie
  and Ubuntu Resolute.

### Fixed

- Use the current `7zip` package names for Debian, Arch Linux and Gentoo.

## [0.2.0] - 2026-10-24

### Added

- Packaging for Debian (`make deb`), RPM, Arch Linux (`make arch`) and Gentoo
  (`contrib/gentoo` overlay with a live ebuild).
- Workflows publishing an APT repository and the Gentoo overlay repository.
- The Gentoo overlay workflow generates an ebuild for the most recent release
  with keywords `~amd64 ~arm64`.
- `CONTRIBUTORS.md`, kept up to date by a workflow.

## [0.1.0] - 2026-10-23

### Added

- FastAPI service with a `POST /split` endpoint for splitting German compound
  words using `compound-split` (`charsplit` method) or `german_compound_splitter`.

### Changed

- `make dictionary` downloads, extracts and converts the Free German Dictionary;
  the default dictionary is now `german_utf8_linux.dic`.

- Restructured into a `src/german_word_splitter` package (api, services,
  backends, config, errors); `app.py` is removed, run
  `uvicorn german_word_splitter.main:app`.
- Backends are created once and cached instead of per request.
- Dictionary path configurable via `GERMAN_WORD_SPLITTER_DICTIONARY`.
- Service errors are mapped to HTTP 400 without leaking internals.

### Added

- pytest suite and README usage documentation.

## Release numbering

- **MAJOR** versions include incompatible API changes.
- **MINOR** versions add functionality in a backward-compatible manner.
- **PATCH** versions include backward-compatible bug fixes.

Before a release, move the relevant changes from `Unreleased` into a dated
version section.
