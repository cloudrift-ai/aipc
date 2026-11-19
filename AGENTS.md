# AGENTS.md

Notes for coding agents working in this repo. This file is the single list of required steps and rules for every build; [docs/process.md](docs/process.md) explains the design process behind them, [docs/printing.md](docs/printing.md) holds the printing guidelines the print auditor uses, and the skills in [.claude/skills/](.claude/skills) give the detailed procedures.

## Layout

| Path | What it is |
| --- | --- |
| [aipc/](aipc/README.md) | AIPC build: two AI workstations (Berserk, Kenshin) on one rack shelf. Fit prototype |
| [gpulab/](gpulab/README.md) | GPU lab build: seven mixed GPUs on cabled x8 risers from one H12D-8D, two printed 13-position baseboards. Design |
| [parts/](parts/README.md) | Shared parts library: one folder per part with its spec (`part.toml`), generated README, model, render and fetched datasheets. Builds only reference it |
| [hwkit/](hwkit) | Shared Python package: part specs, compatibility, assembly registry, export, renders, plates, printers, slicing, shared component models (`hwkit/components`: Hammond shelf, PCIe posts, the AIPC motherboard mount and PSU bracket), and the `hwkit` CLI |
| [hwkit/printers/](hwkit/printers) | Printer definitions (`printer.toml`), vendored OrcaSlicer base presets and shared slicer profiles |
| [docs/](docs) | Shared process and printing guidelines |
| [.claude/skills/](.claude/skills) | Agent skills for every build: `part-intake`, `design-review`, `design-audit` |
| [tests/](tests) | hwkit tests |
| `Makefile`, `pyproject.toml` | Root build: `make setup` creates `venv/` and installs hwkit; every target runs per build |

A build is a folder with a `build.toml` (name, assembly, printer, render sheets and its `[scripts]`). Its `cad/`, `models/`, `print/` and `docs/` belong to that build only. Its `parts/` holds one `<id>.toml` per part it uses: a reference to the library spec plus the build's quantity, role, status, systems, assembly mapping and any build-specific dims or interface changes (schema in [hwkit/spec.py](hwkit/spec.py)). Each build's own notes are under [Build notes](#build-notes) below; there are no per-build agent files.

## Commands

Run everything from the repo root. Targets run for every build, or one with `BUILD=<folder>`.

```bash
make setup                  # venv/ with hwkit, CadQuery and dev tools
make all BUILD=aipc         # cad + render + plates + check
make gcode BUILD=aipc       # slice with OrcaSlicer 2.5.x (PLATES="<plate> ..." for some)
make lint test              # ruff and pytest for hwkit
```

Inside a build folder, `../venv/bin/hwkit <cad|plates|render|check|datasheets|slice>` runs one step.

## Required steps

Do every step that applies to a change, in order. Steps that fail are findings to fix in the geometry or spec, never by loosening a check. Run everything from the repo root with `BUILD=<build>`.

### Adding, choosing or changing a part

Use the `part-intake` skill.

1. **Library first.** Reuse the part's spec in [parts/](parts/README.md), or create `parts/<category>/<id>/part.toml` from the real make, model and revision and its manufacturer datasheet or drawing. A seller listing is `listing` evidence, not `datasheet`.
2. **Source every value.** Each dimension gets `evidence` and `source`; unknown values stay `value = ""`, `evidence = "unknown"`. Never invent a number to make a check pass. A purchased part with no datasheet needs `no_datasheet_reason`.
3. **Declare every interface** it needs (`[[requires]]`) and offers (`[[provides]]`) across the whole system: electrical, mechanical, rack, load (`dims.mass`), airflow and service access.
4. **Reference it from the build** with `<build>/parts/<id>.toml`, and register it in the assembly (`[assembly] match`, `covered_by` or a `not_modeled` reason).
5. **Run** `make datasheets check BUILD=<build>`. Resolve every FAIL before buying; report every BLOCKED item to the owner as an open question.
6. **Only then use it in the CAD,** reading its dimensions with `spec.dim(id, key)`.
7. **Update the build's `parts.xlsx` and docs** when the hardware list changes. Ask the owner before changing selected or owned hardware.

### Changing geometry

1. **Change the generators or specs,** never generated files (see Rules).
2. **Rebuild:** `make all BUILD=<build>` (cad, render, plates, check). Every CAD assertion must pass, `make check` must show no new FAIL, and the assembly must have no coverage errors.
3. **Look at the renders** with the `design-review` skill: each changed part's library `render.png`, its `<build>/models/renders/parts/<id>.png`, and the assembly sheets. Write down every finding.
4. **Rebuild every build a shared change touches:** a change to a library spec, a library model another build checks, or anything in `hwkit/` means `make all` for every affected build, and `make lint test` for `hwkit/`. Confirm the other builds' generated outputs did not change unless intended.
5. **Update the build's docs** (`README.md`, `docs/design.md`, `docs/assembly.md`, `print/README.md`) and `parts.xlsx` where the change affects them.

### 3D printed parts

For every new or changed printed part in any build, after the geometry steps above. A part is not done, and must not be committed as released, until step 6 is complete. [docs/printing.md](docs/printing.md) holds the design and printability guidelines the audit in step 5 checks against.

1. **Change the source, not the output.** Edit the generator in the build's `cad/` or the spec (`parts/printed/<id>/part.toml`, `<build>/parts/<id>.toml`). New printed parts get a library spec, a build reference and a plate in the build's print jobs.
2. **Rebuild and slice:** `make all gcode BUILD=<build>` (or `PLATES="<plate>"` for the changed plates). Every CAD assertion, the compatibility check and the slicer must pass.
3. **Check the overhang screen** in `<build>/print/orientation-audit.json` for the part. Explain every downward-facing area: it must be a short anchored bridge, a 45-degree-or-steeper face, or removed. No flat ceilings over air and no cantilevered ledges.
4. **Inspect it yourself in print orientation:** the part's `render.png` from every side and from below, a probe of where each feature starts, bridges or closes layer by layer, wall and edge distances (4 mm from any hole to a free edge), slivers and isolated pads, and driver access to every fastener in assembly order.
5. **Independent print audit.** Give a separate fresh-context agent the generator, the exported STL/STEP, the renders, the orientation audit, the G-code and [docs/printing.md](docs/printing.md), but not your own conclusions. It reports must-fix, should-fix and notes with measured evidence.
6. **Fix and recheck.** Fix every must-fix, decide each should-fix with a reason, rerun steps 2-4 for the affected areas, and record the slicer estimate and mass (`dims.mass` from the OrcaSlicer filament estimate) in the build's `print/README.md` and the part spec.
7. **Fit-test before batch printing.** Print one of each changed part and dry-fit it against the real hardware. A clean CAD, slicer or audit result is a prototype review, not a fit approval. Mark unmeasured interfaces as provisional until then.

### Auditing a build

Before buying parts, before drilling the shelf or printing a release, or when the owner asks, run the `design-audit` skill: full rebuild, check report, datasheet cross-check, interface hunt, visual review and a fresh-context reviewer, reconciled and recorded as a dated section in the build's design notes.

### Committing

1. `make lint test` passes, and `make all` passes for every build the change touched.
2. Commit the regenerated outputs with the source change; never commit G-code, fetched datasheets or `venv/`.
3. Commit and push directly to `main`. Do not create feature branches or pull requests for this repo unless asked.

## Rules

- Shared code goes in `hwkit/`; a build's `cad/` holds only that build's geometry and plate layout. Do not copy helpers between builds. Read part dimensions with `spec.dim(id, key)`, never as literals.
- A part's spec lives once, in the `parts/` library. A build references it with `<build>/parts/<id>.toml`; never copy a spec into a build. Put what is true of the part itself (dimensions, interfaces, datasheets) in the library, and only what this build decides (quantity, role, caps, assembly names) in the build's file. Changing a library spec affects every build that uses it: rerun `make all` for each.
- A part's library model is written only by the build that owns it (`[model] build`, default the first build by name that uses it). Other builds model the part in their own assembly.
- Never hand-edit generated files: in the library `parts/README.md` and `parts/*/*/*.step|stl|png|README.md`; in each build `models/`, `print/*.3mf`, `parts/*.md` and `docs/system-check.md`. Change the generator or spec and rerun `make all BUILD=<build>`.
- Changes to `hwkit/` affect every build: run `make lint test` and `make all` for every build, and confirm the generated outputs did not change unless intended.
- Do not loosen a check, add keepouts or disable count checks to hide a mismatch. Fix the geometry or spec.
- G-code, fetched datasheets and `venv/` are generated and gitignored.
- Distinguish evidence everywhere: `measured`, `datasheet` and `standard` are verified; `listing`, `review`, `photo-estimate`, `allowance` and `assumed` are not. Mark unmeasured interfaces as provisional in docs and reports. A CAD check against coordinates from the same code does not validate those coordinates.

## Build notes

### aipc

Two AI workstations (Berserk, Kenshin) on one Hammond sliding shelf. Generators: `aipc/cad/shelf_layout.py` (assembly, checks, reports) and `aipc/cad/print_jobs.py` (plates).

- `cad/shelf_layout.py` asserts on collisions, fastener access, slot travel, cable routes and hole counts; `hwkit.registry` asserts on assembly coverage.
- The motherboard mount sections and the PSU bracket are built in `hwkit/components/atx_mobo_mount.py` and `atx_psu_bracket.py`, because gpulab reuses them. AIPC owns and exports their library models; a change there changes gpulab too, so run `make all` for both builds.
- Keep one model per unique printed part. Identical copies share a model; the quantity lives in `parts/<name>.toml`, and `export_print(...)` and the plate `copies` in `cad/print_jobs.py` must agree with it.
- Print plates, profiles and fit-test results are in [aipc/print/README.md](aipc/print/README.md).
- Keep [aipc/parts.xlsx](aipc/parts.xlsx) to parts the build actually uses, in step with `aipc/parts/`.

### gpulab

Seven mixed GPUs on cabled x8 risers from one H12D-8D, on two printed 13-position baseboards.

- [gpulab/cad/layout.py](gpulab/cad/layout.py) is the only geometry generator. It asserts on collisions, air gaps, riser screws in the baseboard slots, cards on the deck and MCIO cable reach.
- Card order, air gaps and the start position live in `cad/layout.py`. Each GPU's `gpu-baseboard-position` count in `gpulab/parts/<id>.toml` is the most positions it may take; keep the two in step.
- The H12D mount sections and the PSU bracket are AIPC library parts built by `hwkit.components.atx_mobo_mount` and `atx_psu_bracket`. The layout rebuilds them and asserts they match the library models; it never exports them. Change their design in hwkit and regenerate AIPC first.
- Both baseboards are one model (`quantity = 2`); baseboard B is a translated copy of A, and the generator asserts it.
- The riser board outline and holes are photo estimates. Replace them in the library's [part.toml](parts/purchased/cpayne-cp0231-mcio-device-adapter/part.toml) from C-Payne's 3D model or a measured board before printing.
- The power budget passes only with each GPU's `load_limited` cap (in `gpulab/parts/<id>.toml`; see [gpulab/README.md](gpulab/README.md#power)). Changing a card or a cap means rechecking the 2,400 W budget; never drop a cap to make a card fit.
