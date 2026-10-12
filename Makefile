PYTHON := .venv/bin/python

.PHONY: all fetch load sql cox export figures test

all: load sql cox export figures

fetch:
	$(PYTHON) src/fetch.py

load:
	$(PYTHON) src/load.py

sql:
	$(PYTHON) src/run_sql.py

cox:
	$(PYTHON) src/cox.py

export:
	$(PYTHON) src/export.py

figures:
	$(PYTHON) src/figures.py

test:
	$(PYTHON) -m pytest
