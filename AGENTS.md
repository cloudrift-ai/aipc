# AGENTS.md

Notes for coding agents working in this repo. The design process for every build is in [docs/process.md](docs/process.md).

## Layout

| Path | What it is |
| --- | --- |
| [aipc/](aipc/README.md) | AIPC build: two AI workstations (Berserk, Kenshin) on one rack shelf. Fit prototype; has its own [AGENTS.md](aipc/AGENTS.md) |
| [gpulab/](gpulab/README.md) | GPU lab build: seven mixed GPUs on cabled x8 risers from one H12D-8D, two printed 13-position baseboards. Design; has its own [AGENTS.md](gpulab/AGENTS.md) |
| [hwkit/](hwkit) | Shared Python package: part specs, compatibility, assembly registry, export, renders, plates, printers, slicing, shared component models (`hwkit/components`: Hammond shelf, PCIe posts), and the `hwkit` CLI |
| [hwkit/printers/](hwkit/printers) | Printer definitions (`printer.toml`), vendored OrcaSlicer base presets and shared slicer profiles |
| [docs/](docs) | Shared process and printing guidelines |
| [.claude/skills/](.claude/skills) | Agent skills for every build: `part-intake`, `design-review`, `design-audit` |
| [tests/](tests) | hwkit tests |
| `Makefile`, `pyproject.toml` | Root build: `make setup` creates `venv/` and installs hwkit; every target runs per build |

A build is a folder with a `build.toml` (name, assembly, printer, render sheets and its `[scripts]`). Its `parts/`, `cad/`, `models/`, `print/` and `docs/` belong to that build only. Read the build's own `AGENTS.md` before changing it.

## Commands

Run everything from the repo root. Targets run for every build, or one with `BUILD=<folder>`.

```bash
make setup                  # venv/ with hwkit, CadQuery and dev tools
make all BUILD=aipc         # cad + render + plates + check
make gcode BUILD=aipc       # slice with OrcaSlicer 2.5.x (PLATES="<plate> ..." for some)
make lint test              # ruff and pytest for hwkit
```

Inside a build folder, `../venv/bin/hwkit <cad|plates|render|check|datasheets|slice>` runs one step.

## Rules

- Shared code goes in `hwkit/`; a build's `cad/` holds only that build's geometry and plate layout. Do not copy helpers between builds. Read part dimensions with `spec.dim(id, key)`, never as literals.
- Builds do not share part folders, models or generated files. If a part is used in two builds, give it a part folder in each build.
- Never hand-edit generated files (`models/`, `print/*.3mf`, `parts/*/*/*.step|stl|png|README.md`, `parts/README.md`, `docs/system-check.md` in each build). Change the generator or spec and rerun `make all BUILD=<build>`.
- Changes to `hwkit/` affect every build: run `make lint test` and `make all` for every build, and confirm the generated outputs did not change unless intended.
- Do not loosen a check, add keepouts or disable count checks to hide a mismatch. Fix the geometry or spec.
- G-code, fetched datasheets and `venv/` are generated and gitignored.
- Distinguish evidence everywhere: `measured`, `datasheet` and `standard` are verified; `listing`, `review`, `photo-estimate`, `allowance` and `assumed` are not. A CAD check against coordinates from the same code does not validate those coordinates.
