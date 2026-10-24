DICT_URL := https://sourceforge.net/projects/germandict/files/latest/download
.DEFAULT_GOAL := help

VENV ?= venv
DICT_DIR := $(VENV)/share/german-word-splitter
BUILD_DIR := build
DICT_7Z := $(BUILD_DIR)/german.dic.7z
DICT_RAW := $(BUILD_DIR)/german.dic
DICT_UTF8 := $(DICT_DIR)/german_utf8_linux.dic
DICT_FILE := src/german_word_splitter/_default_dictionary.py
PYTHON ?= python3
SYSTEM_SITE_PACKAGES ?= 0
PORT_FILE := src/german_word_splitter/_default_port.py
SOCKET_FILE := src/german_word_splitter/_default_socket.py
SOCKET_PATH := $(VENV)/run/german-word-splitter.sock
PREFIX ?= /opt/german-word-splitter
SERVICE_NAME := german-word-splitter
SERVICE_USER ?= german-word-splitter
SERVICE_GROUP ?= german-word-splitter
SUDO ?= sudo
SYSTEMD_DIR ?= /etc/systemd/system
DEFAULTS_DIR ?= /etc/default
DEB_DIR := $(BUILD_DIR)/deb
DEB_VERSION = $(shell sed -n '1s/^[^(]*(\([^)]*\)).*/\1/p' contrib/debian/changelog)
DEB_SRC = $(DEB_DIR)/$(SERVICE_NAME)-$(DEB_VERSION)
PKG_VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
RPM_DIR := $(BUILD_DIR)/rpm
ARCH_DIR := $(BUILD_DIR)/arch
APT_URI ?= https://rotdrop.github.io/python-microservice-german-word-splitting
APT_SUITE ?= $(shell . /etc/os-release; echo $$VERSION_CODENAME)
APT_SUPPORTED_SUITES := trixie resolute
APT_KEYRING_DIR ?= /etc/apt/keyrings
APT_SOURCES_DIR ?= /etc/apt/sources.list.d
VENV_OPTIONS := $(if $(filter 1 true yes,$(SYSTEM_SITE_PACKAGES)),--system-site-packages,)

.PHONY: port socket dictionary-default install venv test dictionary uninstall clean help install-service uninstall-service deb-build-deps deb deb-clean rpm-build-deps rpm rpm-clean arch arch-clean install-apt-source uninstall-apt-source

# Create the virtual environment, install the package with test extras and fetch the dictionary.
install: venv dictionary dictionary-default port socket

help:
	@printf '%s\n' \
		'Available targets:' \
		'  install      Create the virtual environment, fetch the dictionary, and configure defaults.' \
		'  venv         Create the virtual environment and install the package with test extras.' \
		'  test         Run the test suite.' \
		'  dictionary   Download and convert the German dictionary.' \
		'  install-service  Install the systemd service under $(PREFIX) (uses sudo; see SUDO, PREFIX).' \
		'  uninstall-service  Revert install-service: remove unit, $(PREFIX), defaults file, user and group (uses sudo).' \
		'  deb-build-deps   Install the Debian build dependencies with mk-build-deps (uses sudo).' \
		'  deb              Build the Debian package from contrib/debian into $(DEB_DIR)/.' \
		'  deb-clean        Remove $(DEB_DIR)/.' \
		'  rpm-build-deps   Install the RPM build dependencies with dnf (Fedora/RHEL, uses sudo).' \
		'  rpm              Build the RPM from contrib/rpm into $(RPM_DIR)/.' \
		'  rpm-clean        Remove $(RPM_DIR)/.' \
		'  arch             Build the Arch Linux package from contrib/arch into $(ARCH_DIR)/ (makepkg).' \
		'  arch-clean       Remove $(ARCH_DIR)/.' \
		'  install-apt-source    Add the project apt repository for Debian trixie or Ubuntu resolute (uses sudo).' \
		'  uninstall-apt-source  Remove the apt repository configuration and key again.' \
		'  uninstall    Remove the virtual environment and dictionary files.' \
		'  clean        Remove the build/ directory with the download artifacts; keeps the virtual environment.' \
				'  port         Set the default port with PORT=<port> (for example, make install PORT=9000).' \
		'  socket       Configure the default Unix socket when SOCKET=1.' \
		'' \
		'Options:' \
		'  make install VENV=<dir>' \
		'      Use <dir> instead of venv for the virtual environment (default: venv).' \
		'      The converted dictionary is stored in <dir>/share/german-word-splitter/.' \
		'      Pass the same VENV to every make invocation.' \
		'  make install SOCKET=1' \
		'      Enable the Unix socket at venv/run/german-word-splitter.sock.' \
		'  make venv SYSTEM_SITE_PACKAGES=1' \
		'      Create the virtual environment with access to system-installed Python packages.' \
		'      This setting applies only when creating the environment; run make uninstall first to change it.'

# Record the default port if PORT is given (e.g. make install PORT=9000).
port:
	$(if $(PORT),echo "DEFAULT_PORT = $(PORT)" > $(PORT_FILE),@true)

# Record a default Unix socket path if SOCKET is enabled.
socket:
	$(if $(filter 1 true yes,$(SOCKET)),mkdir -p $(VENV)/run && echo 'DEFAULT_SOCKET = "$(SOCKET_PATH)"' > $(SOCKET_FILE),rm -f $(SOCKET_FILE))

venv: $(VENV)/.installed

test: venv
	$(VENV)/bin/pytest

$(VENV)/.installed: pyproject.toml
	$(PYTHON) -m venv $(VENV_OPTIONS) $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[test]"
	touch $@

# Download the Free German Dictionary and convert it to UTF-8 with Unix line breaks.
dictionary: $(DICT_UTF8)

$(DICT_DIR) $(BUILD_DIR):
	mkdir -p $@

$(DICT_7Z): | $(BUILD_DIR)
	curl -fL -o $@ "$(DICT_URL)"

$(DICT_RAW): $(DICT_7Z)
	7z x -y -o$(BUILD_DIR) $(DICT_7Z) $(notdir $(DICT_RAW))
	touch $@

# Order-only: the converted dictionary is not rebuilt after make clean.
$(DICT_UTF8): | $(DICT_DIR) $(DICT_RAW)
	iconv -f ISO_8859-15 -t UTF-8 $(DICT_RAW) | tr -d '\r' > $@

# Record the absolute dictionary path as default for the application.
dictionary-default:
	echo 'DEFAULT_DICTIONARY = "$(abspath $(DICT_UTF8))"' > $(DICT_FILE)

# Remove the build directory (download artifacts); the virtual environment is kept.
clean:
	rm -rf $(BUILD_DIR)

# Remove the virtual environment and the generated default files.
uninstall: clean
	rm -rf $(VENV) $(PORT_FILE) $(SOCKET_FILE) $(DICT_FILE)

# Install the service under $(PREFIX) with a dedicated user and group, and register the systemd unit.
# An existing $(DEFAULTS_DIR)/$(SERVICE_NAME) is never overwritten.
install-service: $(DICT_UTF8)
	$(SUDO) getent group $(SERVICE_GROUP) >/dev/null || $(SUDO) groupadd --system $(SERVICE_GROUP)
	$(SUDO) getent passwd $(SERVICE_USER) >/dev/null || $(SUDO) useradd --system --gid $(SERVICE_GROUP) \
		--home-dir $(PREFIX) --no-create-home --shell /usr/sbin/nologin $(SERVICE_USER)
	$(SUDO) install -d -m 0755 $(PREFIX) $(PREFIX)/share
	$(SUDO) $(PYTHON) -m venv $(PREFIX)/venv
	$(SUDO) $(PREFIX)/venv/bin/pip install --upgrade pip .
	$(SUDO) install -m 0644 $(DICT_UTF8) $(PREFIX)/share/
	$(SUDO) install -m 0644 contrib/$(SERVICE_NAME).service $(SYSTEMD_DIR)/$(SERVICE_NAME).service
	$(SUDO) sed -i -e 's|^User=.*|User=$(SERVICE_USER)|' -e 's|^Group=.*|Group=$(SERVICE_GROUP)|' \
		-e 's|^ExecStart=.*|ExecStart=$(PREFIX)/venv/bin/german-word-splitter|' $(SYSTEMD_DIR)/$(SERVICE_NAME).service
	test -e $(DEFAULTS_DIR)/$(SERVICE_NAME) || { \
		$(SUDO) install -m 0644 contrib/$(SERVICE_NAME).default $(DEFAULTS_DIR)/$(SERVICE_NAME) && \
		$(SUDO) sed -i 's|^#\(GERMAN_WORD_SPLITTER_DICTIONARY=\).*|\1$(PREFIX)/share/$(notdir $(DICT_UTF8))|' $(DEFAULTS_DIR)/$(SERVICE_NAME); }
	$(SUDO) systemctl daemon-reload
	@echo "Installed. Enable with: $(SUDO) systemctl enable --now $(SERVICE_NAME)"

# Revert install-service. Removes $(DEFAULTS_DIR)/$(SERVICE_NAME), including local edits.
uninstall-service:
	-$(SUDO) systemctl disable --now $(SERVICE_NAME)
	$(SUDO) rm -f $(SYSTEMD_DIR)/$(SERVICE_NAME).service $(DEFAULTS_DIR)/$(SERVICE_NAME)
	$(SUDO) systemctl daemon-reload
	$(SUDO) rm -rf -- $(PREFIX)
	if getent passwd $(SERVICE_USER) >/dev/null; then $(SUDO) userdel $(SERVICE_USER); fi
	if getent group $(SERVICE_GROUP) >/dev/null; then $(SUDO) groupdel $(SERVICE_GROUP); fi

# Install the build dependencies listed in contrib/debian/control (needs devscripts and equivs).
deb-build-deps:
	mkdir -p $(DEB_DIR)
	cd $(DEB_DIR) && mk-build-deps --install --remove --root-cmd $(SUDO) \
		--tool 'apt-get -y --no-install-recommends' $(CURDIR)/contrib/debian/control

# Build the Debian package from a copy of the source tree and contrib/debian. Needs network access.
deb:
	rm -rf $(DEB_SRC)
	mkdir -p $(DEB_SRC)
	git ls-files -z --cached --others --exclude-standard | tar --null -T - -cf - | tar -xf - -C $(DEB_SRC)
	cp -r contrib/debian $(DEB_SRC)/debian
	cd $(DEB_SRC) && dpkg-buildpackage -us -uc -b
	@ls $(DEB_DIR)/*.deb

deb-clean:
	rm -rf $(DEB_DIR)

# Source tarball of the tracked and unignored files, as expected by the RPM and Arch packages.
define source_tarball
mkdir -p $(dir $(1))
git ls-files -z --cached --others --exclude-standard | tar --null -T - --transform 's|^|$(SERVICE_NAME)-$(PKG_VERSION)/|' -czf $(1)
endef

# Install the build dependencies listed in the spec file (needs dnf-plugins-core).
rpm-build-deps:
	$(SUDO) dnf builddep -y contrib/rpm/$(SERVICE_NAME).spec

# Build the RPM from contrib/rpm/. The version is taken from pyproject.toml and must match the spec file. Needs network access.
rpm:
	rm -rf $(RPM_DIR)
	$(call source_tarball,$(RPM_DIR)/SOURCES/$(SERVICE_NAME)-$(PKG_VERSION).tar.gz)
	rpmbuild -bb --define '_topdir $(abspath $(RPM_DIR))' contrib/rpm/$(SERVICE_NAME).spec
	@ls $(RPM_DIR)/RPMS/*/*.rpm

rpm-clean:
	rm -rf $(RPM_DIR)

# Build the Arch Linux package from contrib/arch/PKGBUILD. Needs network access; run as a normal user.
arch:
	rm -rf $(ARCH_DIR)
	$(call source_tarball,$(ARCH_DIR)/$(SERVICE_NAME)-$(PKG_VERSION).tar.gz)
	cp contrib/arch/PKGBUILD $(ARCH_DIR)/
	cd $(ARCH_DIR) && makepkg -sf
	@ls $(ARCH_DIR)/*.pkg.tar.*

arch-clean:
	rm -rf $(ARCH_DIR)

# Register the signed apt repository for Debian trixie or Ubuntu resolute (deb822 format).
install-apt-source:
	@case " $(APT_SUPPORTED_SUITES) " in *" $(APT_SUITE) "*) ;; \
		*) echo "Unsupported APT suite '$(APT_SUITE)'; supported suites: $(APT_SUPPORTED_SUITES)" >&2; exit 1;; esac
	$(SUDO) install -d -m 0755 $(APT_KEYRING_DIR) $(APT_SOURCES_DIR)
	curl -fsSL $(APT_URI)/$(SERVICE_NAME).asc | $(SUDO) tee $(APT_KEYRING_DIR)/$(SERVICE_NAME).asc >/dev/null
	printf '%s\n' 'Types: deb' 'URIs: $(APT_URI)' 'Suites: $(APT_SUITE)' 'Components: main' \
		'Signed-By: $(APT_KEYRING_DIR)/$(SERVICE_NAME).asc' \
		| $(SUDO) tee $(APT_SOURCES_DIR)/$(SERVICE_NAME).sources >/dev/null
	@echo "Now run: $(SUDO) apt update && $(SUDO) apt install $(SERVICE_NAME)"

uninstall-apt-source:
	$(SUDO) rm -f $(APT_SOURCES_DIR)/$(SERVICE_NAME).sources $(APT_KEYRING_DIR)/$(SERVICE_NAME).asc
