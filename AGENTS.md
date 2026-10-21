# AGENTS.md

Notes for coding agents working in this repo.

- Generators in `cad/` are the source of truth. Never hand-edit files in `models/` or `print/*.3mf`; change the script and run `make cad plates` (then `make gcode` if OrcaSlicer is installed).
- `cad/shelf_layout.py` asserts on collisions, fastener access and slot travel. Fix the geometry when an assertion fails; do not loosen the check.
- Keep one model per unique printed part. Identical copies share a model; quantities go in `export_print(...)` and the plate `copies` in `cad/print_jobs.py`.
- Follow [docs/printing.md](docs/printing.md) for every printable change, including the independent print audit before release.
- G-code is generated and gitignored. Do not commit `print/gcode/`.
- Distinguish manufacturer drawings, photo estimates and real measurements; mark unmeasured interfaces as provisional in docs and reports. A CAD check against coordinates from the same code does not validate those coordinates.
- Keep [parts.xlsx](parts.xlsx) to parts the build actually uses; update it and the docs when hardware changes.
