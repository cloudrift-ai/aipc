---
name: design-audit
description: Full independent audit of the AIPC design: rebuild, compatibility check, datasheet cross-check, visual review and a fresh-context reviewer. Use before buying parts, before drilling or printing a release, or when the user asks to audit the design.
---

# Design audit

The audit has to find what the generators cannot: wrong inputs. The CAD only proves that the parts are consistent with the numbers it was given.

## Steps

1. **Rebuild everything:** `make datasheets` (failures are fine; note them), then `make all`. Record any assertion failure: it is a finding, not something to work around.
2. **Read the check report:** [docs/system-check.md](../../../docs/system-check.md). Every FAIL is a blocker. Every BLOCKED item is an open question with an owner action (find a datasheet, measure, choose a part).
3. **Cross-check the specs against the datasheets.** For each purchased part with local `datasheets/`, compare every `datasheet`-class value in `part.toml` with the document (quote the page). Flag values labelled `datasheet` that are not in the datasheet, and critical dimensions that are missing (for example slide closed length, connector counts, mounting patterns).
4. **Hunt for missing interfaces.** For each pair of parts that touch, plug in, bolt together, share power or share air, ask whether an interface is declared on both sides. Add one where it is missing, and rerun `make check`.
5. **Visual review:** follow the design-review skill for the whole assembly and every part.
6. **Independent review:** start a fresh-context subagent (general-purpose, read-only) with pointers to `parts/`, `parts/system.toml`, `docs/system-check.md`, `models/assembly-bom.json`, the renders and local datasheets. Ask it for ranked findings with concrete evidence and a list of what it could not verify. Do not give it your findings or hypothesis.
7. **Reconcile:** verify each subagent finding yourself before reporting it. Fix spec errors (wrong value or evidence) directly. Geometry changes follow [docs/printing.md](../../../docs/printing.md); hardware changes follow the part-intake skill. Ask the owner before changing selected hardware.
8. **Record the audit** as a dated section in [docs/design.md](../../../docs/design.md): what was checked, the blockers, open questions and what remains physical-only (fit, load, thermal). Keep `parts.xlsx` in step with `parts/`.

## Reporting

Separate findings into: incompatibilities (FAIL), missing data (BLOCKED), weak evidence that a purchase or a drill hole depends on, and visual or geometry issues. Never present a CAD or check pass as physical fit approval.
