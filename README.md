# Simple Python Microservice for German Compound-Words Splitting

[![codecov](https://codecov.io/gh/rotdrop/python-microservice-german-word-splitting/graph/badge.svg)](https://codecov.io/gh/rotdrop/python-microservice-german-word-splitting)

A small FastAPI service that splits German compound words into their
components. It wraps

- german_compound_splitter, Copyright 2020 by repodiac, see https://github.com/repodiac for updates and further information
- compound-split (PyPI), a packaging of https://github.com/dtuggener/CharSplit

## Install

### Prerequisites

`make install` (and `make dictionary`) needs `curl`, `7z` and `iconv`.
`iconv` is normally already present. Install the others with your
distribution's package manager:

**Debian / Ubuntu**

```sh
sudo apt install curl 7zip
```

**Fedora / RHEL** (7z is provided by p7zip in EPEL on RHEL)

```sh
sudo dnf install curl p7zip p7zip-plugins
```

**Arch Linux**

```sh
sudo pacman -S curl 7zip
```

**Gentoo**

```sh
sudo emerge --ask net-misc/curl app-arch/7zip
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

This requires `curl`, `7z` and `iconv`, see [Prerequisites](#prerequisites). `make clean` removes `build/` (the downloaded archive and intermediate file) but keeps the virtual environment and the converted dictionary. `make install` records the absolute dictionary path as the default.

## Run

```sh
venv/bin/german-word-splitter
```

## Port

The server port is read from `GERMAN_WORD_SPLITTER_PORT` and defaults to 8000.
`make install PORT=9000` changes the default (the env variable still wins).
Set `GERMAN_WORD_SPLITTER_PORT=0` to let the kernel pick a free port; the chosen
port is written to the file named by `GERMAN_WORD_SPLITTER_PORT_FILE`, which
`php/proxy.php` reads automatically. For a Unix socket, its permission bits
(octal, default 660) are set with `GERMAN_WORD_SPLITTER_SOCKET_MODE`.

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

The optional `transliterate` option takes a target locale (e.g. `de_DE`,
`en_US`); the components are then transliterated accordingly (ä→ae for `de`,
ä→a for other locales, ß→ss). For `german_compound_splitter`, the locale must
be configured in `GERMAN_WORD_SPLITTER_TRANSLITERATION_LOCALES` if
transliteration changes the result, otherwise HTTP 400 is returned. This check
is skipped for `charsplit`.

The word must be given in its original German spelling, not transliterated
(`einkäufe`, not `einkaeufe`). The dictionaries only contain the original
spelling with `ä`, `ö`, `ü` and `ß`, and a transliteration cannot be reliably
reverted without a dictionary. Transliterated words are usually reported as not
splittable.

## Tests

```sh
make test
```

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `GERMAN_WORD_SPLITTER_DICTIONARY` | `$(VENV)/share/german-word-splitter/german_utf8_linux.dic` (set by `make install`) | Dictionary file used by `german_compound_splitter` (created by `make dictionary`). |
| `GERMAN_WORD_SPLITTER_TRANSLITERATION_LOCALES` | empty (no transliteration) | Comma- or whitespace-separated locales, e.g. `de_DE.UTF-8,en_US.UTF-8`, read at dictionary load time. Transliterated spellings of dictionary words then also match, so e.g. *Einkaeufe* (`de`: ä→ae, ö→oe, ü→ue) and *Einkaufe* (other locales such as `en_US`: ä→a, ö→o, ü→u) are split like *Einkäufe*; ß→ss in all locales. Only the language part is evaluated. Returned components keep the original dictionary spelling. |

## systemd service

`make install-service` (uses `sudo`, override with `SUDO=`) installs the service under
`/opt/german-word-splitter` (`PREFIX=`), creates the system user and group
`german-word-splitter`, and installs `contrib/german-word-splitter.service`. Environment
variables are read from `/etc/default/german-word-splitter`, which is created from
`contrib/german-word-splitter.default` if missing. Then:

```sh
sudo systemctl enable --now german-word-splitter
```

`make uninstall-service` reverts all of this: it stops and disables the service and removes the
unit, `/opt/german-word-splitter`, `/etc/default/german-word-splitter` (including local edits),
and the user and group.

### Gentoo

`contrib/gentoo/` contains ebuilds (`acct-group/german-word-splitter`,
`acct-user/german-word-splitter`, live ebuild `app-misc/german-word-splitter-9999`) for a
local overlay. They install the service below `/opt/german-word-splitter`, create the
dedicated user and group, and install the systemd unit with the `systemd` USE flag, or the OpenRC script
`contrib/german-word-splitter.initd` without it. The live
ebuild needs network access during the build (`RESTRICT="network-sandbox"`).

`contrib/gentoo/` is a complete ebuild repository (overlay) named
`german-word-splitter`. `eselect repository add` can only clone a repository
whose root is an overlay, so use a local checkout instead:

```sh
git clone https://github.com/rotdrop/python-microservice-german-word-splitting
sudo eselect repository create german-word-splitter   # creates /var/db/repos/german-word-splitter
sudo rm -rf /var/db/repos/german-word-splitter
sudo ln -s "$PWD/python-microservice-german-word-splitting/contrib/gentoo" /var/db/repos/german-word-splitter
sudo emerge --ask app-misc/german-word-splitter
```

Alternatively use the separate repository `rotdrop/german-word-splitter-gentoo-overlay`,
which the `Gentoo overlay repository` workflow regenerates from `contrib/gentoo`
whenever `main` changes it (the split is deterministic, so it only ever fast-forwards):

```sh
sudo eselect repository add german-word-splitter git https://github.com/rotdrop/german-word-splitter-gentoo-overlay
sudo emerge --sync german-word-splitter
sudo emerge --ask app-misc/german-word-splitter
```

The repository is generated; send changes to this repository instead.

### Debian / Ubuntu package

The Debian source for the package lives in `contrib/debian/` (no binaries are committed).
It targets Debian 13 (Trixie) and Ubuntu 26.04 LTS (Resolute) and needs network access during the build
(dictionary, PyPI and GitHub).

```sh
sudo apt install devscripts equivs dpkg-dev
make deb-build-deps   # installs the build dependencies via mk-build-deps (uses sudo)
make deb              # writes build/deb/german-word-splitter_<version>_<arch>.deb
sudo apt install ./build/deb/german-word-splitter_*.deb
```

The package installs below `/opt/german-word-splitter`, creates the system user and group
`german-word-splitter` (kept on removal), installs the systemd unit and
`/etc/default/german-word-splitter`. `make deb-clean` removes `build/deb/`. The package
version is taken from `contrib/debian/changelog`.

#### Signed apt repository

Release builds for Debian 13 (suite `trixie`) and Ubuntu 26.04 (`resolute`), each for
amd64 and arm64, are published as a signed apt
repository on GitHub Pages by the `APT repository` workflow (on `v*` tags or manual start).
The suite is the distribution codename, because the package bundles a virtual environment tied to the
release's Python. Add the repository with

```sh
make install-apt-source          # uses sudo; supports trixie and resolute (or set APT_SUITE explicitly)
sudo apt update
sudo apt install german-word-splitter
```

or by hand:

```sh
sudo install -d -m 0755 /etc/apt/keyrings
sudo curl -fsSL -o /etc/apt/keyrings/german-word-splitter.asc \
  https://rotdrop.github.io/python-microservice-german-word-splitting/german-word-splitter.asc
sudo tee /etc/apt/sources.list.d/german-word-splitter.sources <<EOF
Types: deb
URIs: https://rotdrop.github.io/python-microservice-german-word-splitting
Suites: $(. /etc/os-release; echo $VERSION_CODENAME)
Components: main
Signed-By: /etc/apt/keyrings/german-word-splitter.asc
EOF
```

`make uninstall-apt-source` removes both files again. The repository is built by
`contrib/apt/build-repo.sh` and needs the repository secret `APT_GPG_PRIVATE_KEY` (a passphrase-less
signing key) and GitHub Pages with the "GitHub Actions" source.

### Fedora / RHEL package

The RPM spec lives in `contrib/rpm/`. Run these on Fedora or RHEL (needs network access during the build):

```sh
sudo dnf install rpm-build dnf-plugins-core
make rpm-build-deps   # dnf builddep (uses sudo)
make rpm              # writes build/rpm/RPMS/<arch>/german-word-splitter-*.rpm
sudo dnf install build/rpm/RPMS/*/german-word-splitter-*.rpm
```

On RHEL, `p7zip` and `p7zip-plugins` come from EPEL. The version is taken from `pyproject.toml`
and must match `Version:` in the spec file. `make rpm-clean` removes `build/rpm/`.

### Arch Linux package

`contrib/arch/PKGBUILD` builds the package with `makepkg` (run as a normal user, needs network access):

```sh
make arch             # writes build/arch/german-word-splitter-*.pkg.tar.zst
sudo pacman -U build/arch/german-word-splitter-*.pkg.tar.zst
```

The system user and group are created via `sysusers.d` (`contrib/german-word-splitter.sysusers`).
`make arch-clean` removes `build/arch/`.

Both packages install the same layout as the Debian package and keep the version in sync with
`pyproject.toml` (update `pkgver` and `Version:` on release).
