"""Render every part and the assembly for visual inspection.

Run after ``make cad``. Writes:
  parts/<category>/<id>/render.png        nine views of the part model
  parts/<category>/<id>/in-assembly.png   the part highlighted in the full assembly
  models/renders/assembly*.png            whole build, and each system on its own

Usage: python cad/render_all.py [part-id ...]   (no ids = everything)
"""
from __future__ import annotations

import json
import sys

from aipc import paths, spec
from aipc.render import ASSEMBLY_VIEWS, Scene, render_views

ASSEMBLY_STEP = paths.MODELS / "dual-pc-hammond-assembly.step"


def main(selected: list[str]):
    parts = spec.load_all()
    bom = json.loads((paths.MODELS / "assembly-bom.json").read_text())["parts"]
    todo = [parts[i] for i in selected] if selected else list(parts.values())

    for p in todo:
        if p.model_step.exists():
            render_views(p.model_step, p.render_png, title=f"{p.id}  ({p.category}, qty {p.quantity})")
            print("rendered", p.render_png.relative_to(paths.ROOT))

    scene = Scene(ASSEMBLY_STEP)
    for p in todo:
        names = set(bom.get(p.id, {}).get("instance_names", []))
        if names:
            scene.highlight(p.dir / "in-assembly.png", names, title=f"{p.id} in the assembly")

    if selected:
        return
    paths.RENDERS.mkdir(parents=True, exist_ok=True)
    scene.sheet(paths.RENDERS / "assembly.png", "Dual-PC shelf assembly", ASSEMBLY_VIEWS, (640, 480))
    by_system = {}
    for pid, row in bom.items():
        for system in parts[pid].systems:
            by_system.setdefault(system, set()).update(row["instance_names"])
    for system in ("berserk", "kenshin", "shelf"):
        names = by_system.get(system, set())
        def style(name, rgb, op, names=names):
            return (rgb, op, True, True) if name in names else (rgb, 0.0, False, False)
        scene.sheet(paths.RENDERS / f"assembly-{system}.png", f"{system} parts only",
                    ASSEMBLY_VIEWS, (640, 480), style=style)
    print("rendered", paths.RENDERS.relative_to(paths.ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
