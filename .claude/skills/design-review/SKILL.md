---
name: design-review
description: Visually inspect AIPC part and assembly renders after any CAD change. Use after make cad, before committing geometry, or when asked whether a part or the assembly looks right. Renders every part and the assembly headlessly and walks a checklist; optionally gets an independent fresh-context review.
---

# Design review

A valid solid, a passing collision check or a clean slice is not a review. Look at the pictures.

## Steps

1. `make cad render` (or `.venv/bin/python cad/render_all.py <part-id> ...` for just the changed parts; this still refreshes their in-assembly views).
2. For each changed part, open with the Read tool:
   - `parts/<category>/<id>/render.png`: nine views (three isometric, top, bottom, front, rear, left, right), with the bounding box in the title.
   - `parts/<category>/<id>/in-assembly.png`: the part in orange with the rest of the assembly ghosted.
3. Open `models/renders/assembly.png` and the per-system sheets `assembly-berserk.png`, `assembly-kenshin.png`, `assembly-shelf.png`.
4. Walk the checklist below and write down every finding with the view it came from.
5. For a non-trivial change, ask a fresh-context subagent to review the same images and specs without telling it your conclusions (see the design-audit skill), then reconcile.

## Checklist

**Each part**
- Bounding box matches the intended size and the datasheet (purchased parts) or the design intent (printed parts).
- Holes, slots and pockets are where the mating part needs them, and are through where they must be.
- No slivers, thin walls, floating islands, accidental steps or unclosed spans; see [docs/printing.md](../../../docs/printing.md).
- Printed parts: a broad bed face exists in the intended print orientation; loads run along layers.

**In the assembly**
- The part sits on or against what carries it: no gaps, no interpenetration, nothing floating.
- It is oriented as intended (fan airflow, ports facing the service corridor, hose ends, PSU fan and inlet).
- Fastener heads, washers and drivers have room; parts installed earlier are not covered before their bolts are tightened.
- Overhang beyond the deck front and rear, and total height, match `parts/system.toml` and the cabinet.
- Cables, hoses, connectors and plugs have their keepouts, and nothing blocks them.
- Every part in `parts/README.md` with state "modeled" is visible where it should be; parts marked `not_modeled` are listed as open items.

## Report

List findings as blocker, major or minor, naming the part, the view and what is wrong. Say plainly what the renders cannot show: real tolerances, flexible parts, plugged connector bodies, thermal behaviour.
