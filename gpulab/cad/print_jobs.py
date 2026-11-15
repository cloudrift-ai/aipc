"""Pack the GPU lab printed parts into print plates for the build's printer.

Run with ``hwkit plates`` after ``hwkit cad``. The baseboard prints flat, as
installed (nut channels open to the bed), turned 90 degrees so its 258 mm
length runs along the 270 mm bed axis. It prints without a brim: the channels
are open at both plate ends, and a brim would fill their mouths (the AIPC rear
rails had the same problem and printed well without one).

The H12D mount sections and the PSU bracket are AIPC library parts. Their bed
orientation, margins and profiles come from the shared hwkit components, so
these plates match AIPC's plates for the same parts.
"""

from __future__ import annotations

import json
from collections import Counter

from hwkit import paths, printers, spec
from hwkit.components import atx_mobo_mount as mobo_mount
from hwkit.components import atx_psu_bracket as psu_bracket
from hwkit.plates import center_group, downward_overhang_area, make_3mf, make_svg, read_binary_stl

OUT = paths.PRINT
PRINTER = printers.get()
BED_W, BED_D = PRINTER.bed
LONG_EDGE_MARGIN = 3.25  # along the bed's long axis, as for the AIPC motherboard rails (no brim, no skirt)
EDGE_MARGIN = 12.0
PALETTE = {"baseboard": "#3b82f6", "mobo_adapter": "#3b82f6", "psu": "#f59e0b"}
LABELS = {"gpulab_baseboard": "GPU baseboard (13 positions)", "h12d_mobo_adapter_rail": "H12D rail section",
          "atx_mobo_adapter_front": "ATX front section", "psu_bracket": "PSU bracket"}
PETG = "0.4mm; original PETG setup"
# job: (part, process profile, filament profile, nozzle, bed margin along the long axis)
JOBS = {
    "01_gpulab_baseboard": ("gpulab_baseboard", "profiles/baseboard-no-brim.json", "printer:duramic-petg-240c.json", PETG, LONG_EDGE_MARGIN),
    "02_h12d_mobo_adapter_rail": ("h12d_mobo_adapter_rail", mobo_mount.PROFILE["h12d_mobo_adapter_rail"], mobo_mount.FILAMENT, PETG,
                                  mobo_mount.PRINT_EDGE_MARGIN),
    "03_atx_mobo_adapter_front": ("atx_mobo_adapter_front", mobo_mount.PROFILE["atx_mobo_adapter_front"], mobo_mount.FILAMENT, PETG,
                                  mobo_mount.PRINT_EDGE_MARGIN),
    "04_psu_bracket": ("psu_bracket", psu_bracket.PROCESS, psu_bracket.FILAMENT, psu_bracket.NOZZLE, EDGE_MARGIN),
}


def turned(mesh):
    """Turn 90 degrees in the bed plane so the plate's length runs along bed X."""
    vertices, triangles, (width, depth, height) = mesh
    return [(y, round(width - x, 5), z) for x, y, z in vertices], triangles, (depth, width, height)


ORIENT = {
    "gpulab_baseboard": (turned, "as installed, nut channels open to the bed, turned 90 degrees; no supports",
                         "the 1.5 mm ledges over each nut channel and the channel roofs between slot ends"),
    "h12d_mobo_adapter_rail": (mobo_mount.print_mesh, mobo_mount.PRINT_NOTE, "the 2 mm GPU-tab groove roof only (audited in AIPC)"),
    "atx_mobo_adapter_front": (mobo_mount.print_mesh, mobo_mount.PRINT_NOTE, "none expected"),
    "psu_bracket": (lambda mesh: mesh, psu_bracket.PRINT_NOTE, "none expected"),
}


def main():
    (OUT / "profiles").mkdir(parents=True, exist_ok=True)
    process = PRINTER.load_profile("printer:process.json")
    process.update({"name": "0.20mm PETG baseboard no brim @Qidi X-Plus Gen1", "setting_id": "PETG_GPULAB_BASEBOARD",
                    "skirt_loops": "0", "brim_type": "no_brim", "brim_width": "0"})
    (OUT / "profiles/baseboard-no-brim.json").write_text(json.dumps(process, indent=2) + "\n")
    for name, profile in mobo_mount.print_profiles(PRINTER).items():
        (OUT / "profiles" / name).write_text(json.dumps(profile, indent=2) + "\n")

    printed = {p.id: p for p in spec.load_all().values() if p.category == "printed"}
    for stale in (*OUT.glob("*.3mf"), *OUT.glob("*.svg"), *(OUT / "gcode").glob("*.gcode"), *(OUT / "gcode").glob("manifest.json")):
        stale.unlink()
    summary, counts, audit = {}, Counter(), {}
    for job, (part_id, process_ref, filament_ref, nozzle, long_margin) in JOBS.items():
        source = read_binary_stl(printed[part_id].model_stl)
        orient, orientation, overhang_note = ORIENT[part_id]
        mesh = orient(source)
        meshes = {part_id: mesh}
        copies = printed[part_id].quantity
        placements = center_group([(part_id, 0, 0)], meshes, PRINTER.bed)
        (_, x, y), (w, d, h) = placements[0], mesh[2]
        assert x >= long_margin and x + w <= BED_W - long_margin + 0.01, (job, "bed X margin", x, w)
        assert y >= min(long_margin, EDGE_MARGIN) and y + d <= BED_D - min(long_margin, EDGE_MARGIN) + 0.01, (job, "bed Y margin", y, d)
        make_3mf(OUT / f"{job}.3mf", placements, meshes)
        make_svg(OUT / f"{job}.svg", placements, meshes, PRINTER.bed, EDGE_MARGIN, PALETTE, LABELS)
        counts[part_id] += copies
        audit[part_id] = {"orientation": orientation, "downward_overhang_projected_mm2": downward_overhang_area(mesh),
                          "overhang_note": overhang_note}
        summary[job] = {"process_profile": process_ref, "filament_profile": filament_ref,
                        "required_nozzle": nozzle, "supports_required": False,
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
