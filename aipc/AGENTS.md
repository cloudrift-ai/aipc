# AGENTS.md

Notes for coding agents working on the AIPC build. Paths are relative to this `aipc/` folder. Run `make <target> BUILD=aipc` from the repo root. Read the repo's [AGENTS.md](../AGENTS.md) first; the full workflow is in [docs/process.md](../docs/process.md).

## Process rules

1. **Parts come from the shared library.** Each part's spec is in the repo's [parts/](../parts/README.md) library (`part.toml`, generated `README.md`, datasheets, model). This build references the ones it uses with `parts/<id>.toml` (quantity, role, status, systems, assembly mapping, build-specific overrides). Use the `part-intake` skill to add or change a part.
2. **Render and inspect every part** (`make render`, then look at `render.png`). Use the `design-review` skill.
3. **Everything is modeled in one assembly** and inspected (`models/renders/`, `models/renders/parts/<id>.png`). `make cad` fails if an assembly instance matches no referenced part, or a part is missing from the assembly without a `not_modeled` reason.
4. **Check whole-system compatibility from the datasheets before choosing a part** (`make check`, [docs/system-check.md](docs/system-check.md)). Resolve FAILs before buying; report BLOCKED items as open questions.

## Code rules

- Generators in `cad/`, the library specs in `../parts/*/*/part.toml` and this build's `parts/*.toml` are the source of truth. Never hand-edit generated files: `models/`, `print/*.3mf`, `parts/*.md`, `docs/system-check.md`, and the library's `README.md`, `*.step`, `*.stl` and `render.png`. Change the script or spec and run `make all` (then `make gcode` if OrcaSlicer is installed).
- Use the shared [hwkit](../hwkit) package (spec lookup, export, assembly registry, rendering, compatibility, plates, printers) instead of writing new helpers. Put code that another build could use into hwkit, not into `cad/`. Read part dimensions with `spec.dim(id, key)`, never as literals.
- `cad/shelf_layout.py` asserts on collisions, fastener access and slot travel; `hwkit.registry` asserts on assembly coverage. Fix the geometry or spec when an assertion fails; do not loosen the check, add keepouts or disable count checks to hide a mismatch.
- The motherboard mount sections and the PSU bracket are built in `hwkit/components/atx_mobo_mount.py` and `atx_psu_bracket.py`, because gpulab reuses them. AIPC owns and exports their library models; a change there changes gpulab too, so run `make all` for both builds.
- Keep one model per unique printed part. Identical copies share a model; the quantity lives in `parts/<name>.toml`, and `export_print(...)` and the plate `copies` in `cad/print_jobs.py` must agree with it.
- Every printable change follows the required steps in the root [AGENTS.md](../AGENTS.md#3d-printed-parts-required-steps), including the independent print audit, plus the AIPC notes in [print/README.md](print/README.md). Use the `design-audit` skill for a full design audit.
- G-code and fetched datasheets are generated and gitignored. Do not commit `print/gcode/` or the library's `parts/*/*/datasheets/`.
- Distinguish evidence: `measured`, `datasheet` and `standard` are verified; `listing`, `review`, `photo-estimate`, `allowance` and `assumed` are not. Mark unmeasured interfaces as provisional in docs and reports. A CAD check against coordinates from the same code does not validate those coordinates.
- Keep [parts.xlsx](parts.xlsx) to parts the build actually uses, and keep it in step with `parts/`; update it and the docs when hardware changes.
