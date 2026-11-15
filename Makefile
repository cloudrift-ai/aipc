# Hardware builds: one folder per build (a folder with build.toml), shared tooling in hwkit/.
# Targets run for every build, or for one with BUILD=<folder>, e.g. `make all BUILD=aipc`.

PYTHON ?= python3.13
VENV   := venv
HWKIT  := $(CURDIR)/$(VENV)/bin/hwkit
BUILDS := $(patsubst %/build.toml,%,$(wildcard */build.toml))
BUILD  ?= $(BUILDS)

# Runs `hwkit <command>` in each selected build folder.
define hwkit
	@for b in $(BUILD); do echo "== $$b: hwkit $(1)"; (cd $$b && $(HWKIT) $(1)) || exit 1; done
endef

.PHONY: help setup lint format test all cad render check datasheets plates gcode clean-gcode clean
# The slicer updates one shared print/gcode/manifest.json per build.
.NOTPARALLEL:

help:
	@echo "Builds: $(BUILDS)   (select one with BUILD=<folder>; default: all)"
	@echo ""
	@echo "make setup       - create $(VENV)/ and install hwkit with its CAD and dev dependencies"
	@echo "make lint        - ruff check and format check of hwkit/ and tests/"
	@echo "make format      - ruff format and autofix hwkit/ and tests/"
	@echo "make test        - run the hwkit tests"
	@echo "make all         - cad + render + plates + check (everything except G-code)"
	@echo "make cad         - regenerate the assembly, reports and every part model"
	@echo "make render      - render every part and the assembly for visual inspection"
	@echo "make check       - spec lint, system compatibility, assembly coverage; writes docs/system-check.md"
	@echo "make datasheets  - download the datasheets of each build's parts into parts/*/*/datasheets/ (not committed)"
	@echo "make plates      - pack the printed parts into print plates (3MF) in print/"
	@echo "make gcode       - slice the plates with OrcaSlicer into print/gcode/ (not committed); PLATES=\"<plate> ...\" for some"
	@echo "make clean-gcode - delete generated G-code"
	@echo "Override slicer detection with ORCA=\"<command>\" (OrcaSlicer 2.5.x; base presets vendored in hwkit/printers/)."

setup: $(VENV)/.setup-complete

# The marker lives inside the venv, so an interrupted install never looks complete.
$(VENV)/.setup-complete: pyproject.toml
	@if [ ! -x "$(VENV)/bin/python" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv --prompt aipc $(VENV); \
	fi
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"
	@touch $@

lint: setup
	$(VENV)/bin/ruff check hwkit tests
	$(VENV)/bin/ruff format --check hwkit tests

format: setup
	$(VENV)/bin/ruff check --fix hwkit tests
	$(VENV)/bin/ruff format hwkit tests

test: setup
	$(VENV)/bin/pytest

all: cad render plates check

cad: setup
	$(call hwkit,cad)

render: setup
	$(call hwkit,render)

check: setup
	$(call hwkit,check)

datasheets: setup
	$(call hwkit,datasheets)

plates: setup
	$(call hwkit,plates)

gcode: setup
	$(call hwkit,slice $(PLATES))

clean-gcode:
	rm -rf $(addsuffix /print/gcode,$(BUILD))

clean: clean-gcode
	rm -rf $(VENV)
	find . -name __pycache__ -type d -prune -not -path "./$(VENV)/*" -exec rm -rf {} +
