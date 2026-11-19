# Design process

This process applies to every build in the repo (one folder per build, such as [aipc/](../aipc/README.md)). Part specs live once in the shared [parts library](../parts/README.md) at the repo root; paths such as `models/` and the build's `parts/<id>.toml` references are inside the build folder. Run `make` from the repo root with `BUILD=<build>`.

Most past mistakes came from a mismatch between the modeled part and the real one, for example a shelf and slides chosen without checking that they fit each other or the cabinet. This process makes every part and every interface explicit, sourced and checked before anything is bought, printed or drilled.

## The four rules

1. **One library folder per part, referenced by each build.** Every purchased, printed and fabricated part has `parts/<category>/<id>/` at the repo root with:
   - `part.toml`: identity, dimensions and interfaces, each tagged with an evidence class and a source.
   - `README.md`: generated text specification with the builds that use the part (edit `part.toml`, not the README).
   - `datasheets/`: the manufacturer documents listed in `part.toml`, fetched by `make datasheets` (gitignored: we keep URLs and extracted values, not copies of other people's PDFs).
   - `<id>.step` (and `<id>.stl` for printed parts): the part model. Use the vendor's CAD when one is available (`[model] source = "vendor"`; the generator will not overwrite it), otherwise the owning build's generator (`[model] build`, default the first build that uses the part) constructs it from the spec dimensions.

   A build uses a part through `<build>/parts/<id>.toml`: `part = "<category>/<id>"`, the quantity, role, status and systems in this build, its `[assembly]` mapping, and optionally build `notes`, extra `[dims]` and `[[requires]]`/`[[provides]]` changes (merged into the library entry of the same type, or `replaces`/`remove` one). `make check` writes `<build>/parts/<id>.md` with the build's view and checks.
2. **Render and inspect every part.** `make render` writes `render.png` (nine views) for each part. Look at each changed part before accepting it.
3. **Model everything as one assembly and inspect it.** Every assembly instance must belong to a part the build references or a declared keepout, and every part must appear in the assembly with its full quantity, sit inside another part's envelope (`covered_by`), or state why it is `not_modeled`. `make cad` fails otherwise. `make render` writes `models/renders/assembly*.png` and `models/renders/parts/<id>.png` (the part highlighted in the assembly) for each part.
4. **Check compatibility across the whole system before choosing a part.** Each part declares `[[provides]]` and `[[requires]]` interfaces taken from its datasheet. `make check` matches them across the build's systems (in AIPC: Berserk, Kenshin, the shelf and the rack), and writes the build's `docs/system-check.md` (for example [aipc/docs/system-check.md](../aipc/docs/system-check.md)).

## Evidence classes

| Class | Meaning | Counts as verified |
| --- | --- | --- |
| `measured` | Measured on the real part by the owner, with date | yes |
| `datasheet` | Manufacturer datasheet, drawing or spec page | yes |
| `standard` | Published standard (ATX, PCIe CEM, M.2, fan hole patterns) | yes |
| `listing` | Seller listing or marketing text | no |
| `review` | Independent review or teardown measurement | no |
| `photo-estimate` | Scaled from a photograph | no |
| `allowance` | Design allowance or target chosen by us | no |
| `assumed` | Plausible value not yet sourced | no |
| `unknown` | Value missing; leave `value = ""` | blocks |

A check that compares a value with itself proves nothing. If the layout uses a number, it must come from `hwkit.spec.dim()` so that it is defined only in the part's spec, and the spec states how trustworthy it is.

## Workflow

The required steps for choosing or changing a part, changing geometry, printed parts, audits and commits are listed once, in the root [AGENTS.md](../AGENTS.md#required-steps). The [part-intake](../.claude/skills/part-intake/SKILL.md), [design-review](../.claude/skills/design-review/SKILL.md) and [design-audit](../.claude/skills/design-audit/SKILL.md) skills give the detailed procedures, and [printing.md](printing.md) the printing guidelines.

### Auditing the design

Run the [design-audit skill](../.claude/skills/design-audit/SKILL.md): a full rebuild, a check, a visual review and a fresh-context reviewer who compares the part specs against the datasheets and the renders.

## Shared library

Do not reinvent the plumbing in each script. The [hwkit](../hwkit) package at the repo root (installed into `venv/` by `make setup`) provides:

| Module | Use it for |
| --- | --- |
| `hwkit.spec` | `spec.get(id)`, `spec.dim(id, key)`, `spec.load_all()` (the build's parts, merged over the library), `spec.load_library()`, `spec.lint()` |
| `hwkit.paths` | The library (`LIBRARY`), locations in the current build (`ROOT`, `PARTS`, `SYSTEM`, `MODELS`, `RENDERS`, `PART_RENDERS`, `PRINT`, `ASSEMBLY_STEP`) and its `build.toml` (`BUILD`) |
| `hwkit.export` | `export_print(name, shape, qty, purpose)` into the library folder, checked against the build's quantity; `export_component(id, shape)`; both only for models the build owns |
| `hwkit.registry` | `classify_assembly(assembly)`: maps instances to parts, enforces coverage and counts, exports component models, writes `models/assembly-bom.json` |
| `hwkit.render` | `render_views(obj, png)` and `Scene(step).highlight(...)`: headless shaded contact sheets |
| `hwkit.compat` | `run_checks()`: value, count and budget rules over all interfaces |
| `hwkit.partdocs` | Generated library READMEs and index, and each build's part pages and index |
| `hwkit.plates` | Read STL meshes, screen overhangs, center a plate, write 3MF and SVG previews |
| `hwkit.printers` | Printers in `hwkit/printers/<id>/`: bed, OrcaSlicer base presets, shared profiles, G-code policy and materials |

Commands (`hwkit <command>`, run inside a build folder; the root Makefile wraps them): `cad` and `plates` run the build's own generators named in its `build.toml` `[scripts]`; `render` ([renders.py](../hwkit/renders.py)), `check` ([check.py](../hwkit/check.py)), `datasheets` ([datasheets.py](../hwkit/datasheets.py)) and `slice` ([slicer.py](../hwkit/slicer.py)) are shared.

## Adding a build

1. Create `<build>/build.toml` with `name`, `title`, `assembly_step`, `printer` and `[scripts]` (copy [aipc/build.toml](../aipc/build.toml)).
2. Add `<build>/parts/<id>.toml` for every part (reuse library parts; add new ones to the library), `<build>/cad/` with the assembly generator and plate script, and `<build>/README.md`. Add the build's notes (generators, its own assertions, ownership of shared models) under Build notes in the root [AGENTS.md](../AGENTS.md#build-notes); builds have no agent files of their own.
3. Run `make all BUILD=<build>`. The root Makefile picks up every folder with a `build.toml`.
