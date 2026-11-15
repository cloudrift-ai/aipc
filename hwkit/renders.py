"""Render every part and the assembly for visual inspection.

Run with ``hwkit render`` after ``hwkit cad``. Writes:
  parts/<category>/<id>/render.png   nine views of the library model, for the parts whose model this build owns
  models/renders/parts/<id>.png      in the build folder: the part highlighted in the build's assembly
  models/renders/assembly*.png       whole build, and each system in build.toml [render] system_sheets

Usage: hwkit render [part-id ...]   (no ids = everything)
"""

from __future__ import annotations

import json
import sys

from hwkit import paths, spec
from hwkit.render import ASSEMBLY_VIEWS, Scene, render_views


def main(selected: list[str]):
    parts = spec.load_all()
    bom = json.loads((paths.MODELS / "assembly-bom.json").read_text())["parts"]
    todo = [parts[i] for i in selected] if selected else list(parts.values())

    for p in todo:
        if p.owns_model and p.model_step.exists():
            render_views(p.model_step, p.render_png, title=f"{p.id}  ({p.category})")
            print("rendered", p.render_png.relative_to(paths.REPO))

    scene = Scene(paths.ASSEMBLY_STEP)
    paths.PART_RENDERS.mkdir(parents=True, exist_ok=True)
    for p in todo:
        names = set(bom.get(p.id, {}).get("instance_names", []))
        if names:
            scene.highlight(p.in_assembly_png, names, title=f"{p.id} in the assembly")

    if selected:
        return
    paths.RENDERS.mkdir(parents=True, exist_ok=True)
    scene.sheet(paths.RENDERS / "assembly.png", paths.BUILD.get("title", paths.BUILD["name"]), ASSEMBLY_VIEWS, (640, 480))
    by_system = {}
    for pid, row in bom.items():
        for system in parts[pid].systems:
            by_system.setdefault(system, set()).update(row["instance_names"])
    for system in paths.BUILD.get("render", {}).get("system_sheets", []):
        names = by_system.get(system, set())

        def style(name, rgb, op, names=names):
            return (rgb, op, True, True) if name in names else (rgb, 0.0, False, False)

        scene.sheet(paths.RENDERS / f"assembly-{system}.png", f"{system} parts only", ASSEMBLY_VIEWS, (640, 480), style=style)
    print("rendered", paths.RENDERS.relative_to(paths.ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
