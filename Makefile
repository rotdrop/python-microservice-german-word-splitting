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
VENV_OPTIONS := $(if $(filter 1 true yes,$(SYSTEM_SITE_PACKAGES)),--system-site-packages,)

.PHONY: port socket dictionary-default install venv test dictionary uninstall clean help

# Create the virtual environment, install the package with test extras and fetch the dictionary.
install: venv dictionary dictionary-default port socket

help:
	@printf '%s\n' \
		'Available targets:' \
		'  install      Create the virtual environment, fetch the dictionary, and configure defaults.' \
		'  venv         Create the virtual environment and install the package with test extras.' \
		'  test         Run the test suite.' \
		'  dictionary   Download and convert the German dictionary.' \
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
