"""Provisional closed-slide assembly, using the actual printable shim shape.

Rail cross-sections and side-slot positions are visualization parameters, not
manufacturer CAD or a drilling pattern. Fasteners are a proposed custom joint,
not a reconstruction of the manufacturer's mounting holes or supplied screws.
"""

from itertools import combinations
import json
import math

import cadquery as cq
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Patch
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import rail_shelf_shims as shims
from shelf_interfaces import SIDE_SLOT_LENGTH, SIDE_SLOT_WIDTH


SHIM = shims.Shim(2.0)  # representative thickness, NOT a measured gap
# Owner confirms two side mounting slots at each end, on both sides.
# Exact spacing is unmeasured. Keep the hole pattern separate from shim sites:
# one slot per pair locates a shim; its companion stays open for metal fastening.
FRONT_SLOT_Y = (100.0, 150.0)
REAR_SLOT_Y = (550.0, 600.0)
SLOT_Y = FRONT_SLOT_Y + REAR_SLOT_Y
SHIM_Y = (FRONT_SLOT_Y[0], REAR_SLOT_Y[-1])
OPEN_SLOT_Y = tuple(y for y in SLOT_Y if y not in SHIM_Y)
SIDE_HEIGHT = 44.0
CENTER_Z = -22.0
SLOT_LENGTH, SLOT_WIDTH = SIDE_SLOT_LENGTH, SIDE_SLOT_WIDTH
# Owner confirms rails are longer than the 700 mm shelf. Neither the kit guide
# nor the part-number suffix establishes a closed length. This 800 mm display
# envelope is explicitly UNMEASURED. Center it on the shelf as requested;
# changing its length preserves equal front/rear overhang automatically.
# Do not confuse body length, bracket span and extension travel.
RAIL_LENGTH = 800.0
INNER_HEIGHT, OUTER_HEIGHT = 28.0, 36.0
RAIL_METAL_T = 1.5
INNER_DEPTH, OUTER_DEPTH = 5.0, 11.5
SCREW_D, SCREW_LENGTH = 4.0, 12.0
RAIL_HOLE_D = 4.5
HEAD_D, HEAD_HEIGHT, HEX_KEY_AF = 7.6, 2.2, 2.5
NUT_AF, NUT_HEIGHT, THREAD_PITCH = 7.0, 3.2, .7
WASHER_OD, WASHER_ID, WASHER_T = 12.0, 4.3, 1.0
GAP_WASHERS = 2
# Keep >=1 mm between a moving washer and the neighboring printed pad. The
# screw alone permits +/-18 mm, but the complete joint is limited to +/-17 mm.
MOUNT_TRAVEL = 17.0
COLORS = {"sidewall": (.48, .52, .57), "inner": (.68, .72, .77),
          "outer": (.33, .39, .46), "shim": (.15, .76, .68),
          "screw": (.91, .57, .18), "washer": (.78, .66, .43),
          "nut": (.91, .57, .18)}

SOURCES = {
    "shelf_drawing": "https://sgcdn.startech.com/005329/media/sets/ADJSHELFHDV_Diagram/ADJSHELFHDV_Diagram.PDF",
    "rail_installation_only": "https://download.gigabyte.com/FileList/Manual/server_system_qig_25HB2-3A0202-K0R.pdf",
    "button_head_envelope": "https://www.blohm-gmbh.de/de/en/Products/Product-overview/Machine-and-fixture-components/Screws-nuts-and-washers/Button-head-screws-EN-ISO-7380.html",
    "washer": "https://www.pgb-europe.com/en-gb/205267/flat-washer-din-9021-m-4-a4-43-12-10",
    "nut": "https://www.pgb-europe.com/en-gb/242836/hexagon-nut-din-934-m-4-a2-70",
}


def box(x, y, z, w, d, h):
    return (cq.Workplane("XY").box(w, d, h, centered=False)
            .translate((x, y, z)).val())


def axial(x, y):
    return cq.Workplane(cq.Plane(origin=(x, y, CENTER_Z), xDir=(0, 1, 0), normal=(1, 0, 0)))


def mounting_joint(y, shelf_thickness):
    """Metal-to-metal stack, head in rail channel, nut inside shelf.

    Smooth nominal thread envelopes avoid fictitious thread collisions. The
    nut bore is a display clearance, not a tap-drill recommendation.
    """
    under_head = -SHIM.thickness - RAIL_METAL_T
    head = (axial(under_head - HEAD_HEIGHT, y).circle(HEAD_D / 2)
            .extrude(HEAD_HEIGHT).edges("<X").fillet(.9))
    socket = (axial(under_head - HEAD_HEIGHT - .01, y)
              .polygon(6, HEX_KEY_AF / math.cos(math.pi / 6)).extrude(1.31))
    shaft = axial(under_head, y).circle(SCREW_D / 2).extrude(SCREW_LENGTH)
    screw = head.cut(socket).union(shaft).val()
    parts = [("M4x12_button_screw", "screw", screw)]
    for i in range(GAP_WASHERS):
        washer = (axial(-SHIM.thickness + i * WASHER_T, y)
                  .circle(WASHER_OD / 2).circle(WASHER_ID / 2).extrude(WASHER_T).val())
        parts.append((f"gap_washer_{i + 1}", "washer", washer))
    backing = (axial(shelf_thickness, y).circle(WASHER_OD / 2)
               .circle(WASHER_ID / 2).extrude(WASHER_T).val())
    parts.append(("shelf_backing_washer", "washer", backing))
    nut = (axial(shelf_thickness + WASHER_T, y)
           .polygon(6, NUT_AF / math.cos(math.pi / 6)).circle((SCREW_D + .02) / 2)
           .extrude(NUT_HEIGHT).val())
    parts.append(("M4_hex_nut", "nut", nut))
    return [(f"mount_Y{y:g}_{n}", k, s) for n, k, s in parts]


def rail_start_y(shelf_depth):
    """Keep the shelf datum and holes fixed; center the rails along its depth."""
    return (shelf_depth - RAIL_LENGTH) / 2


def channel(face_x, depth, height, opens_outward, rail_y):
    """Simple nested C-sections; ball races, stops and locks are not represented."""
    z = CENTER_Z - height / 2
    web_x = face_x - RAIL_METAL_T if opens_outward else face_x - depth
    web = box(web_x, rail_y, z, RAIL_METAL_T, RAIL_LENGTH, height)
    flanges = [box(face_x - depth, rail_y, zz, depth, RAIL_LENGTH, RAIL_METAL_T)
               for zz in (z, z + height - RAIL_METAL_T)]
    return web.fuse(*flanges).clean()


def build(shelf_width, shelf_depth, shelf_thickness):
    rail_y = rail_start_y(shelf_depth)
    assert math.isfinite(rail_y) and math.isfinite(RAIL_LENGTH)
    assert RAIL_LENGTH > shelf_depth, "owner confirms rail envelope is longer than shelf"
    assert math.isclose(GAP_WASHERS * WASHER_T, SHIM.thickness), "metal gap stack must match shim"
    assert SCREW_D < RAIL_HOLE_D < HEAD_D
    assert WASHER_ID > SCREW_D and WASHER_OD > SLOT_WIDTH
    grip = RAIL_METAL_T + SHIM.thickness + shelf_thickness + WASHER_T + NUT_HEIGHT
    assert SCREW_LENGTH - grip >= 2 * THREAD_PITCH, "full nut engagement plus two threads"
    assert MOUNT_TRAVEL < (SLOT_LENGTH - SCREW_D) / 2
    assert SHIM.thickness in shims.TRIAL_THICKNESSES
    assert SLOT_LENGTH > SHIM.locator_length and SLOT_WIDTH > SHIM.locator_width
    assert SHIM.locator_height > shelf_thickness
    assert SHIM.height < INNER_HEIGHT - 2 * RAIL_METAL_T
    assert INNER_HEIGHT < OUTER_HEIGHT - 2 * RAIL_METAL_T
    assert -SIDE_HEIGHT < CENTER_Z - OUTER_HEIGHT / 2
    assert CENTER_Z + OUTER_HEIGHT / 2 < -shelf_thickness
    assert len(FRONT_SLOT_Y) == len(REAR_SLOT_Y) == 2
    assert len(set(SLOT_Y)) == 4 and len(SHIM_Y) == 2
    assert all(y < shelf_depth / 2 for y in FRONT_SLOT_Y)
    assert all(y > shelf_depth / 2 for y in REAR_SLOT_Y)
    for y in SLOT_Y:
        assert 0 < y - SLOT_LENGTH / 2 < y + SLOT_LENGTH / 2 < shelf_depth
        assert rail_y < y - SLOT_LENGTH / 2 < y + SLOT_LENGTH / 2 < rail_y + RAIL_LENGTH
    for y in SHIM_Y:
        assert rail_y < y - SHIM.width / 2 < y + SHIM.width / 2 < rail_y + RAIL_LENGTH
        for open_y in OPEN_SLOT_Y:
            assert abs(open_y - y) > (SHIM.width + SLOT_LENGTH) / 2, "leave companion slot outside pad footprint"

    wall = box(0, 0, -SIDE_HEIGHT, shelf_thickness, shelf_depth,
               SIDE_HEIGHT - shelf_thickness)
    cut_plane = cq.Plane(origin=(-1, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))
    for y in SLOT_Y:
        cutter = (cq.Workplane(cut_plane).center(y, CENTER_Z)
                  .slot2D(SLOT_LENGTH, SLOT_WIDTH).extrude(shelf_thickness + 2).val())
        wall = wall.cut(cutter)

    inner = channel(-SHIM.thickness, INNER_DEPTH, INNER_HEIGHT, True, rail_y)
    for y in OPEN_SLOT_Y:
        cutter = axial(-SHIM.thickness - INNER_DEPTH - 1, y).circle(RAIL_HOLE_D / 2).extrude(INNER_DEPTH + 2).val()
        inner = inner.cut(cutter)
    left = [("sidewall_with_illustrative_slots", "sidewall", wall),
            ("inner_slide_with_proposed_mounting_holes", "inner", inner),
            ("outer_slide_closed", "outer", channel(-SHIM.thickness, OUTER_DEPTH, OUTER_HEIGHT, False, rail_y))]
    prototype = shims.build(SHIM).val()
    for i, y in enumerate(SHIM_Y, 1):
        # Local X follows the long shelf slot; local Z points inward through steel.
        plane = cq.Plane(origin=(-SHIM.thickness, y - SHIM.width / 2,
                                 CENTER_Z - SHIM.height / 2),
                         xDir=(0, 1, 0), normal=(1, 0, 0))
        left.append((f"{SHIM.name}_{i}", "shim", prototype.moved(cq.Location(plane))))
    for y in OPEN_SLOT_Y:
        left.extend(mounting_joint(y, shelf_thickness))
    entries = []
    for side in ("left", "right"):
        for name, kind, shape in left:
            if side == "right":
                shape = shape.mirror("YZ", (shelf_width / 2, 0, 0))
            assert shape.isValid() and len(shape.Solids()) == 1, name
            if kind in {"inner", "outer"}:
                bounds = shape.BoundingBox()
                assert math.isclose((bounds.ymin + bounds.ymax) / 2, shelf_depth / 2), "rail must be centered on shelf"
                assert math.isclose(-bounds.ymin, bounds.ymax - shelf_depth), "equal front/rear rail overhang"
            entries.append((f"{side}_{name}_PROVISIONAL", kind, shape))
    return entries


def _bbox_overlap(a, b):
    return all(min(getattr(a, axis + "max"), getattr(b, axis + "max")) -
               max(getattr(a, axis + "min"), getattr(b, axis + "min")) > 1e-6
               for axis in "xyz")


def check_mounts(entries, existing, width, shelf_thickness):
    """Validate proposed hardware, useful slot adjustment and assembly access."""
    moving_kinds = {"inner", "outer", "screw", "washer", "nut"}
    fixed = [(n, s) for n, k, s in entries if k not in moving_kinds] + existing
    # Continuous conservative envelopes cover every point between adjustment
    # limits, not only sampled positions. Split each screw at its shoulder so
    # its head diameter is not incorrectly carried through the shelf slot.
    swept_checks = 0
    for name, kind, shape in entries:
        if kind not in moving_kinds:
            continue
        bounds = [shape.BoundingBox()]
        if kind == "screw":
            y = shape.Center().y
            under_head = -SHIM.thickness - RAIL_METAL_T
            pieces = [box(under_head - HEAD_HEIGHT, y - HEAD_D / 2, CENTER_Z - HEAD_D / 2,
                          HEAD_HEIGHT, HEAD_D, HEAD_D),
                      box(under_head, y - SCREW_D / 2, CENTER_Z - SCREW_D / 2,
                          SCREW_LENGTH, SCREW_D, SCREW_D)]
            if name.startswith("right_"):
                pieces = [p.mirror("YZ", (width / 2, 0, 0)) for p in pieces]
            bounds = [p.BoundingBox() for p in pieces]
        for b in bounds:
            envelope = box(b.xmin, b.ymin - MOUNT_TRAVEL, b.zmin,
                           b.xlen, b.ylen + 2 * MOUNT_TRAVEL, b.zlen)
            for other_name, other in fixed:
                if _bbox_overlap(envelope.BoundingBox(), other.BoundingBox()):
                    assert envelope.intersect(other).Volume() < .01, (name, other_name, "continuous adjustment envelope collision")
                    swept_checks += 1
    travel_checks = 0
    for dy in (-MOUNT_TRAVEL, MOUNT_TRAVEL):
        for name, kind, shape in entries:
            if kind not in moving_kinds:
                continue
            moved = shape.translate((0, dy, 0))
            for other_name, other in fixed:
                if _bbox_overlap(moved.BoundingBox(), other.BoundingBox()):
                    assert moved.intersect(other).Volume() < .01, (name, other_name, dy, "mount adjustment collision")
                    travel_checks += 1
    tool_checks = 0
    swept_tool_checks = 0
    clearances = []
    for side in ("left", "right"):
        by_name = {n: s for n, _, s in entries if n.startswith(side + "_")}
        wall = next(s for n, k, s in entries if n.startswith(side + "_") and k == "sidewall")
        inner = next(s for n, k, s in entries if n.startswith(side + "_") and k == "inner")
        outer = next(s for n, k, s in entries if n.startswith(side + "_") and k == "outer")
        for y in OPEN_SLOT_Y:
            prefix = f"{side}_mount_Y{y:g}_"
            def part(suffix):
                return by_name[prefix + suffix + "_PROVISIONAL"]
            screw = part("M4x12_button_screw")
            gap = [part(f"gap_washer_{i + 1}") for i in range(GAP_WASHERS)]
            backing, nut = part("shelf_backing_washer"), part("M4_hex_nut")
            stack = [screw, inner, *gap, wall, backing, nut]
            for a, b in zip(stack, stack[1:]):
                assert a.distance(b) < 1e-6, (prefix, "disconnected metal clamp stack")
            clearances.append(screw.distance(outer))
            assert clearances[-1] > 1, (prefix, "screw head must clear outer section")
            for dy in (-MOUNT_TRAVEL, 0, MOUNT_TRAVEL):
                # Outer rails must be detached: their webs block the screw key.
                # 6 mm driver shaft and hollow 11 mm OD nut socket envelopes.
                under_head = -SHIM.thickness - RAIL_METAL_T
                driver = axial(under_head - HEAD_HEIGHT - 40, y + dy).circle(3).extrude(40).val()
                socket = (axial(shelf_thickness + WASHER_T, y + dy)
                          .circle(5.5).circle(4.5).extrude(40).val())
                for tool_name, tool in (("driver", driver), ("nut_socket", socket)):
                    if side == "right":
                        tool = tool.mirror("YZ", (width / 2, 0, 0))
                    if dy == 0:
                        b = tool.BoundingBox()
                        swept_tool = box(b.xmin, b.ymin - MOUNT_TRAVEL, b.zmin,
                                         b.xlen, b.ylen + 2 * MOUNT_TRAVEL, b.zlen)
                        for other_name, other in fixed:
                            if _bbox_overlap(swept_tool.BoundingBox(), other.BoundingBox()):
                                assert swept_tool.intersect(other).Volume() < .01, (prefix, tool_name, other_name, "continuous tool access")
                                swept_tool_checks += 1
                    obstacles = existing + [(n, s.translate((0, dy, 0)) if k in moving_kinds else s)
                                             for n, k, s in entries if k != "outer"]
                    for other_name, other in obstacles:
                        if _bbox_overlap(tool.BoundingBox(), other.BoundingBox()):
                            assert tool.intersect(other).Volume() < .01, (prefix, tool_name, other_name, "tool access")
                            tool_checks += 1
    return {
        "mount_adjustment_endpoints_mm": [-MOUNT_TRAVEL, MOUNT_TRAVEL],
        "adjustment_boolean_pairs": travel_checks,
        "continuous_adjustment_envelope_pairs": swept_checks,
        "continuous_adjustment_method": "conservative swept bounding volumes against fixed shelf, shims and existing assembly; screw head and shaft treated separately",
        "tool_boolean_pairs": tool_checks,
        "continuous_tool_envelope_pairs": swept_tool_checks,
        "driver_diameter_mm": 6.0, "nut_socket_outer_diameter_mm": 11.0,
        "tool_reach_mm": 40.0,
        "tool_access_condition": "inner slide detached from outer rail; tighten before reinsertion",
        "minimum_head_to_schematic_outer_rail_mm": min(clearances),
        "washer_land_each_side_of_slot_mm": (WASHER_OD - SLOT_WIDTH) / 2,
        "all_metal_stack_contacts": True,
    }


def add_to_assembly(assembly, shelf_width, shelf_depth, shelf_thickness, out):
    rail_y = rail_start_y(shelf_depth)
    entries = build(shelf_width, shelf_depth, shelf_thickness)
    # Audit all existing placed CAD solids, including underside hardware. These
    # checks validate the illustrative placement, not the unknown real interfaces.
    existing = [(name, shape.moved(loc)) for shape, name, loc, _ in assembly]
    checks = 0
    for name, _, shape in entries:
        for other_name, other in existing:
            if _bbox_overlap(shape.BoundingBox(), other.BoundingBox()):
                assert shape.intersect(other).Volume() < .01, (name, other_name, "rail assembly collision")
                checks += 1
    for (name, _, shape), (other_name, _, other) in combinations(entries, 2):
        if _bbox_overlap(shape.BoundingBox(), other.BoundingBox()):
            assert shape.intersect(other).Volume() < .01, (name, other_name, "rail assembly self-collision")
            checks += 1
    for side in ("left", "right"):
        side_entries = [(n, k, s) for n, k, s in entries if n.startswith(side + "_")]
        wall = next(s for _, k, s in side_entries if k == "sidewall")
        inner = next(s for _, k, s in side_entries if k == "inner")
        for name, kind, shape in side_entries:
            if kind == "shim":
                assert shape.distance(wall) < 1e-6, (name, "pad must seat on shelf")
                assert shape.distance(inner) < 1e-6, (name, "flat face must contact inner slide")

    mount_checks = check_mounts(entries, existing, shelf_width, shelf_thickness)

    group = cq.Assembly(name="rail_and_shim_placement_PROVISIONAL")
    for name, kind, shape in entries:
        group.add(shape, name=name, color=cq.Color(*COLORS[kind]))
    assembly.add(group)
    report = {
        "status": "Illustrative closed-slide assembly; unmeasured interfaces, not a drilling or installation release",
        "main_assembly": "kenshin-berserk-6u-shelf-envelope.step",
        "source": "cad/rail_shelf_assembly.py",
        "references": SOURCES,
        "rail_identity_reference": "King Slide 3A02-600 / Gigabyte 25HB2-3A0202-K0R; schematic C-sections only, not manufacturer geometry",
        "dimension_basis": {
            "shelf_width_depth": "446 x 700 mm nominal published shelf body",
            "sidewall": "44 mm nominal published overall height used as a simplified downward sidewall; fold shape and 1.2 mm steel thickness are provisional",
            "slot_pattern": "Owner confirms two slots at the front and two at the back on each side, one behind the other along shelf depth; eight total.",
            "slot_size": "40 x 6.5 mm: manufacturer-dimensioned deck vents, with matching side-hole dimensions confirmed by owner. Actual aperture tolerances remain unmeasured.",
            "rail_length": "Owner confirms rails exceed the 700 mm shelf depth. 800 mm is an unmeasured display envelope, not a published or inferred length; 600 in the rail model name is not used as a length specification.",
            "rail_alignment": "Owner requests shelf centered along the rails; equal front/rear overhang, with shelf, slots and fasteners kept at their existing coordinates. Custom rail holes may be drilled to suit.",
            "rail_and_positions": "Rail sections and numeric slot/screw coordinates remain chosen visualization parameters, not measurements or rack-standard dimensions",
        },
        "closed_rail_envelope_each_mm": {"length_y": RAIL_LENGTH, "depth_x": OUTER_DEPTH,
                                        "height_z": OUTER_HEIGHT, "start_y": rail_y,
                                        "end_y": rail_y + RAIL_LENGTH, "provisional": True},
        "shelf_depth_mm": shelf_depth,
        "shelf_and_rail_center_y_mm": shelf_depth / 2,
        "rail_hole_centers_from_front_mm": [y - rail_y for y in OPEN_SLOT_Y],
        "illustrative_overhang_mm": {"front": max(0, -rail_y),
                                     "rear": max(0, rail_y + RAIL_LENGTH - shelf_depth)},
        "rail_dimensions_unresolved": ["actual inner and outer section lengths", "adjustable rack-bracket span and end offsets", "extension travel"],
        "inner_rail_height_mm": INNER_HEIGHT,
        "rail_sheet_thickness_mm": RAIL_METAL_T,
        "shelf_side_height_mm": SIDE_HEIGHT,
        "inner_slide_face_separation_mm": shelf_width + 2 * SHIM.thickness,
        "shim_model": SHIM.name,
        "illustrative_shim_instances": len(SHIM_Y) * 2,
        "shim_pad_thickness_mm": SHIM.thickness,
        "side_slots_per_side": len(SLOT_Y),
        "total_side_slots": len(SLOT_Y) * 2,
        "front_slot_centers_y_mm": FRONT_SLOT_Y,
        "rear_slot_centers_y_mm": REAR_SLOT_Y,
        "screw_slot_centers_y_mm": OPEN_SLOT_Y,
        "shim_centers_y_mm": SHIM_Y,
        "shim_center_z_mm": CENTER_Z,
        "nominal_side_slot_mm": [SLOT_LENGTH, SLOT_WIDTH],
        "ridge_direction": "inward, through unused side slots; long axis follows shelf Y",
        "ridge_clearance_beyond_inner_wall_mm": SHIM.locator_height - shelf_thickness,
        "proposed_mounting": {
            "status": "Custom prototype layout, not factory rail-hole data or a drilling release; no purchased hardware change",
            "hole_count": 2 * len(OPEN_SLOT_Y), "rail_hole_diameter_mm": RAIL_HOLE_D,
            "hole_centers_y_mm_each_side": OPEN_SLOT_Y, "hole_center_z_mm": CENTER_Z,
            "screws": {"type": "M4 x 12 button head, ISO 7380-1 envelope", "quantity": 4,
                       "head_diameter_mm": HEAD_D, "head_height_mm": HEAD_HEIGHT},
            "nuts": {"type": "M4 hex, DIN 934 envelope", "quantity": 4,
                     "across_flats_mm": NUT_AF, "height_mm": NUT_HEIGHT},
            "washers": {"type": "M4 large washer, DIN 9021 envelope", "quantity": 12,
                        "OD_ID_thickness_mm": [WASHER_OD, WASHER_ID, WASHER_T],
                        "per_joint": "two washers bridge the 2 mm gap, one backs the shelf slot inside"},
            "stack_order_from_outside": ["screw head", "inner rail 1.5", "metal gap washers 2 x 1", "shelf 1.2", "backing washer 1", "nut 3.2"],
            "under_head_to_nut_end_mm": RAIL_METAL_T + SHIM.thickness + shelf_thickness + WASHER_T + NUT_HEIGHT,
            "screw_past_nut_mm": SCREW_LENGTH - RAIL_METAL_T - SHIM.thickness - shelf_thickness - WASHER_T - NUT_HEIGHT,
            "thread_model": "Smooth nominal envelopes, no helical thread or tap-drill representation",
            "adjustment_mm": [-MOUNT_TRAVEL, MOUNT_TRAVEL],
            "checks": mount_checks,
        },
        "print_quantity": "Plate 15 remains one of each trial thickness. Four display instances do not establish installed quantity or change the print manifest.",
        "checks": {"valid_single_solids": len(entries), "boolean_collision_pairs": checks,
                   "existing_assembly_items_screened": len(existing),
                   "positive_volume_collisions": 0, "both_pad_faces_seated": True},
        "not_validated": ["actual sidewall folds, slot tolerances and positions", "actual rail section and rack fit",
                          "actual fastener fit, torque, locking method and metal load capacity", "real moving races, slide motion, locks and end stops",
                          "load capacity, pad compression and creep"],
        "instances": [{"name": name, "kind": kind,
                       "model": SHIM.name if kind == "shim" else "proposed fastener envelope" if kind in {"screw", "washer", "nut"} else "schematic metal reference"}
                      for name, kind, _ in entries],
    }
    (out / "rail-shelf-assembly-report.json").write_text(json.dumps(report, indent=2) + "\n")
    preview(entries, shelf_width, shelf_depth, shelf_thickness, out)
    return report


def _draw(ax, shape, color):
    vertices, faces = shape.tessellate(.15, .15)
    points = np.asarray([v.toTuple() for v in vertices])
    triangles = points[np.asarray(faces)]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
    el, az = np.radians((ax.elev, ax.azim))
    direction = np.array((np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)))
    visible = normals @ direction > 1e-7
    triangles, normals = triangles[visible], normals[visible]
    light = np.array((-.4, -.5, .9))
    light /= np.linalg.norm(light)
    shades = .65 + .35 * np.clip(normals @ light, 0, 1)
    ax.add_collection3d(Poly3DCollection(triangles, facecolors=shades[:, None] * color,
                                       edgecolors="none", linewidths=0, antialiaseds=False))


def preview(entries, width, depth, thickness, out):
    rail_y = rail_start_y(depth)
    fig = plt.figure(figsize=(13, 7))
    overall = fig.add_subplot(121, projection="3d")
    overall.view_init(elev=-28, azim=-65)
    for _, kind, shape in entries:
        _draw(overall, shape, np.array(COLORS[kind]))
    # Deck outline keeps the added side hardware visible from below.
    overall.plot([0, width, width, 0, 0], [0, 0, depth, depth, 0], [0] * 5, color=".5", lw=1)
    y_min, y_max = min(0, rail_y) - 10, max(depth, rail_y + RAIL_LENGTH) + 10
    overall.set(xlim=(-20, width + 20), ylim=(y_min, y_max), zlim=(-50, 10))
    overall.set_box_aspect((width + 40, y_max - y_min, 60))
    overall.set_proj_type("ortho")
    overall.set_axis_off()
    overall.set_title("Closed rails · underside view\nFour shims and four proposed metal joints", fontsize=13)

    detail = fig.add_subplot(122, projection="3d")
    detail.view_init(elev=22, azim=-105)
    detail_half_length = SHIM.width / 2 + 4
    clip = box(-30, SHIM_Y[0] - detail_half_length, -48, 45, 2 * detail_half_length, 48)
    for name, kind, shape in entries:
        if not name.startswith("left_"):
            continue
        cropped = shape.intersect(clip)
        if cropped.Volume() < .01:
            continue
        # Explosion is only in this preview; the STEP contains seated parts.
        dx = {"sidewall": 0, "shim": -18, "inner": -35, "outer": -65,
              "screw": -35, "washer": 0, "nut": 0}[kind]
        _draw(detail, cropped.translate((dx, 0, 0)), np.array(COLORS[kind]))
    detail.set(xlim=(-85, 6), ylim=(SHIM_Y[0] - detail_half_length, SHIM_Y[0] + detail_half_length), zlim=(-46, 0))
    detail.set_box_aspect((91, 2 * detail_half_length, 46), zoom=1.15)
    detail.set_proj_type("ortho")
    detail.set_axis_off()
    detail.set_title("Exploded detail · spacing enlarged here only\nOuter rail → inner rail → shim → shelf side", fontsize=13)
    fig.suptitle("Rails and locating shims in the assembly STEP", fontsize=19)
    fig.text(.5, .075, "Green: actual printable shim geometry. Grey: provisional metal reference geometry.\n"
             f"Shelf centered on rails: {(RAIL_LENGTH - depth) / 2:g} mm overhang at each end in this unmeasured {RAIL_LENGTH:g} mm rail model.",
             ha="center", fontsize=11)
    fig.subplots_adjust(top=.82, bottom=.17, left=.01, right=.99, wspace=.04)
    fig.savefig(out / "rail-shelf-assembly.png", dpi=160)
    plt.close(fig)

    # Unobscured side elevation of the generated steel face makes the actual
    # four-hole pattern reviewable; the assembled slides otherwise hide it.
    fig, ax = plt.subplots(figsize=(13, 3))
    wall = next(shape for name, kind, shape in entries if name.startswith("left_") and kind == "sidewall")
    for face in wall.Faces():
        if face.BoundingBox().xlen < 1e-6 and abs(face.Center().x) < 1e-6:
            vertices, faces = face.tessellate(.1, .1)
            yz = np.asarray([(v.y, v.z) for v in vertices])
            ax.add_collection(PolyCollection(yz[np.asarray(faces)], facecolors="#737d89",
                                             edgecolors="none", antialiaseds=False))
    for y in SHIM_Y:
        ax.add_patch(FancyBboxPatch((y - SHIM.width / 2, CENTER_Z - SHIM.height / 2),
                     SHIM.width, SHIM.height,
                     boxstyle=f"round,pad=0,rounding_size={SHIM.height / 2}",
                     facecolor="none", edgecolor="#13b59e", linestyle="--", linewidth=2))
    for pair, label in ((FRONT_SLOT_Y, "Front pair"), (REAR_SLOT_Y, "Rear pair")):
        ax.text(sum(pair) / 2, 5, label, ha="center", va="bottom", fontsize=12)
    for y in SLOT_Y:
        role = "Shim" if y in SHIM_Y else "M4 screw"
        ax.text(y, -51, f"{role}\nY{y:g}", ha="center", va="top", fontsize=10)
    ax.text(0, -5, "Front", ha="left", va="bottom", fontsize=10)
    ax.text(depth, -5, "Rear", ha="right", va="bottom", fontsize=10)
    ax.set(xlim=(-5, depth + 5), ylim=(-78, 18), aspect="equal")
    ax.set_axis_off()
    fig.suptitle("Each shelf side: two front slots + two rear slots", fontsize=17)
    fig.text(.5, .09, "Dashed green: shim footprint. Companion slots take the proposed metal mounting joints.\n"
             "40 × 6.5 mm slots match deck vents, as confirmed by owner; numeric positions remain provisional.",
             ha="center", fontsize=10)
    fig.subplots_adjust(top=.84, bottom=.25, left=.035, right=.965)
    fig.savefig(out / "shelf-side-mounting-pattern.png", dpi=170)
    plt.close(fig)
    mounting_preview(entries, depth, thickness, out)


def mounting_preview(entries, depth, thickness, out):
    rail_y = rail_start_y(depth)
    fig = plt.figure(figsize=(13, 8))
    grid = fig.add_gridspec(2, 2, height_ratios=(1, 1.2), width_ratios=(1.2, 1))
    pattern = fig.add_subplot(grid[0, :])
    pattern.add_patch(Rectangle((0, -44), depth, 44, facecolor="#dde1e5", edgecolor="#737d89"))
    for y in SLOT_Y:
        pattern.add_patch(FancyBboxPatch((y - SLOT_LENGTH / 2, CENTER_Z - SLOT_WIDTH / 2),
                          SLOT_LENGTH, SLOT_WIDTH, boxstyle=f"round,pad=0,rounding_size={SLOT_WIDTH / 2}",
                          facecolor="white", edgecolor="#626e7c"))
    for y in SHIM_Y:
        pattern.add_patch(FancyBboxPatch((y - SHIM.width / 2, CENTER_Z - SHIM.height / 2),
                          SHIM.width, SHIM.height, boxstyle=f"round,pad=0,rounding_size={SHIM.height / 2}",
                          facecolor="none", edgecolor="#13b59e", linewidth=2))
    rail_z = -90
    pattern.add_patch(Rectangle((rail_y, rail_z - INNER_HEIGHT / 2), RAIL_LENGTH, INNER_HEIGHT,
                               facecolor="#aeb8c4", edgecolor="#626e7c"))
    for y in OPEN_SLOT_Y:
        pattern.add_patch(Circle((y, rail_z), RAIL_HOLE_D / 2, facecolor="white", edgecolor="#a65c0c"))
        pattern.plot([y, y], [CENTER_Z, rail_z], color="#c58226", linestyle="--", lw=1)
        pattern.annotate(f"Ø{RAIL_HOLE_D:g} at Y{y:g}", (y, rail_z), (y + 27, rail_z - 44),
                         arrowprops={"arrowstyle": "->", "color": "#a65c0c"}, fontsize=10)
    for y, length, label in ((15, depth, f"Shelf: {depth:g} mm · manufacturer drawing"),
                              (-155, RAIL_LENGTH, f"Rail display: {RAIL_LENGTH:g} mm · UNMEASURED placeholder")):
        start = 0 if y > 0 else rail_y
        pattern.annotate("", (start, y), (start + length, y), arrowprops={"arrowstyle": "<->", "color": "#4b5563"})
        pattern.text(start + length / 2, y + (6 if y > 0 else -6), label,
                     ha="center", va="bottom" if y > 0 else "top", fontsize=11)
    pattern.text(rail_y + RAIL_LENGTH + 8, rail_z, "Inner rail\n(separated for view)", va="center", fontsize=10)
    for start, end in ((rail_y, 0), (depth, rail_y + RAIL_LENGTH)):
        pattern.annotate("", (start, -57), (end, -57), arrowprops={"arrowstyle": "<->", "color": "#4b5563"})
        pattern.text((start + end) / 2, -52, f"{end - start:g} mm", ha="center", fontsize=9)
    pattern.set(xlim=(min(0, rail_y) - 10, max(depth, rail_y + RAIL_LENGTH) + 130), ylim=(-185, 45), aspect="equal")
    pattern.set_axis_off()
    pattern.set_title("Shelf centered on rails · existing shelf holes and screw positions retained", fontsize=13, pad=12)

    section = fig.add_subplot(grid[1, 0])
    y = OPEN_SLOT_Y[0]
    clip = box(-16, y - .01, CENTER_Z - 20, 30, .02, 40)
    for name, kind, shape in entries:
        if not name.startswith("left_"):
            continue
        cut = shape.intersect(clip)
        if cut.Volume() < 1e-5:
            continue
        vertices, faces = cut.tessellate(.04, .1)
        xz = np.asarray([(v.x, v.z - CENTER_Z) for v in vertices])
        section.add_collection(PolyCollection(xz[np.asarray(faces)], facecolors=COLORS[kind],
                                              edgecolors="none", antialiaseds=False))
    section.set(xlim=(-15, 11), ylim=(-8, 8), aspect="equal", xlabel="Across shelf side, mm", ylabel="Above screw axis, mm")
    section.set_title("Actual CAD section through a screw", fontsize=13)
    section.grid(alpha=.15)
    section.legend(handles=[Patch(color=COLORS[k], label=l) for k, l in
                           (("inner", "Inner rail"), ("sidewall", "Shelf"), ("screw", "Screw / nut"), ("washer", "Steel washers"))],
                   loc="lower center", bbox_to_anchor=(.5, -.47), ncol=2, frameon=False, fontsize=10)
    notes = fig.add_subplot(grid[1, 1])
    notes.set_axis_off()
    grip = RAIL_METAL_T + SHIM.thickness + thickness + WASHER_T + NUT_HEIGHT
    notes.text(0, .95,
               "4 × M4 × 12 button-head screws\n4 × M4 hex nuts · 12 × Ø12 × 1 washers\n\n"
               "Clamp stack, outside → inside\n"
               f"1.5 rail + 2 metal gap + {thickness:g} shelf\n+ 1 backing washer + 3.2 nut = {grip:g} mm\n"
               f"Screw extends {SCREW_LENGTH - grip:.1f} mm beyond nut.\n\n"
               f"Mounting adjustment: ±{MOUNT_TRAVEL:g} mm along slots.\n"
               "Detach inner rails to tighten screws.\n"
               "Printed shims stay in the neighboring slots.\n\n"
               "Proposed hardware; real rail holes, moving races,\n"
               "gap and thicknesses still need confirmation.",
               va="top", fontsize=11, linespacing=1.4)
    fig.suptitle("Rail-to-shelf mounting · review model", fontsize=19)
    fig.subplots_adjust(top=.89, bottom=.16, left=.06, right=.98, hspace=.45, wspace=.22)
    fig.savefig(out / "rail-shelf-mounting.png", dpi=170)
    plt.close(fig)
