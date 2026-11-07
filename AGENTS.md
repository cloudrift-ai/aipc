# AGENTS.md

Notes for coding agents working in this repo. The full workflow is in [docs/process.md](docs/process.md).

## Process rules

1. **One folder per part.** Every purchased, printed and fabricated part has `parts/<category>/<id>/` with `part.toml` (evidence-tagged dimensions and interfaces), a generated `README.md`, its datasheets (`make datasheets`) and the model used in the assembly. Use the `part-intake` skill to add or change a part.
2. **Render and inspect every part** (`make render`, then look at `render.png`). Use the `design-review` skill.
3. **Everything is modeled in one assembly** and inspected (`models/renders/`, `in-assembly.png`). `make cad` fails if an assembly instance has no part folder, or a part is missing from the assembly without a `not_modeled` reason.
4. **Check whole-system compatibility from the datasheets before choosing a part** (`make check`, [docs/system-check.md](docs/system-check.md)). Resolve FAILs before buying; report BLOCKED items as open questions.

## Code rules

- Generators in `cad/` and specs in `parts/*/*/part.toml` are the source of truth. Never hand-edit generated files: `models/`, `print/*.3mf`, `parts/*/*/*.step|stl|png|README.md`, `parts/README.md`, `docs/system-check.md`. Change the script or spec and run `make all` (then `make gcode` if OrcaSlicer is installed).
- Use the shared library `cad/aipc/` (spec lookup, export, assembly registry, rendering, compatibility) instead of writing new helpers. Read part dimensions with `spec.dim(id, key)`, never as literals.
- `cad/shelf_layout.py` asserts on collisions, fastener access and slot travel; `aipc.registry` asserts on assembly coverage. Fix the geometry or spec when an assertion fails; do not loosen the check, add keepouts or disable count checks to hide a mismatch.
- Keep one model per unique printed part. Identical copies share a model; the quantity lives in `part.toml`, and `export_print(...)` and the plate `copies` in `cad/print_jobs.py` must agree with it.
- Follow [docs/printing.md](docs/printing.md) for every printable change, including the independent print audit before release. Use the `design-audit` skill for a full design audit.
- G-code and fetched datasheets are generated and gitignored. Do not commit `print/gcode/` or `parts/*/*/datasheets/`.
- Distinguish evidence: `measured`, `datasheet` and `standard` are verified; `listing`, `photo-estimate`, `allowance` and `assumed` are not. Mark unmeasured interfaces as provisional in docs and reports. A CAD check against coordinates from the same code does not validate those coordinates.
- Keep [parts.xlsx](parts.xlsx) to parts the build actually uses, and keep it in step with `parts/`; update it and the docs when hardware changes.
