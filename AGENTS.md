# AGENTS.md

Notes for coding agents working in this repo. The design process for every build is in [docs/process.md](docs/process.md).

## Layout

| Path | What it is |
| --- | --- |
| [aipc/](aipc/README.md) | AIPC build: two AI workstations (Berserk, Kenshin) on one rack shelf. Fit prototype; has its own [AGENTS.md](aipc/AGENTS.md) |
| [gpulab/](gpulab/README.md) | GPU lab build: seven mixed GPUs on cabled x8 risers from one H12D-8D, two printed 13-position baseboards. Design; has its own [AGENTS.md](gpulab/AGENTS.md) |
| [parts/](parts/README.md) | Shared parts library: one folder per part with its spec (`part.toml`), generated README, model, render and fetched datasheets. Builds only reference it |
| [hwkit/](hwkit) | Shared Python package: part specs, compatibility, assembly registry, export, renders, plates, printers, slicing, shared component models (`hwkit/components`: Hammond shelf, PCIe posts, the AIPC motherboard mount and PSU bracket), and the `hwkit` CLI |
| [hwkit/printers/](hwkit/printers) | Printer definitions (`printer.toml`), vendored OrcaSlicer base presets and shared slicer profiles |
| [docs/](docs) | Shared process and printing guidelines |
| [.claude/skills/](.claude/skills) | Agent skills for every build: `part-intake`, `design-review`, `design-audit` |
| [tests/](tests) | hwkit tests |
| `Makefile`, `pyproject.toml` | Root build: `make setup` creates `venv/` and installs hwkit; every target runs per build |

A build is a folder with a `build.toml` (name, assembly, printer, render sheets and its `[scripts]`). Its `cad/`, `models/`, `print/` and `docs/` belong to that build only. Its `parts/` holds one `<id>.toml` per part it uses: a reference to the library spec plus the build's quantity, role, status, systems, assembly mapping and any build-specific dims or interface changes (schema in [hwkit/spec.py](hwkit/spec.py)). Read the build's own `AGENTS.md` before changing it.

## Commands

Run everything from the repo root. Targets run for every build, or one with `BUILD=<folder>`.

```bash
make setup                  # venv/ with hwkit, CadQuery and dev tools
make all BUILD=aipc         # cad + render + plates + check
make gcode BUILD=aipc       # slice with OrcaSlicer 2.5.x (PLATES="<plate> ..." for some)
make lint test              # ruff and pytest for hwkit
```

Inside a build folder, `../venv/bin/hwkit <cad|plates|render|check|datasheets|slice>` runs one step.

## 3D printed parts: required steps

Do every step, in order, for every new or changed printed part in any build. A part is not done, and must not be committed as released, until step 6 is complete. [docs/printing.md](docs/printing.md) holds the design and printability guidelines the audit in step 5 checks against.

1. **Change the source, not the output.** Edit the generator in the build's `cad/` or the spec (`parts/printed/<id>/part.toml`, `<build>/parts/<id>.toml`). New printed parts get a library spec, a build reference and a plate in the build's print jobs.
2. **Rebuild and slice:** `make all gcode BUILD=<build>` (or `PLATES="<plate>"` for the changed plates). Every CAD assertion, the compatibility check and the slicer must pass.
3. **Check the overhang screen** in `<build>/print/orientation-audit.json` for the part. Explain every downward-facing area: it must be a short anchored bridge, a 45-degree-or-steeper face, or removed. No flat ceilings over air and no cantilevered ledges.
4. **Inspect it yourself in print orientation:** the part's `render.png` from every side and from below, a probe of where each feature starts, bridges or closes layer by layer, wall and edge distances (4 mm from any hole to a free edge), slivers and isolated pads, and driver access to every fastener in assembly order.
5. **Independent print audit.** Give a separate fresh-context agent the generator, the exported STL/STEP, the renders, the orientation audit, the G-code and [docs/printing.md](docs/printing.md), but not your own conclusions. It reports must-fix, should-fix and notes with measured evidence.
6. **Fix and recheck.** Fix every must-fix, decide each should-fix with a reason, rerun steps 2-4 for the affected areas, and record the slicer estimate and mass (`dims.mass` from the OrcaSlicer filament estimate) in the build's `print/README.md` and the part spec.
7. **Fit-test before batch printing.** Print one of each changed part and dry-fit it against the real hardware. A clean CAD, slicer or audit result is a prototype review, not a fit approval. Mark unmeasured interfaces as provisional until then.

## Rules

- Shared code goes in `hwkit/`; a build's `cad/` holds only that build's geometry and plate layout. Do not copy helpers between builds. Read part dimensions with `spec.dim(id, key)`, never as literals.
- A part's spec lives once, in the `parts/` library. A build references it with `<build>/parts/<id>.toml`; never copy a spec into a build. Put what is true of the part itself (dimensions, interfaces, datasheets) in the library, and only what this build decides (quantity, role, caps, assembly names) in the build's file. Changing a library spec affects every build that uses it: rerun `make all` for each.
- A part's library model is written only by the build that owns it (`[model] build`, default the first build by name that uses it). Other builds model the part in their own assembly.
- Never hand-edit generated files: in the library `parts/README.md` and `parts/*/*/*.step|stl|png|README.md`; in each build `models/`, `print/*.3mf`, `parts/*.md` and `docs/system-check.md`. Change the generator or spec and rerun `make all BUILD=<build>`.
- Changes to `hwkit/` affect every build: run `make lint test` and `make all` for every build, and confirm the generated outputs did not change unless intended.
- Do not loosen a check, add keepouts or disable count checks to hide a mismatch. Fix the geometry or spec.
- G-code, fetched datasheets and `venv/` are generated and gitignored.
- Git: commit and push directly to `main`; do not create feature branches or pull requests for this repo unless asked.
- Distinguish evidence everywhere: `measured`, `datasheet` and `standard` are verified; `listing`, `review`, `photo-estimate`, `allowance` and `assumed` are not. A CAD check against coordinates from the same code does not validate those coordinates.
