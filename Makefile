DICT_URL := https://sourceforge.net/projects/germandict/files/latest/download
DICT_7Z := german.dic.7z
DICT_RAW := german.dic
DICT_UTF8 := german_utf8_linux.dic

VENV := venv
PYTHON ?= python3
SYSTEM_SITE_PACKAGES ?= 0
PORT_FILE := src/german_word_splitter/_default_port.py
SOCKET_FILE := src/german_word_splitter/_default_socket.py
SOCKET_PATH := $(VENV)/run/german-word-splitter.sock
VENV_OPTIONS := $(if $(filter 1 true yes,$(SYSTEM_SITE_PACKAGES)),--system-site-packages,)

.PHONY: port socket install venv test dictionary uninstall clean-dictionary

# Create the virtual environment, install the package with test extras and fetch the dictionary.
install: venv dictionary port socket

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

$(DICT_7Z):
	curl -fL -o $@ "$(DICT_URL)"

$(DICT_RAW): $(DICT_7Z)
	7z x -y $(DICT_7Z) $(DICT_RAW)

$(DICT_UTF8): $(DICT_RAW)
	iconv -f ISO_8859-15 -t UTF-8 $(DICT_RAW) | tr -d '\r' > $@
	rm -f $(DICT_7Z) $(DICT_RAW)

clean-dictionary:
	rm -f $(DICT_7Z) $(DICT_RAW) $(DICT_UTF8)

# Remove the virtual environment and the downloaded/converted dictionary files.
uninstall: clean-dictionary
	rm -rf $(VENV) $(PORT_FILE) $(SOCKET_FILE)
