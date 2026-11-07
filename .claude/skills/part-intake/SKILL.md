---
name: part-intake
description: Add, select, replace or change a part in the AIPC build (purchased component, printed bracket or fabricated plate). Use before buying or swapping hardware, when a part's dimensions or interfaces change, or when a part is missing from parts/. Creates the part folder, part.toml with evidence-tagged dimensions and interfaces, datasheets and model, then runs the system compatibility check.
---

# Part intake

Every part lives in `parts/<category>/<id>/` (category: `purchased`, `printed`, `fabricated`). The folder name equals `id`. Read [docs/process.md](../../../docs/process.md) once for the rules.

## Steps

1. **Find the real part first.** Get the exact make, model and revision (label photo or order). Find the manufacturer datasheet or drawing. A seller listing is `listing` evidence, not `datasheet`.
2. **Write `part.toml`** using the schema below. Copy a similar part as a template (for example `parts/purchased/nvidia-v100-pcie-16gb/part.toml`).
3. **Transcribe only what you can source.** Each dimension gets `evidence` and `source`. Unknown values stay `value = ""` with `evidence = "unknown"`. Never invent a plausible number to make a check pass.
4. **Declare the interfaces** the part needs (`[[requires]]`) and offers (`[[provides]]`). Think about the whole system, not just the neighbouring part: electrical (connectors, wattage), mechanical (sockets, cooler brackets, slots, card thickness vs slot pitch, mounting patterns, threads, fastener stacks), rack (post depth, width, units, cabinet depth and height), load (`dims.mass`), airflow and service access.
5. **Register it in the assembly.** Add `[assembly] match = ["^Instance_name_regex$"]` for the instances the generator adds, or `covered_by = "<id>"`, or `not_modeled = "<reason>"`. Set `instances_per_unit` when one unit has several instances, or `count_check = false` for bulk items such as fasteners and cables.
6. **Use the spec in the CAD.** Read dimensions with `from aipc import spec; spec.dim("<id>", "<key>")`. No literals for a part's own dimensions in `cad/`.
7. **Run** `make datasheets cad render check`. Fix every FAIL before buying; list every BLOCKED item to the user as an open question. Look at `render.png` and `in-assembly.png` (see the design-review skill).
8. **Update `parts.xlsx`** and the docs when the hardware list changes.

## Schema

```toml
id = "vendor-model"                # equals the folder name
name = "Human readable name"
category = "purchased"             # purchased | printed | fabricated
role = "what it does in the build"
status = "selected"                # owned | ordered | selected | candidate | unspecified | design
quantity = 1
systems = ["berserk"]              # berserk | kenshin | shelf | rack
evidence = "datasheet"             # default for entries below that omit it
on_shelf = true                    # false: mass not carried by the shelf
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
load_limited = 180.0               # optional configured limit (makes the result provisional)

[assembly]
match = ["^Berserk_V100_16GB_PCIE\\d$"]
instances_per_unit = 1
```

Interface rules in `cad/aipc/compat.py`: **value** (equal value, in `accepts`, or within `min..max`), **count** (required count × quantity ≤ provided), **budget** (sum of loads ≤ capacity × derate). Check results: FAIL, BLOCKED, provisional and pass.

## Do not

- Do not hand-edit generated `README.md`, `*.step`, `*.stl` or `render.png`.
- Do not mark a value `datasheet` without a datasheet that states it, or `measured` without a measurement and date.
- Do not loosen a check, add a keepout or set `count_check = false` to hide a real mismatch.
