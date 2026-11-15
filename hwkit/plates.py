"""Print plate helpers: read STL meshes, screen overhangs, center a layout and
write Core 3MF projects with an SVG preview.

A mesh is ``(vertices, triangles, (width, depth, height))`` with the model
based at the origin. A placement is ``(part, x, y)`` in bed millimetres.
The build's plate script decides orientation, grouping and profiles; the
printer (``hwkit.printers``) gives the bed size.
"""

from __future__ import annotations

import math
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


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
        cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        norm = math.sqrt(sum(n * n for n in cross))
        if norm and cross[2] / norm < -math.sqrt(0.5):
            total += -cross[2] / 2
    return round(total, 2)


def center_group(placements, meshes, bed):
    """Keep the compact layout intact and put its occupied bounds at bed center."""
    bed_w, bed_d = bed
    left = min(x for _, x, _ in placements)
    front = min(y for _, _, y in placements)
    right = max(x + meshes[part][2][0] for part, x, _ in placements)
    rear = max(y + meshes[part][2][1] for part, _, y in placements)
    dx = (bed_w - (right - left)) / 2 - left
    dy = (bed_d - (rear - front)) / 2 - front
    return [(part, round(x + dx, 3), round(y + dy, 3)) for part, x, y in placements]


def read_binary_stl(path: Path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + count * 50, f"Expected binary STL: {path}"
    vertices, vertex_ids, triangles = [], {}, []
    for i in range(count):
        coords = struct.unpack_from("<9f", data, 84 + i * 50 + 12)
        tri = []
        for k in (0, 3, 6):
            vertex = tuple(round(float(v), 5) for v in coords[k : k + 3])
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
        obj = ET.SubElement(resources, f"{{{ns}}}object", {"id": str(ids[part]), "type": "model", "name": part})
        mesh = ET.SubElement(obj, f"{{{ns}}}mesh")
        verts_xml = ET.SubElement(mesh, f"{{{ns}}}vertices")
        for x, y, z in vertices:
            ET.SubElement(verts_xml, f"{{{ns}}}vertex", {"x": str(x), "y": str(y), "z": str(z)})
        tris_xml = ET.SubElement(mesh, f"{{{ns}}}triangles")
        for a, b, c in triangles:
            ET.SubElement(tris_xml, f"{{{ns}}}triangle", {"v1": str(a), "v2": str(b), "v3": str(c)})
    build = ET.SubElement(model, f"{{{ns}}}build")
    for part, x, y in placements:
        ET.SubElement(build, f"{{{ns}}}item", {"objectid": str(ids[part]), "transform": f"1 0 0 0 1 0 0 0 1 {x} {y} 0"})
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
        "</Relationships>"
    )
    with ZipFile(path, "w", ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in (
            ("[Content_Types].xml", content_types),
            ("_rels/.rels", rels),
            ("3D/3dmodel.model", ET.tostring(model, encoding="utf-8", xml_declaration=True)),
        ):
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            z.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=6)


def make_svg(path: Path, placements, meshes, bed, edge_margin, palette: dict[str, str], labels: dict[str, str]):
    """Top view of a plate. ``palette`` maps a part-name substring to a fill color; ``labels`` maps part to text."""
    bed_w, bed_d = bed
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-5 -5 {bed_w + 10} {bed_d + 10}">',
        f'<rect x="0" y="0" width="{bed_w}" height="{bed_d}" fill="#f8fafc" stroke="#334155" stroke-width="1"/>',
        f'<rect x="{edge_margin}" y="{edge_margin}" '
        f'width="{bed_w - 2 * edge_margin}" height="{bed_d - 2 * edge_margin}" '
        'fill="none" stroke="#94a3b8" stroke-dasharray="3 3"/>',
    ]
    for part, x, y in placements:
        w, d, _ = meshes[part][2]
        # SVG Y is inverted so the origin in the plate drawing is front-left.
        sy = bed_d - y - d
        fill = next(color for key, color in palette.items() if key in part)
        lines.append(
            f'<rect x="{x}" y="{sy}" width="{w}" height="{d}" fill="{fill}" fill-opacity="0.75" stroke="#0f172a" stroke-width="0.6"/>'
        )
        label = labels.get(part, part.replace("_", " "))
        lines.append(
            f'<text x="{x + w / 2}" y="{sy + d / 2 + 1.5}" font-family="sans-serif" font-size="5" text-anchor="middle" '
            f'fill="#0f172a">{label}</text>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n")
