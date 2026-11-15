---
name: part-intake
description: Add, select, replace or change a part in a build (for example AIPC) (purchased component, printed bracket or fabricated plate). Use before buying or swapping hardware, when a part's dimensions or interfaces change, or when a part is missing from a build. Reuses or creates the shared library spec (part.toml with evidence-tagged dimensions, interfaces, datasheets and model), adds the build's reference file, then runs the system compatibility check.
---

# Part intake

This skill applies to every build in the repo. Part specs live in the shared `parts/` library at the repo root; the build's `parts/<id>.toml` references, `models/` and `docs/system-check.md` are inside the build folder (for example `aipc/`). Run `make <target> BUILD=<build>` from the repo root; the shared code is in `hwkit/`.

Every part's spec lives once in the library, `parts/<category>/<id>/part.toml` at the repo root (category: `purchased`, `printed`, `fabricated`; the folder name equals `id`). A build uses it through `<build>/parts/<id>.toml`. Read [docs/process.md](../../../docs/process.md) once for the rules.

## Steps

0. **Check the library first.** If [parts/README.md](../../../parts/README.md) already has the part, skip to step 5: only add the build's reference file. Improve the library spec only with facts about the part itself; they apply to every build that uses it.
1. **Find the real part first.** Get the exact make, model and revision (label photo or order). Find the manufacturer datasheet or drawing. A seller listing is `listing` evidence, not `datasheet`.
2. **Write the library `part.toml`** using the schema below. Copy a similar part as a template (for example `parts/purchased/nvidia-v100-pcie-16gb/part.toml`). Keep build decisions (quantity, role, status, systems, power caps, assembly names) out of it.
3. **Transcribe only what you can source.** Each dimension gets `evidence` and `source`. Unknown values stay `value = ""` with `evidence = "unknown"`. Never invent a plausible number to make a check pass.
4. **Declare the interfaces** the part needs (`[[requires]]`) and offers (`[[provides]]`). Think about the whole system, not just the neighbouring part: electrical (connectors, wattage), mechanical (sockets, cooler brackets, slots, card thickness vs slot pitch, mounting patterns, threads, fastener stacks), rack (post depth, width, units, cabinet depth and height), load (`dims.mass`), airflow and service access.
5. **Reference it from the build** with `<build>/parts/<id>.toml` (schema below) and **register it in the assembly**: add `[assembly] match = ["^Instance_name_regex$"]` for the instances the generator adds, or `covered_by = "<id>"`, or `not_modeled = "<reason>"`. Set `instances_per_unit` when one unit has several instances, or `count_check = false` for bulk items such as fasteners and cables.
6. **Use the spec in the CAD.** Read dimensions with `from hwkit import spec; spec.dim("<id>", "<key>")`. No literals for a part's own dimensions in `cad/`.
7. **Run** `make datasheets cad render check`. Fix every FAIL before buying; list every BLOCKED item to the user as an open question. Look at `render.png` and the build's `models/renders/parts/<id>.png` (see the design-review skill).
8. **Update `parts.xlsx`** and the docs when the hardware list changes.

## Library schema: `parts/<category>/<id>/part.toml`

```toml
id = "vendor-model"                # equals the folder name
name = "Human readable name"
category = "purchased"             # purchased | printed | fabricated
evidence = "datasheet"             # default for entries below that omit it
notes = """Free text: caveats, revision, what to verify."""
no_datasheet_reason = ""           # required for purchased parts without [[datasheets]]

[links]
product = "https://..."

[[datasheets]]
title = "Drawing"
url = "https://..."

[model]
source = "constructed"             # vendor | constructed | generated
vendor_cad = ""                    # where the vendor STEP can be obtained
# build = "aipc"                   # the build whose generator writes the model; default: first build using it

[dims]
length = { value = 266.7, unit = "mm", evidence = "datasheet", source = "brief p.2" }
mass = { value = 1.2, unit = "kg", evidence = "assumed" }

[[provides]]
type = "m2-slot"                   # interface type; must match the requirer's type
value = "M.2 2280 NVMe"            # or accepts = [...]; or min/max for ranges
count = 3                          # per unit; multiplied by quantity
# capacity = 1600.0, unit = "W", derate = 0.8   for budgets

[[requires]]
type = "dc-power"
load = 250.0                       # budget rule
```

## Build reference: `<build>/parts/<id>.toml`

```toml
part = "purchased/vendor-model"    # the library spec
role = "what it does in this build"
status = "selected"                # owned | ordered | selected | candidate | unspecified | design
quantity = 1
systems = ["berserk"]              # the build's systems; AIPC: berserk | kenshin | shelf | rack
on_shelf = true                    # optional; false: mass not carried by the shelf
notes = """Optional: what matters about the part in this build."""

[dims]                             # optional: build-specific dims, merged over the library's
mass = { value = 0.3, unit = "kg", evidence = "assumed" }

[[requires]]                       # optional: changes the library entry of the same type...
type = "dc-power"
load_limited = 180.0               # configured limit (makes the result provisional)

[[requires]]                       # ...or takes over another type's entry, or adds a new one
type = "riser-x16-slot"
replaces = "pcie-x16-slot"         # remove = true drops an entry instead

[assembly]
match = ["^Berserk_V100_16GB_PCIE\\d$"]
instances_per_unit = 1
```

Interface rules in `hwkit/compat.py`: **value** (equal value, in `accepts`, or within `min..max`), **count** (required count × quantity ≤ provided), **budget** (sum of loads ≤ capacity × derate). Check results: FAIL, BLOCKED, provisional and pass.

## Do not

- Do not hand-edit generated `README.md`, `<build>/parts/*.md`, `*.step`, `*.stl` or `render.png`.
- Do not copy a library spec into a build or create a second library folder for the same part.
- Do not mark a value `datasheet` without a datasheet that states it, or `measured` without a measurement and date.
- Do not loosen a check, add a keepout or set `count_check = false` to hide a real mismatch.
