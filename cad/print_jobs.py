"""Pack provisional drilled-shelf STLs on first-generation Qidi X-Plus beds.

Run after shelf_layout.py. Produces centered Core 3MF projects with
separate, named objects, SVG previews and a machine-readable quantity manifest.
The 3MF files contain geometry and centered placement; OrcaSlicer adds print settings.
"""

from __future__ import annotations

import json
import math
import struct
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models"
OUT = ROOT / "print"
BED_W, BED_D = 270.0, 200.0  # Orca's Qidi X-Plus 0.4 nozzle preset
EDGE_MARGIN = 12.0
MOBO_EDGE_MARGIN = 3.25  # long interlocked sections; motherboard-only profile disables skirt, keeps 3 mm brim
MIN_GAP = 8.0  # leaves 2 mm between neighboring 3 mm brims


def print_orientation(part, mesh):
    """Orient large flat parts to keep their short side across the bed depth.

    Board frames additionally flip to put screw-head recesses upward. The assembly
    STLs stay in shelf coordinates; only the 3MF bed orientation changes.
    """
    vertices, triangles, (width, depth, height) = mesh
    if part.startswith("gpu_exhaust_"):
        return mesh, {"gpu_exhaust_fan_flange": "flat fan face on bed; straight neck up, no supports",
                      "gpu_exhaust_roof_flange": "flat square mating face on bed; neck up, no supports"}[part]
    if part.endswith("_aio_hose_brace"):
        return mesh, "mirrored inward web on bed; hose-load plane within layers; broad original-foot clearance; no supports"
    if part == "psu_bracket":
        return mesh, "broad rear frame face flat on bed; compact foot and gussets grow upward; HT-PLA-GF with0.4mm hardened nozzle"
    if part == "v100_gpu_shroud":
        return mesh, "integral fan face on bed, rotated90deg; continuous exterior and four permanent tapered ribs; no removable supports"
    if part == "tnut_fit_coupon":
        return mesh, "flat coupon, M4 rectangular T-nut pocket open up"
    if part in {"fan140_aio_frame", "fan120_aio_frame"}:
        rotated = [(y, round(width - x, 5), z) for x, y, z in vertices]
        return (rotated, triangles, (depth, width, height)), "flat, rotated 90 degrees for larger bed-edge clearance"
    if "_mobo_adapter_" not in part:
        return mesh, "shelf orientation"
    rotated = [(y, x, round(height - z, 5))
               for x, y, z in vertices]
    return (rotated, triangles, (depth, width, height)), "flat, rotated 90 degrees; screw-head recesses up"


def downward_overhang_area(mesh):
    """Projected area of elevated faces with normals within 45 degrees of -Z.

    This is a mesh screening metric, not a slicer support or bridge simulation.
    Coplanar faces on the bed are excluded.
    """
    vertices, triangles, _ = mesh
    total = 0.0
    for ia, ib, ic in triangles:
        a, b, c = vertices[ia], vertices[ib], vertices[ic]
        zmid = (a[2] + b[2] + c[2]) / 3
        if zmid <= 0.25:
            continue
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        cross = (u[1] * v[2] - u[2] * v[1],
                 u[2] * v[0] - u[0] * v[2],
                 u[0] * v[1] - u[1] * v[0])
        norm = math.sqrt(sum(n * n for n in cross))
        if norm and cross[2] / norm < -math.sqrt(0.5):
            total += -cross[2] / 2
    return round(total, 2)

def pack_jobs(meshes):
    """One centered plate per unique model, in suggested print order.

    Returns {job: (placements, copies)}: print a plate's G-code `copies` times.
    The two PSU brackets fit side by side, so their plate holds both.
    """
    single = lambda part, copies=1: ([(part, 0, 0)], copies)
    psu_w = meshes["psu_bracket"][2][0]
    return {
        "01_atx_mobo_adapter_front": single("atx_mobo_adapter_front", 2),
        "02_atx_mobo_adapter_rail": single("atx_mobo_adapter_rail"),
        "03_h12d_mobo_adapter_rail": single("h12d_mobo_adapter_rail"),
        "04_gpu_rest": single("gpu_rest"),
        "05_psu_brackets": ([("psu_bracket", 0, 0), ("psu_bracket", psu_w + MIN_GAP, 0)], 1),
        "06_fan140_aio_frame": single("fan140_aio_frame", 2),
        "07_fan140_aio_hose_brace": single("fan140_aio_hose_brace"),
        "08_fan120_aio_frame": single("fan120_aio_frame", 2),
        "09_fan120_aio_hose_brace": single("fan120_aio_hose_brace"),
        "10_fan120_aio_center_spacer": single("fan120_aio_center_spacer"),
        "11_tnut_fit_coupon": single("tnut_fit_coupon"),
        "12_v100_gpu_shroud": single("v100_gpu_shroud"),
        "13_gpu_exhaust_fan_flange": single("gpu_exhaust_fan_flange"),
        "14_gpu_exhaust_roof_flange": single("gpu_exhaust_roof_flange"),
    }


def center_group(placements, meshes):
    """Keep the compact layout intact and put its occupied bounds at bed center."""
    left = min(x for _, x, _ in placements)
    front = min(y for _, _, y in placements)
    right = max(x + meshes[part][2][0] for part, x, _ in placements)
    rear = max(y + meshes[part][2][1] for part, _, y in placements)
    dx = (BED_W - (right - left)) / 2 - left
    dy = (BED_D - (rear - front)) / 2 - front
    return [(part, round(x + dx, 3), round(y + dy, 3))
            for part, x, y in placements]


def read_binary_stl(path: Path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + count * 50, f"Expected binary STL: {path}"
    vertices, vertex_ids, triangles = [], {}, []
    for i in range(count):
        coords = struct.unpack_from("<9f", data, 84 + i * 50 + 12)
        tri = []
        for k in (0, 3, 6):
            vertex = tuple(round(float(v), 5) for v in coords[k:k + 3])
            if vertex not in vertex_ids:
                vertex_ids[vertex] = len(vertices)
                vertices.append(vertex)
            tri.append(vertex_ids[vertex])
        triangles.append(tuple(tri))
    lo = tuple(min(v[i] for v in vertices) for i in range(3))
    hi = tuple(max(v[i] for v in vertices) for i in range(3))
    assert all(abs(v) < 0.01 for v in lo), f"STL not based at origin: {path}: {lo}"
    return vertices, triangles, tuple(round(hi[i] - lo[i], 3) for i in range(3))


def make_3mf(path: Path, placements, meshes):
    ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    ET.register_namespace("", ns)
    model = ET.Element(f"{{{ns}}}model", {"unit": "millimeter", "xml:lang": "en-US"})
    resources = ET.SubElement(model, f"{{{ns}}}resources")
    used = list(dict.fromkeys(part for part, _, _ in placements))
    ids = {part: index + 1 for index, part in enumerate(used)}
    for part in used:
        vertices, triangles, _ = meshes[part]
        obj = ET.SubElement(resources, f"{{{ns}}}object", {
            "id": str(ids[part]), "type": "model", "name": part})
        mesh = ET.SubElement(obj, f"{{{ns}}}mesh")
        verts_xml = ET.SubElement(mesh, f"{{{ns}}}vertices")
        for x, y, z in vertices:
            ET.SubElement(verts_xml, f"{{{ns}}}vertex", {
                "x": str(x), "y": str(y), "z": str(z)})
        tris_xml = ET.SubElement(mesh, f"{{{ns}}}triangles")
        for a, b, c in triangles:
            ET.SubElement(tris_xml, f"{{{ns}}}triangle", {
                "v1": str(a), "v2": str(b), "v3": str(c)})
    build = ET.SubElement(model, f"{{{ns}}}build")
    for part, x, y in placements:
        ET.SubElement(build, f"{{{ns}}}item", {
            "objectid": str(ids[part]),
            "transform": f"1 0 0 0 1 0 0 0 1 {x} {y} 0"})
    content_types = ('<?xml version="1.0" encoding="UTF-8"?>'
                     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                     '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')
    with ZipFile(path, "w", ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in (("[Content_Types].xml", content_types),
                           ("_rels/.rels", rels),
                           ("3D/3dmodel.model", ET.tostring(
                               model, encoding="utf-8", xml_declaration=True))):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            z.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=6)


def make_svg(path: Path, placements, meshes):
    palette = {"gpu_exhaust": "#268a99", "v100": "#37a0a5", "mobo_adapter": "#3b82f6", "psu": "#f59e0b",
               "fan120": "#f97316", "fan140": "#a855f7", "gpu_rest": "#22c55e", "tnut": "#37a0a5"}
    short_labels = {"atx_mobo_adapter_front": "ATX front section",
                    "atx_mobo_adapter_rail": "ATX rail section",
                    "h12d_mobo_adapter_rail": "H12D rail section",
                    "psu_bracket": "PSU bracket",
                    "fan140_aio_frame": "140 mm AIO frame",
                    "fan140_aio_hose_brace": "140 mm hose brace",
                    "fan120_aio_frame": "120 mm AIO frame",
                    "fan120_aio_hose_brace": "120 mm hose brace",
                    "fan120_aio_center_spacer": "120 mm fan spacer",
                    "gpu_rest": "GPU rest",
                    "v100_gpu_shroud": "V100 GPU shroud",
                    "tnut_fit_coupon": "M4 T-nut fit test"}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-5 -5 {BED_W + 10} {BED_D + 10}">',
        f'<rect x="0" y="0" width="{BED_W}" height="{BED_D}" '
        'fill="#f8fafc" stroke="#334155" stroke-width="1"/>',
        f'<rect x="{EDGE_MARGIN}" y="{EDGE_MARGIN}" '
        f'width="{BED_W - 2 * EDGE_MARGIN}" height="{BED_D - 2 * EDGE_MARGIN}" '
        'fill="none" stroke="#94a3b8" stroke-dasharray="3 3"/>',
    ]
    for part, x, y in placements:
        w, d, _ = meshes[part][2]
        # SVG Y is inverted so the origin in the plate drawing is front-left.
        sy = BED_D - y - d
        lines.append(f'<rect x="{x}" y="{sy}" width="{w}" height="{d}" '
                     f'fill="{next(color for key, color in palette.items() if key in part)}" fill-opacity="0.75" stroke="#0f172a" '
                     'stroke-width="0.6"/>')
        label = short_labels.get(part, part.replace("_", " "))
        lines.append(f'<text x="{x + w / 2}" y="{sy + d / 2 + 1.5}" '
                     'font-family="sans-serif" font-size="5" text-anchor="middle" '
                     f'fill="#0f172a">{label}</text>')
    lines.append('</svg>')
    path.write_text("\n".join(lines) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Center the two long ATX sections; keep the 3 mm brim, omit only the skirt.
    mobo_process=json.loads((OUT/"profiles/process.json").read_text())
    mobo_process.update({"name":"0.20mm PETG ATX ears @Qidi X-Plus Gen1","setting_id":"PETG_ATX_EARS", "skirt_loops":"0"})
    (OUT/"profiles/motherboard-ears.json").write_text(json.dumps(mobo_process,indent=2)+"\n")
    (OUT/"profiles/motherboard-rails-supported.json").unlink(missing_ok=True)
    # Integral chamber ribs support the shroud; all current cooling jobs use this process.
    cooling_process=json.loads((OUT / "profiles/ht-pla-gf-psu.json").read_text())
    cooling_process.update({"name":"0.20mm HT-PLA-GF cooling @Qidi X-Plus Gen1","setting_id":"HTPLAGF_COOLING_SLOW"})
    (OUT/"profiles/ht-pla-gf-cooling.json").write_text(json.dumps(cooling_process,indent=2)+"\n")
    (OUT/"profiles/ht-pla-gf-cooling-supported.json").unlink(missing_ok=True)
    (OUT/"profiles/plenum-supports.json").unlink(missing_ok=True)
    intended = {entry["part"]: entry["quantity"] for entry in
                json.loads((SOURCE / "fit-report.json").read_text())["printed_parts"]}
    source_meshes = {part: read_binary_stl(SOURCE / f"{part}.stl") for part in intended}
    oriented = {part: print_orientation(part, mesh)
                for part, mesh in source_meshes.items()}
    meshes = {part: oriented[part][0] for part in intended}
    orientation_audit = {}
    for part in intended:
        before = downward_overhang_area(source_meshes[part])
        after = downward_overhang_area(meshes[part])
        assert after <= before + 0.01, (part, before, after)
        bridge_note = None
        if part.endswith('_mobo_adapter_rail'):
            # Only the 2mm-wide GPU groove roofs may face down. All screw
            # pockets stay open upward in the original print orientation.
            # Groove is1..3mm behind PCB edge; the forward circular caps of
            # eight16x11.5mm washer lands interrupt it. Integrate those caps
            # independently of the exported mesh to check the exact roof area.
            vertices, triangles, (width, depth, _) = meshes[part]
            radius = 11.5/2
            def cap_area(height):
                return (radius*radius*math.acos((radius-height)/radius)
                        -(radius-height)*math.sqrt(2*radius*height-height*height))
            expected = 2*depth-8*(cap_area(3.5)-cap_area(1.5))
            assert abs(after-expected) < .5, (part, 'unexpected bridge area', after, expected)
            for indices in triangles:
                a,b,c = [vertices[i] for i in indices]
                u = [b[i]-a[i] for i in range(3)]
                v = [c[i]-a[i] for i in range(3)]
                normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
                norm = math.sqrt(sum(n*n for n in normal))
                # Use the same 45-degree criterion as the screening metric;
                # float STL coordinates give vertical curved walls tiny Z normals.
                if norm and normal[2]/norm < -math.sqrt(.5) and min(a[2],b[2],c[2]) > .25:
                    assert all(abs(p[2]-2) < .001 for p in (a,b,c)), (part, 'unexpected roof height')
                    assert all(width-15.501 <= p[0] <= width-13.499 for p in (a,b,c)), (part, 'roof outside GPU groove')
                    assert max(p[0] for p in (a,b,c))-min(p[0] for p in (a,b,c)) <= 2.001
            bridge_note = 'Original recesses-up orientation; only the2mm GPU groove at PCB rear+1..3mm bridges at print Z2, between walls rooted on bed. No support; inspect sliced closure and dry-fit.'
        elif "_mobo_adapter_" in part:
            assert after == 0, (part, after)
        orientation_audit[part] = {
            "orientation": oriented[part][1],
            "original_downward_overhang_projected_mm2": before,
            "print_downward_overhang_projected_mm2": after,
            **({'bridge_review': bridge_note} if bridge_note else {}),
        }
    jobs = pack_jobs(meshes)
    # A new plate export invalidates any older toolpaths, even if the names match.
    for stale in (*OUT.glob("*.3mf"), *OUT.glob("*.svg"),
                  *((OUT / "gcode").glob("*.gcode")),
                  *((OUT / "gcode").glob("manifest.json"))):
        stale.unlink()
    counts = Counter()
    summary = {}
    for job, (local_placements, copies) in jobs.items():
        placements = center_group(local_placements, meshes)
        rectangles = []
        for part, x, y in placements:
            assert part in intended
            w, d, h = meshes[part][2]
            margin = (MOBO_EDGE_MARGIN if "_mobo_adapter_" in part else EDGE_MARGIN)
            assert x >= margin and y >= margin, (part, x,y,w,d)
            assert x + w <= BED_W - margin + 0.01, (part,w,d)
            assert y + d <= BED_D - margin + 0.01, (part,w,d)
            assert h <= 200
            for other, ox, oy, ow, od in rectangles:
                gap_x = max(ox - (x + w), x - (ox + ow), 0)
                gap_y = max(oy - (y + d), y - (oy + od), 0)
                assert gap_x >= MIN_GAP - .01 or gap_y >= MIN_GAP - .01, \
                    (job, part, other)
            rectangles.append((part, x, y, w, d))
            counts[part] += copies
        make_3mf(OUT / f"{job}.3mf", placements, meshes)
        make_svg(OUT / f"{job}.svg", placements, meshes)
        heat_material = any(key in job for key in ("psu", "v100_", "gpu_exhaust_", "tnut_"))
        summary[job] = {
            "process_profile": "profiles/ht-pla-gf-psu.json" if "psu" in job else "profiles/ht-pla-gf-cooling.json" if heat_material else "profiles/motherboard-ears.json" if "mobo_adapter" in job else "profiles/process.json",
            "filament_profile": "profiles/polymaker-ht-pla-gf-230c.json" if heat_material else "profiles/duramic-petg-240c.json",
            "required_nozzle": "0.4mm hardened steel" if heat_material else "0.4mm; original PETG setup",
            "supports_required": False,
            "copies": copies,
            "items": dict(Counter(part for part, _, _ in placements)),
            "count": len(placements),
            "highest_part_mm": max(meshes[part][2][2] for part, _, _ in placements),
            "occupied_bounds_mm": [
                min(x for _, x, _ in placements),
                min(y for _, _, y in placements),
                max(x + meshes[part][2][0] for part, x, _ in placements),
                max(y + meshes[part][2][1] for part, _, y in placements),
            ],
        }
        left, front, right, rear = summary[job]["occupied_bounds_mm"]
        assert abs((left + right) / 2 - BED_W / 2) < 0.01
        assert abs((front + rear) / 2 - BED_D / 2) < 0.01
    assert dict(counts) == intended, (dict(counts), intended)
    (OUT / "manifest.json").write_text(json.dumps({
        "printer": "Qidi X-Plus first generation, 0.4 mm nozzle Orca preset",
        "bed_mm": [BED_W, BED_D],
        "edge_margin_mm": EDGE_MARGIN,
        "motherboard_edge_margin_exception_mm": MOBO_EDGE_MARGIN,
        "minimum_part_gap_mm": MIN_GAP,
        "parts_total": sum(counts.values()),
        "installation_released": False,
        "gcode_status": "run `make gcode` for provisional fit-prototype G-code; print each plate `copies` times",
        "jobs": summary,
    }, indent=2) + "\n")
    (OUT / "orientation-audit.json").write_text(json.dumps({
        "metric": "projected area of elevated mesh faces with normals within 45 degrees of downward vertical; bed contact excluded",
        "limit": "screening only; bridges and layer paths must also be checked in OrcaSlicer",
        "parts": orientation_audit,
    }, indent=2) + "\n")
    print(f"Wrote {len(jobs)} plates / {sum(counts.values())} printed parts to {OUT}")


if __name__ == "__main__":
    main()
