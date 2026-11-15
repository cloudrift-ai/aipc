"""Pack the GPU lab printed parts into print plates for the build's printer.

Run with ``hwkit plates`` after ``hwkit cad``. The baseboard prints flat, as
installed (nut channels open to the bed), turned 90 degrees so its 258 mm
length runs along the 270 mm bed axis. It prints without a brim: the channels
are open at both plate ends, and a brim would fill their mouths (the AIPC rear
rails had the same problem and printed well without one).
"""

from __future__ import annotations

import json
from collections import Counter

from hwkit import paths, printers, spec
from hwkit.plates import center_group, downward_overhang_area, make_3mf, make_svg, read_binary_stl

OUT = paths.PRINT
PRINTER = printers.get()
BED_W, BED_D = PRINTER.bed
LONG_EDGE_MARGIN = 3.25  # along the bed's long axis, as for the AIPC motherboard rails (no brim, no skirt)
EDGE_MARGIN = 12.0
PALETTE = {"baseboard": "#3b82f6"}
LABELS = {"gpulab_baseboard": "GPU baseboard (13 positions)"}
JOBS = {"01_gpulab_baseboard": ("gpulab_baseboard", "profiles/baseboard-no-brim.json", "printer:duramic-petg-240c.json")}


def turned(mesh):
    """Turn 90 degrees in the bed plane so the plate's length runs along bed X."""
    vertices, triangles, (width, depth, height) = mesh
    return [(y, round(width - x, 5), z) for x, y, z in vertices], triangles, (depth, width, height)


def main():
    (OUT / "profiles").mkdir(parents=True, exist_ok=True)
    process = PRINTER.load_profile("printer:process.json")
    process.update({"name": "0.20mm PETG baseboard no brim @Qidi X-Plus Gen1", "setting_id": "PETG_GPULAB_BASEBOARD",
                    "skirt_loops": "0", "brim_type": "no_brim", "brim_width": "0"})
    (OUT / "profiles/baseboard-no-brim.json").write_text(json.dumps(process, indent=2) + "\n")

    printed = {p.id: p for p in spec.load_all().values() if p.category == "printed"}
    for stale in (*OUT.glob("*.3mf"), *OUT.glob("*.svg"), *(OUT / "gcode").glob("*.gcode"), *(OUT / "gcode").glob("manifest.json")):
        stale.unlink()
    summary, counts, audit = {}, Counter(), {}
    for job, (part_id, process_ref, filament_ref) in JOBS.items():
        source = read_binary_stl(printed[part_id].model_stl)
        mesh = turned(source)
        meshes = {part_id: mesh}
        copies = printed[part_id].quantity
        placements = center_group([(part_id, 0, 0)], meshes, PRINTER.bed)
        (_, x, y), (w, d, h) = placements[0], mesh[2]
        assert x >= LONG_EDGE_MARGIN and x + w <= BED_W - LONG_EDGE_MARGIN + 0.01, (job, "bed X margin", x, w)
        assert y >= EDGE_MARGIN and y + d <= BED_D - EDGE_MARGIN + 0.01, (job, "bed Y margin", y, d)
        make_3mf(OUT / f"{job}.3mf", placements, meshes)
        make_svg(OUT / f"{job}.svg", placements, meshes, PRINTER.bed, EDGE_MARGIN, PALETTE, LABELS)
        counts[part_id] += copies
        audit[part_id] = {"orientation": "as installed, nut channels open to the bed, turned 90 degrees; no supports",
                          "downward_overhang_projected_mm2": downward_overhang_area(mesh),
                          "overhang_note": "the 1.5 mm ledges over each nut channel and the channel roofs between slot ends"}
        summary[job] = {"process_profile": process_ref, "filament_profile": filament_ref,
                        "required_nozzle": "0.4mm; original PETG setup", "supports_required": False,
                        "copies": copies, "items": {part_id: 1}, "count": 1, "highest_part_mm": h,
                        "occupied_bounds_mm": [x, y, x + w, y + d]}
    assert dict(counts) == {pid: p.quantity for pid, p in printed.items()}, (dict(counts), "printed parts and plates disagree")
    (OUT / "manifest.json").write_text(json.dumps({
        "printer": f"{PRINTER.name} Orca preset", "bed_mm": [BED_W, BED_D],
        "edge_margin_mm": EDGE_MARGIN, "long_edge_margin_mm": LONG_EDGE_MARGIN,
        "parts_total": sum(counts.values()), "installation_released": False,
        "gcode_status": "run `make gcode BUILD=gpulab`; print each plate `copies` times",
        "jobs": summary}, indent=2) + "\n")
    (OUT / "orientation-audit.json").write_text(json.dumps({"parts": audit}, indent=2) + "\n")
    print(f"Wrote {len(summary)} plates / {sum(counts.values())} printed parts to {OUT}")


if __name__ == "__main__":
    main()
