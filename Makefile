VENV   ?= .venv
PYTHON ?= python3
PY     := $(VENV)/bin/python

MODELS  := models
PRINT   := print
PLATES  := $(wildcard $(PRINT)/*.3mf)
GCODE   := $(patsubst $(PRINT)/%.3mf,$(PRINT)/gcode/%.gcode,$(PLATES))
PROFILES := $(wildcard $(PRINT)/profiles/*.json)

.PHONY: help setup cad plates gcode clean-gcode clean
# slice_jobs.py updates one shared print/gcode/manifest.json
.NOTPARALLEL:

help:
	@echo "make setup   - create $(VENV) with the CAD dependencies"
	@echo "make cad     - regenerate STEP/STL models, previews and fit reports in $(MODELS)/"
	@echo "make plates  - pack the models into centered Qidi X-Plus plates (3MF) in $(PRINT)/"
	@echo "make gcode   - slice every plate with OrcaSlicer into $(PRINT)/gcode/ (not committed)"
	@echo "make $(PRINT)/gcode/<plate>.gcode - slice one plate"
	@echo "make clean-gcode - delete generated G-code"
	@echo "Override slicer detection with ORCA=\"<command>\" and ORCA_MACHINE=<Qidi X-Plus preset .json>."

setup: $(VENV)/.installed

$(VENV)/.installed: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	touch $@

cad: setup
	$(PY) cad/shelf_layout.py

plates: setup
	$(PY) cad/print_jobs.py

gcode: $(GCODE)

$(PRINT)/gcode/%.gcode: $(PRINT)/%.3mf $(PRINT)/manifest.json $(PROFILES) cad/slice_jobs.py
	$(PYTHON) cad/slice_jobs.py $*

clean-gcode:
	rm -rf $(PRINT)/gcode

clean: clean-gcode
	rm -rf $(VENV)
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
