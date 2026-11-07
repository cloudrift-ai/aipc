"""STEP/STL export into part folders."""
from __future__ import annotations

import cadquery as cq

from . import spec


def _check_single_solid(name: str, shape: cq.Workplane):
    assert shape.val().isValid(), name
    assert len(shape.solids().vals()) == 1, f"multiple solids in {name}"


def export_print(name: str, shape: cq.Workplane, quantity: int, purpose: str) -> dict:
    """Export one unique printed part to parts/printed/<name>/ and return its manifest row.

    The quantity must match the part spec, so the generator, the spec and the
    plate counts cannot disagree.
    """
    part = spec.get(name)
    assert part.category == "printed", f"{name} is not a printed part"
    assert part.quantity == quantity, f"{name}: generator quantity {quantity} != part.toml {part.quantity}"
    _check_single_solid(name, shape)
    part.dir.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(part.model_step))
    cq.exporters.export(shape, str(part.model_stl), tolerance=0.08, angularTolerance=0.08)
    bb = shape.val().BoundingBox()
    return {"part": name, "quantity": quantity,
            "bounding_box_mm": [round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2)],
            "purpose": purpose}


def export_component(part_id: str, shape: cq.Shape | cq.Workplane) -> None:
    """Export the model a purchased/fabricated part uses in the assembly, moved to its own origin.

    A vendor CAD file (``[model] source = "vendor"``) is never overwritten.
    """
    part = spec.get(part_id)
    if part.data.get("model", {}).get("source") == "vendor":
        return
    solid = shape.val() if isinstance(shape, cq.Workplane) else shape
    bb = solid.BoundingBox()
    local = solid.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin))
    part.dir.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(cq.Workplane().add(local), str(part.model_step))
