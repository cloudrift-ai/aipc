# Design process

This process applies to every build in the repo (one folder per build, such as [aipc/](../aipc/README.md)). Paths such as `parts/` and `models/` are inside the build folder; run `make` from the repo root with `BUILD=<build>`.

Most past mistakes came from a mismatch between the modeled part and the real one, for example a shelf and slides chosen without checking that they fit each other or the cabinet. This process makes every part and every interface explicit, sourced and checked before anything is bought, printed or drilled.

## The four rules

1. **One folder per part.** Every purchased, printed and fabricated part has `parts/<category>/<id>/` with:
   - `part.toml`: identity, quantity, status, dimensions and interfaces, each tagged with an evidence class and a source.
   - `README.md`: generated text specification (edit `part.toml`, not the README).
   - `datasheets/`: the manufacturer documents listed in `part.toml`, fetched by `make datasheets` (gitignored: we keep URLs and extracted values, not copies of other people's PDFs).
   - `<id>.step` (and `<id>.stl` for printed parts): the model the assembly uses. Use the vendor's CAD when one is available (`[model] source = "vendor"`; the generator will not overwrite it), otherwise the generator constructs it from the spec dimensions.
2. **Render and inspect every part.** `make render` writes `render.png` (nine views) for each part. Look at each changed part before accepting it.
3. **Model everything as one assembly and inspect it.** Every assembly instance must belong to a part folder or a declared keepout, and every part must appear in the assembly with its full quantity, sit inside another part's envelope (`covered_by`), or state why it is `not_modeled`. `make cad` fails otherwise. `make render` writes `models/renders/assembly*.png` and `in-assembly.png` for each part.
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

### Choosing or changing a part

1. Create or edit `parts/<category>/<id>/part.toml`. The [part-intake skill](../.claude/skills/part-intake/SKILL.md) has the schema.
2. Add its datasheets and run `make datasheets`. Transcribe the dimensions and interfaces you need, with evidence and source. A purchased part with no datasheet needs `no_datasheet_reason`.
3. Declare every interface it needs and offers: socket, cooler mount, memory type, slots, power connectors and wattage, mounting patterns, fastener threads, rack and cabinet dimensions, mass.
4. Run `make check`. Resolve every **FAIL** before buying. Every **BLOCKED** item is a question to answer, usually by finding a datasheet or measuring.
5. Only then use the part in the CAD, reading its dimensions with `spec.dim(id, key)`.

### Changing geometry

1. Change the build's generators in `cad/`, never the generated files.
2. `make cad render plates check BUILD=<build>`, or simply `make all BUILD=<build>`.
3. Inspect `render.png` and `in-assembly.png` for each changed part and the assembly sheets, using the [design-review skill](../.claude/skills/design-review/SKILL.md).
4. Follow [printing.md](printing.md) for printable parts, including the independent audit.

### Auditing the design

Run the [design-audit skill](../.claude/skills/design-audit/SKILL.md): a full rebuild, a check, a visual review and a fresh-context reviewer who compares the part specs against the datasheets and the renders.

## Shared library

Do not reinvent the plumbing in each script. The [hwkit](../hwkit) package at the repo root (installed into `venv/` by `make setup`) provides:

| Module | Use it for |
| --- | --- |
| `hwkit.spec` | `spec.get(id)`, `spec.dim(id, key)`, `spec.load_all()`, `spec.lint()` |
| `hwkit.paths` | Locations in the current build (`ROOT`, `PARTS`, `MODELS`, `RENDERS`, `PRINT`, `ASSEMBLY_STEP`) and its `build.toml` (`BUILD`) |
| `hwkit.export` | `export_print(name, shape, qty, purpose)` into the part folder, checked against `part.toml`; `export_component(id, shape)` |
| `hwkit.registry` | `classify_assembly(assembly)`: maps instances to parts, enforces coverage and counts, exports component models, writes `models/assembly-bom.json` |
| `hwkit.render` | `render_views(obj, png)` and `Scene(step).highlight(...)`: headless shaded contact sheets |
| `hwkit.compat` | `run_checks()`: value, count and budget rules over all interfaces |
| `hwkit.partdocs` | Generated part READMEs and the parts index |
| `hwkit.plates` | Read STL meshes, screen overhangs, center a plate, write 3MF and SVG previews |
| `hwkit.printers` | Printers in `hwkit/printers/<id>/`: bed, OrcaSlicer base presets, shared profiles, G-code policy and materials |

Commands (`hwkit <command>`, run inside a build folder; the root Makefile wraps them): `cad` and `plates` run the build's own generators named in its `build.toml` `[scripts]`; `render` ([renders.py](../hwkit/renders.py)), `check` ([check.py](../hwkit/check.py)), `datasheets` ([datasheets.py](../hwkit/datasheets.py)) and `slice` ([slicer.py](../hwkit/slicer.py)) are shared.

## Adding a build

1. Create `<build>/build.toml` with `name`, `title`, `assembly_step`, `printer` and `[scripts]` (copy [aipc/build.toml](../aipc/build.toml)).
2. Add `<build>/parts/`, `<build>/cad/` with the assembly generator and plate script, `<build>/README.md` and `<build>/AGENTS.md` (with `CLAUDE.md` containing `@AGENTS.md`).
3. Run `make all BUILD=<build>`. The root Makefile picks up every folder with a `build.toml`.
