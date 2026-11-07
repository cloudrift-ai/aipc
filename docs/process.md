# Design process

Most past mistakes came from a mismatch between the modeled part and the real one, for example a shelf and slides chosen without checking that they fit each other or the cabinet. This process makes every part and every interface explicit, sourced and checked before anything is bought, printed or drilled.

## The four rules

1. **One folder per part.** Every purchased, printed and fabricated part has `parts/<category>/<id>/` with:
   - `part.toml`: identity, quantity, status, dimensions and interfaces, each tagged with an evidence class and a source.
   - `README.md`: generated text specification (edit `part.toml`, not the README).
   - `datasheets/`: the manufacturer documents listed in `part.toml`, fetched by `make datasheets` (gitignored: we keep URLs and extracted values, not copies of other people's PDFs).
   - `<id>.step` (and `<id>.stl` for printed parts): the model the assembly uses. Use the vendor's CAD when one is available (`[model] source = "vendor"`; the generator will not overwrite it), otherwise the generator constructs it from the spec dimensions.
2. **Render and inspect every part.** `make render` writes `render.png` (nine views) for each part. Look at each changed part before accepting it.
3. **Model everything as one assembly and inspect it.** Every assembly instance must belong to a part folder or a declared keepout, and every part must appear in the assembly with its full quantity, sit inside another part's envelope (`covered_by`), or state why it is `not_modeled`. `make cad` fails otherwise. `make render` writes `models/renders/assembly*.png` and `in-assembly.png` for each part.
4. **Check compatibility across the whole system before choosing a part.** Each part declares `[[provides]]` and `[[requires]]` interfaces taken from its datasheet. `make check` matches them across Berserk, Kenshin, the shelf and the rack, and writes [system-check.md](system-check.md).

## Evidence classes

| Class | Meaning | Counts as verified |
| --- | --- | --- |
| `measured` | Measured on the real part by the owner, with date | yes |
| `datasheet` | Manufacturer datasheet, drawing or spec page | yes |
| `standard` | Published standard (ATX, PCIe CEM, M.2, fan hole patterns) | yes |
| `listing` | Seller listing or marketing text | no |
| `photo-estimate` | Scaled from a photograph | no |
| `allowance` | Design allowance or target chosen by us | no |
| `assumed` | Plausible value not yet sourced | no |
| `unknown` | Value missing; leave `value = ""` | blocks |

A check that compares a value with itself proves nothing. If the layout uses a number, it must come from `aipc.spec.dim()` so that it is defined only in the part's spec, and the spec states how trustworthy it is.

## Workflow

### Choosing or changing a part

1. Create or edit `parts/<category>/<id>/part.toml`. The [part-intake skill](../.claude/skills/part-intake/SKILL.md) has the schema.
2. Add its datasheets and run `make datasheets`. Transcribe the dimensions and interfaces you need, with evidence and source. A purchased part with no datasheet needs `no_datasheet_reason`.
3. Declare every interface it needs and offers: socket, cooler mount, memory type, slots, power connectors and wattage, mounting patterns, fastener threads, rack and cabinet dimensions, mass.
4. Run `make check`. Resolve every **FAIL** before buying. Every **BLOCKED** item is a question to answer, usually by finding a datasheet or measuring.
5. Only then use the part in the CAD, reading its dimensions with `spec.dim(id, key)`.

### Changing geometry

1. Change the generators in `cad/`, never the generated files.
2. `make cad render plates check`, or simply `make all`.
3. Inspect `render.png` and `in-assembly.png` for each changed part and the assembly sheets, using the [design-review skill](../.claude/skills/design-review/SKILL.md).
4. Follow [printing.md](printing.md) for printable parts, including the independent audit.

### Auditing the design

Run the [design-audit skill](../.claude/skills/design-audit/SKILL.md): a full rebuild, a check, a visual review and a fresh-context reviewer who compares the part specs against the datasheets and the renders.

## Shared library

Do not reinvent the plumbing in each script. `cad/aipc/` provides:

| Module | Use it for |
| --- | --- |
| `aipc.spec` | `spec.get(id)`, `spec.dim(id, key)`, `spec.load_all()`, `spec.lint()` |
| `aipc.paths` | Repository locations (`PARTS`, `MODELS`, `RENDERS`, `PRINT`) |
| `aipc.export` | `export_print(name, shape, qty, purpose)` into the part folder, checked against `part.toml`; `export_component(id, shape)` |
| `aipc.registry` | `classify_assembly(assembly)`: maps instances to parts, enforces coverage and counts, exports component models, writes `models/assembly-bom.json` |
| `aipc.render` | `render_views(obj, png)` and `Scene(step).highlight(...)`: headless shaded contact sheets |
| `aipc.compat` | `run_checks()`: value, count and budget rules over all interfaces |
| `aipc.partdocs` | Generated part READMEs and the parts index |

Scripts: [shelf_layout.py](../cad/shelf_layout.py) (`make cad`), [render_all.py](../cad/render_all.py) (`make render`), [check_system.py](../cad/check_system.py) (`make check`), [fetch_datasheets.py](../cad/fetch_datasheets.py) (`make datasheets`), [print_jobs.py](../cad/print_jobs.py) (`make plates`) and [slice_jobs.py](../cad/slice_jobs.py) (`make gcode`).
