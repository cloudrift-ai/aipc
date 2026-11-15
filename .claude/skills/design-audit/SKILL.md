---
name: design-audit
description: Full independent audit of a build's design (for example AIPC): rebuild, compatibility check, datasheet cross-check, visual review and a fresh-context reviewer. Use before buying parts, before drilling or printing a release, or when the user asks to audit the design.
---

# Design audit

This skill applies to every build in the repo. Part specs live in the shared `parts/` library at the repo root; the build's `parts/<id>.toml` references, `models/` and `docs/system-check.md` are inside the build folder (for example `aipc/`). Run `make <target> BUILD=<build>` from the repo root; the shared code is in `hwkit/`.

The audit has to find what the generators cannot: wrong inputs. The CAD only proves that the parts are consistent with the numbers it was given.

## Steps

1. **Rebuild everything:** `make datasheets` (failures are fine; note them), then `make all`. Record any assertion failure: it is a finding, not something to work around.
2. **Read the check report:** the build's `docs/system-check.md` (for example [aipc/docs/system-check.md](../../../aipc/docs/system-check.md)). Every FAIL is a blocker. Every BLOCKED item is an open question with an owner action (find a datasheet, measure, choose a part).
3. **Cross-check the specs against the datasheets.** For each purchased part with local `datasheets/`, compare every `datasheet`-class value in `part.toml` with the document (quote the page). Flag values labelled `datasheet` that are not in the datasheet, and critical dimensions that are missing (for example slide closed length, connector counts, mounting patterns).
4. **Hunt for missing interfaces.** For each pair of parts that touch, plug in, bolt together, share power or share air, ask whether an interface is declared on both sides. Add one where it is missing, and rerun `make check`.
5. **Visual review:** follow the design-review skill for the whole assembly and every part.
6. **Independent review:** start a fresh-context subagent (general-purpose, read-only) with pointers to the build's `parts/*.toml` and the library specs they reference, the build's `system.toml`, `docs/system-check.md`, `models/assembly-bom.json`, the renders and local datasheets. Ask it for ranked findings with concrete evidence and a list of what it could not verify. Do not give it your findings or hypothesis.
7. **Reconcile:** verify each subagent finding yourself before reporting it. Fix spec errors (wrong value or evidence) directly. Geometry changes follow [docs/printing.md](../../../docs/printing.md); hardware changes follow the part-intake skill. Ask the owner before changing selected hardware.
8. **Record the audit** as a dated section in the build's design notes (for AIPC, [docs/design.md](../../../aipc/docs/design.md)): what was checked, the blockers, open questions and what remains physical-only (fit, load, thermal). Keep `parts.xlsx` in step with the build's `parts/`.

## Reporting

Separate findings into: incompatibilities (FAIL), missing data (BLOCKED), weak evidence that a purchase or a drill hole depends on, and visual or geometry issues. Never present a CAD or check pass as physical fit approval.
