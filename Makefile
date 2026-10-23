DICT_URL := https://sourceforge.net/projects/germandict/files/latest/download
DICT_7Z := german.dic.7z
DICT_RAW := german.dic
DICT_UTF8 := german_utf8_linux.dic

VENV := venv
PYTHON ?= python3

.PHONY: install venv dictionary clean-dictionary

# Create the virtual environment, install the package with test extras and fetch the dictionary.
install: venv dictionary

venv: $(VENV)/.installed

$(VENV)/.installed: pyproject.toml
	$(PYTHON) -m venv $(VENV)
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

clean-dictionary:
	rm -f $(DICT_7Z) $(DICT_RAW) $(DICT_UTF8)
