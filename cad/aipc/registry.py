"""Map every assembly instance to a part folder, and every part folder to the assembly.

Rule: everything is modeled in the assembly. Each instance name must match
exactly one part's ``[assembly] match`` regex (or a declared keepout in
parts/system.toml). Each part either appears with the expected instance count,
is ``covered_by`` another part's envelope, or states why it is ``not_modeled``.
"""
from __future__ import annotations

import json
import re

import cadquery as cq

from . import paths, spec
from .export import export_component


def _instances(assembly: cq.Assembly):
    for shape, name, loc, _color in assembly:
        yield name.split("/", 1)[-1], shape.moved(loc)


def classify_assembly(assembly: cq.Assembly, export_models: bool = True) -> dict:
    parts = spec.load_all()
    keepouts = spec.system_spec().get("keepouts", [])
    patterns = [(p.id, re.compile(rx)) for p in parts.values() for rx in p.assembly.get("match", [])]
    patterns += [(f"keepout:{k['id']}", re.compile(rx)) for k in keepouts for rx in k["match"]]

    found: dict[str, list] = {}
    errors = []
    for name, shape in _instances(assembly):
        hits = sorted({pid for pid, rx in patterns if rx.search(name)})
        if not hits:
            errors.append(f"assembly instance '{name}' matches no part folder or keepout")
            continue
        if len(hits) > 1:
            errors.append(f"assembly instance '{name}' matches several parts: {hits}")
            continue
        found.setdefault(hits[0], []).append((name, shape))

    bom = {}
    for p in parts.values():
        inst = found.get(p.id, [])
        a = p.assembly
        per_unit = int(a.get("instances_per_unit", 1))
        expected = None if a.get("count_check") is False else p.quantity * per_unit
        if inst:
            state = "modeled"
            if expected is not None and len(inst) != expected:
                errors.append(f"{p.id}: {len(inst)} assembly instances, expected quantity {p.quantity} x {per_unit}")
        elif a.get("covered_by"):
            state = "covered"
            if a["covered_by"] not in parts:
                errors.append(f"{p.id}: covered_by unknown part {a['covered_by']}")
        elif a.get("not_modeled"):
            state = "not_modeled"
        else:
            state = "missing"
            errors.append(f"{p.id}: not in the assembly and no not_modeled reason")
        bom[p.id] = {"name": p.name, "category": p.category, "quantity": p.quantity,
                     "state": state, "instances": len(inst), "expected_instances": expected,
                     "covered_by": a.get("covered_by"), "not_modeled": a.get("not_modeled"),
                     "instance_names": [n for n, _ in inst]}
        if export_models and inst and p.category in ("purchased", "fabricated"):
            unit = inst if p.quantity == 1 else inst[:per_unit]
            export_component(p.id, cq.Compound.makeCompound([s for _, s in unit]))
    bom_keepouts = {k: [n for n, _ in v] for k, v in found.items() if k.startswith("keepout:")}
    report = {"rule": "every assembly instance belongs to a part folder or a declared keepout; every part is modeled, covered or explicitly not modeled",
              "parts": bom, "keepouts": bom_keepouts, "errors": errors}
    (paths.MODELS / "assembly-bom.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
