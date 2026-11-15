"""Printed two-section ATX motherboard mount on a steel shelf (designed for AIPC).

Two braced, interlocking 6 mm sections sit under a 305 x 244-class board.
Full-depth drop-in dovetails locate X/Y, not Z. Independent shelf bolts retain
each section; GPU post bases pass through the rail at the I/O edge and seat
directly on the steel. Under-PCB anchors go in before the motherboard.

The geometry is built in the board's own frame (I/O edge toward +Y), so any
build can place the same sections under its board. The library models
(``h12d_mobo_adapter_rail``, ``atx_mobo_adapter_front``) are exported by AIPC;
other builds compare their copy with those models instead of exporting.
"""

import cadquery as cq

from hwkit.components import pcie_post as post_hw

THICKNESS = 6.0
CLEARANCE = 0.3
SHELF_SLOT_LENGTH = 8.0
SHELF_TRAVEL = 2.0
BAR_WIDTH = 25.0
EAR_WIDTH = 14.0
EAR_OFFSET = 6.5
SHELF_SLOT_WIDTH = 4.0
WASHER_OD = 7.0
POST_SLOT_LENGTH, POST_SLOT_WIDTH = post_hw.OPENING_LENGTH, post_hw.OPENING_WIDTH
REAR_RAIL_CENTER_Y = 7.5  # keep the outer rail unchanged when locating holes
# ATX2.2 Fig3: mounting datum is10.16mm inside PCB rear edge.
# PCIe CEM2.0 Figs5-1/5-2/6-14: connector key is46.94mm inside that datum.
# Fig6-2: bracket outside flat face is59.05mm behind key -> PCB rear+1.95.
# Fig6-4:0.86mm sheet and5deg outward bend over5.07mm -> tip about+1.53..2.39.
# Use a1..3mm rear-edge groove for nominal fit; tolerance stack needs a dry fit.
ATX_REAR_MOUNT_DATUM = 0.4 * 25.4
PCIE_KEY_FROM_MOUNT_DATUM = 46.94
PCIE_BRACKET_FACE_FROM_KEY = 59.05
PCIE_BRACKET_OUTSIDE_Y = PCIE_BRACKET_FACE_FROM_KEY - PCIE_KEY_FROM_MOUNT_DATUM - ATX_REAR_MOUNT_DATUM
GPU_TAB_RELIEF_DEPTH = 2.0
GPU_TAB_GROOVE_WIDTH = 2.0
GPU_TAB_GROOVE_Y = 2.0  # nominal-fit allowance referenced to PCB edge, not posts
STANDOFF_EDGE_WEB = 4.0
SITES = {
    "A": (0.65, 0.4),
    "B": (3.75, 0.4),
    "C": (5.55, 0.4),
    "F": (11.75, 1.3),
    "G": (0.65, 6.5),
    "H": (5.55, 6.5),
    "J": (11.75, 6.5),
    "K": (0.65, 9.35),
    "L": (5.55, 9.35),
    "M": (11.75, 9.35),
}
# Group names preserve earlier job identities; anchor ends are now reversed.
GROUPS = {"front": ("A", "B", "C", "G", "K"), "rear": ("F", "H", "J", "L", "M")}
ANCHOR_ENDS = {"front": "rear", "rear": "front"}


def box(x0, x1, y0, y1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, THICKNESS, centered=(False, False, False)).translate((x0, y0, 0))


def build(name, x0, y0, w, d, post_x, post_y):
    """Both sections under one 305 x 244-class board, in the board's own frame.

    ``x0`` is the PCB low-X edge, ``y0`` the edge opposite the I/O and
    ``y0 + d`` the I/O edge (toward +Y); Z = 0 is the deck top. ``post_x``
    are post slot offsets from ``x0`` on the rail ``post_y`` beyond the I/O
    edge. Returns ``({'front': frame, 'rear': frame}, joints)``; the caller
    names the sections and turns them into place.
    """
    back = y0 + d
    holes = {k: (x0 + u * 25.4, back - v * 25.4) for k, (u, v) in SITES.items()}
    xa, ya = holes["A"]
    xc, _ = holes["C"]
    xf, yf = holes["F"]
    _, yg = holes["G"]
    _, yk = holes["K"]
    split = x0 + 124
    # Use the same reference depth and anchor pattern for both 305x244-class boards.
    front_y = back - 244.0
    post_slots = [(x0 + u, back + post_y) for u in post_x]
    anchors = {
        "front": [(x0 + u, back - 13) for u in (54.2, 110.0)] + [(x0 + 110.0, yk + 3)],
        "rear": [(x0 + 218, front_y - EAR_OFFSET), (x0 + 297, front_y - EAR_OFFSET)],
    }
    # Optional anchors oppose each section's primary ears; matching side slots
    # provide another simple attachment choice without adding more ears.
    optional = {
        "front": [(x0 + 54.2, yk + 3), (xa + 3.5, (ya + yg) / 2)],
        "rear": [(x0 + 218, yf - 3), (x0 + 260, yf - 3), (xf - 3.5, (yf + yg) / 2)],
    }
    front = box(xa - 9, xc + BAR_WIDTH / 2, ya + 9.5 - BAR_WIDTH, ya + 9.5)
    front = front.union(box(xa - 9, xa - 9 + BAR_WIDTH, yk - 9.5, ya + 9.5))
    for low in (yk - 9.5, yg - BAR_WIDTH / 2):
        front = front.union(box(xa - 9, split, low, low + BAR_WIDTH))
    rear = box(split + CLEARANCE, xf + 9, yk - 9.5, yk - 9.5 + BAR_WIDTH)
    rear = rear.union(box(split + CLEARANCE, xf + 9, yg - BAR_WIDTH / 2, yg + BAR_WIDTH / 2))
    rear = rear.union(box(xc - BAR_WIDTH / 2, xc + BAR_WIDTH / 2, yk - 9.5, yg + 30 - CLEARANCE))
    rear = rear.union(box(xf + 9 - BAR_WIDTH, xf + 9, yk - 9.5, yf + 9.5))
    rear = rear.union(box(x0 + 218 - BAR_WIDTH / 2, xf + 9, yf + 9.5 - BAR_WIDTH, yf + 9.5))
    front = front.union(box(xc - BAR_WIDTH / 2, xc + BAR_WIDTH / 2, yg + 30, ya + 9.5))
    rear = rear.union(box(x0 + 218 - BAR_WIDTH / 2, x0 + 218 + BAR_WIDTH / 2, yg - BAR_WIDTH / 2, yf + 9.5))
    shapes = {"front": front, "rear": rear}
    # One broad 25mm-deep rear rail contains every selectable PCIe post slot.
    # Its last two positions enter the conservative I/O service projection;
    # the 6mm rail sits below the modeled PCB, but actual shield clearance
    # and populated-post locations must be checked on the fitted hardware.
    shapes["front"] = shapes["front"].union(
        box(
            min(xa - 9, post_slots[0][0] - EAR_WIDTH / 2),
            max(xc + BAR_WIDTH / 2, post_slots[-1][0] + EAR_WIDTH / 2),
            back + REAR_RAIL_CENTER_Y + 9 - BAR_WIDTH,
            back + REAR_RAIL_CENTER_Y + 9,
        )
    )
    for x, y in anchors["rear"]:
        shapes["rear"] = shapes["rear"].union(box(x - EAR_WIDTH / 2, x + EAR_WIDTH / 2, y - 8, yk - 9.5 + BAR_WIDTH))
    joints = []

    def joint(cx, cy, axis):
        # 10mm neck /16mm head /8mm engagement, full6mm thickness.
        # The third key turns90 degrees and closes the C-to-H rail.
        local = [(-4, -5), (0, -5), (8, -8), (8, 8), (0, 5), (-4, 5)]
        pts = [(cx + u, cy + v) if axis == "X" else (cx + v, cy - u) for u, v in local]
        wire = cq.Workplane("XY").polyline(pts).close()
        male = wire.extrude(THICKNESS)
        socket = wire.wires().toPending().offset2D(CLEARANCE).extrude(THICKNESS)
        shapes["front"] = shapes["front"].union(male)
        shapes["rear"] = shapes["rear"].cut(socket)
        joints.append(
            {
                "center_xy_mm": [cx, cy],
                "engagement_mm": 8,
                "neck_mm": 10,
                "head_mm": 16,
                "clearance_per_side_mm": CLEARANCE,
                "locates_axes": ["X", "Y"],
                "key_axis": axis,
                "insertion_axis": "Z",
            }
        )

    for cy in (yk + 3, yg):
        joint(split, cy, "X")
    joint(xc, yg + 30, "Y")
    result = {}
    for group, s in shapes.items():
        sites = GROUPS[group]
        slot_width = SHELF_SLOT_WIDTH
        washer_od = WASHER_OD
        for site in sites:
            x, y = holes[site]
            for length, width, height in ((6.0, 3.7, 6.0), (10.8, 8.5, 3.0)):
                s = s.cut(cq.Workplane("XY").center(x, y).slot2D(length, width, 90).extrude(height))
        if group == "front":
            for x, y in post_slots:
                # A true six-sided hole with post_hw.BODY_FACE_CLEARANCE per face.
                # The user requested a snug fit, removing slot adjustment.
                s = s.cut(cq.Workplane("XY").polyline(post_hw.opening_points()).close().extrude(THICKNESS).translate((x, y, 0)))
        for points, length, width in (
            (anchors[group], SHELF_SLOT_LENGTH, slot_width),
            (optional[group], SHELF_SLOT_LENGTH, SHELF_SLOT_WIDTH),
        ):
            for x, y in points:
                s = s.cut(cq.Workplane("XY").center(x, y).slot2D(length, width, 90).extrude(THICKNESS))
        relief = None
        if group == "front":
            inner_y = back + GPU_TAB_GROOVE_Y - GPU_TAB_GROOVE_WIDTH / 2
            outer_y = back + GPU_TAB_GROOVE_Y + GPU_TAB_GROOVE_WIDTH / 2
            bb = s.val().BoundingBox()
            # A narrow rectangular groove keeps the original print orientation:
            # its walls start on the bed and the roof bridges only 2 mm at Z2.
            cutter = (
                cq.Workplane("XY")
                .box(bb.xlen + 2, GPU_TAB_GROOVE_WIDTH, GPU_TAB_RELIEF_DEPTH + 1, centered=(False, False, False))
                .translate((bb.xmin - 1, inner_y, THICKNESS - GPU_TAB_RELIEF_DEPTH))
            )
            # Keep the full thickness around every selectable board screw,
            # including optional B. Do not trade a seated GPU for a weak land.
            lands = []
            for site in sites:
                x, y = holes[site]
                land = cq.Workplane("XY").center(x, y).slot2D(6 + 2 * STANDOFF_EDGE_WEB, 3.7 + 2 * STANDOFF_EDGE_WEB, 90).extrude(THICKNESS)
                lands.append(land)
            # Through-bases carry no load into plastic, so no washer lands
            # interrupt the groove. Point the hex tips toward the PCB:
            # Berserk tips meet the groove without a0.1mm unprintable web;
            # Kenshin's farther-back holes stay separate from the groove.
            original = s.val()
            s = s.cut(cutter)
            assert original.Volume() - s.val().Volume() > 100, (name, "missing GPU tab relief")
            for land in lands:
                assert original.intersect(land.val()).cut(s.val()).Volume() < 0.01, (name, "standoff land")
            assert THICKNESS - GPU_TAB_RELIEF_DEPTH >= 4
            # Each inter-post gap must actually open down to the requested
            # floor, including the region beyond the PCB where tongues land.
            for (lx, _), (rx, _) in zip(post_slots, post_slots[1:], strict=False):
                probe = (
                    cq.Workplane("XY")
                    .center((lx + rx) / 2, back + GPU_TAB_GROOVE_Y)
                    .rect(4, GPU_TAB_GROOVE_WIDTH - 0.02)
                    .extrude(GPU_TAB_RELIEF_DEPTH - 0.02)
                    .translate((0, 0, THICKNESS - GPU_TAB_RELIEF_DEPTH + 0.01))
                )
                assert s.val().intersect(probe.val()).Volume() < 0.01, (name, "GPU tab gap")
            relief = {
                "type": "narrow rectangular groove",
                "depth_mm": GPU_TAB_RELIEF_DEPTH,
                "width_mm": GPU_TAB_GROOVE_WIDTH,
                "remaining_base_thickness_mm": THICKNESS - GPU_TAB_RELIEF_DEPTH,
                "installed_y_range_mm": [inner_y, outer_y],
                "y_range_relative_to_PCB_rear_mm": [inner_y - back, outer_y - back],
                "standard_bracket_outside_face_relative_to_PCB_rear_mm": PCIE_BRACKET_OUTSIDE_Y,
                "standard_datum_chain_mm": {
                    "key_to_bracket_outside_face": PCIE_BRACKET_FACE_FROM_KEY,
                    "mount_datum_to_key": PCIE_KEY_FROM_MOUNT_DATUM,
                    "PCB_rear_to_mount_datum": ATX_REAR_MOUNT_DATUM,
                },
                "standoff_slot_edge_web_mm": STANDOFF_EDGE_WEB,
                "standoff_lands_preserved": True,
                "intersects_post_clearance_slots": back + post_y - POST_SLOT_LENGTH / 2 < outer_y,
                "print_orientation": "original: installed top on bed, screw-head recesses up",
                "print_bridge_span_mm": GPU_TAB_GROOVE_WIDTH,
                "supports_required": False,
                "basis": (
                    "ATX2.2 Fig3 and PCIe CEM2.0 Figs5-1/5-2/6-2/6-14 give nominal bracket outside "
                    "face59.05-46.94-10.16=1.95mm behind PCB rear. Fig6-4 specifies0.86mm sheet and5deg+/-2deg outward "
                    "tongue bend over5.07mm, giving nominal tip about1.53..2.39mm behind PCB. Groove1..3mm is a nominal-"
                    "fit design allowance, not guaranteed full tolerance coverage; depth2mm requested by owner. Actual "
                    "hardware fit remains unmeasured"
                ),
                "sources": [
                    "https://analytika.sk/fileadmin/user_upload/developer_specs_atx2_2.PDF#page=12",
                    "https://tecsmith.github.io/homeassistant-pc-switch/specs/"
                    "pci-express-card-electromechanical-specification-revision-2.pdf#page=85",
                ],
                "physical_fit_verified": False,
                "fit_check": (
                    "Measure seated tab X/Y/Z; check tongues against metal bases and steel deck; print one of each rear "
                    "rail and dry-fit before use"
                ),
            }
        for x, y in anchors[group]:
            if group == "rear":
                assert y + SHELF_TRAVEL + washer_od / 2 <= y0
            else:
                assert y0 <= y - SHELF_TRAVEL - washer_od / 2 and y + SHELF_TRAVEL + washer_od / 2 <= back
                # A complete 4mm web surrounds each independent anchor,
                # including the underside around board screw counterbores.
                web = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .slot2D(16, 12, 90)
                    .extrude(THICKNESS)
                    .cut(cq.Workplane("XY").center(x, y).slot2D(8, 4, 90).extrude(THICKNESS))
                )
                assert web.val().cut(s.val()).Volume() < 0.01, (name, "anchor edge web", x, y)
        assert s.val().isValid() and len(s.solids().vals()) == 1, (name, group)
        bb = s.val().BoundingBox()
        result[group] = {
            "shape": s,
            "print_shape": s.translate((-bb.xmin, -bb.ymin, 0)),
            "origin": (bb.xmin, bb.ymin),
            "sites": sites,
            "hole_centers": {site: holes[site] for site in sites},
            "anchors": anchors[group],
            "optional_anchors": optional[group],
            "anchor_end": ANCHOR_ENDS[group],
            "through_post_centers": post_slots if group == "front" else [],
            "post_slots": post_slots if group == "front" else [],
            "rear_rail_depth_mm": BAR_WIDTH if group == "front" else None,
            "gpu_tab_relief": relief,
            "post_slots_are_selectable": True,
            "standalone_anchors": anchors[group],
            "install_anchors_before_PCB": group == "front",
            "post_slot_mm": [POST_SLOT_LENGTH, POST_SLOT_WIDTH],
            "post_opening": post_hw.opening_spec(),
            "shelf_slot_mm": [8.0, slot_width],
            "shelf_fastener": "M3",
            "top_washer_od_mm": washer_od,
            "backing_washer_od_mm": WASHER_OD,
            "shelf_hole_diameter_mm": 3.5,
            "bar_width_mm": BAR_WIDTH,
            "ear_width_mm": EAR_WIDTH,
            "bounds": [bb.xmin, bb.ymin, bb.xmax, bb.ymax],
        }
    a, b = [v["shape"].val() for v in result.values()]
    assert a.intersect(b).Volume() < 0.01, (name, "overlapping sections")
    assert a.distance(b) >= CLEARANCE - 0.001
    return result, joints


# --- Printing (shared by every build that prints these sections) ---------------------------------
PRINT_EDGE_MARGIN = 3.25  # long interlocked sections; their profiles disable the skirt; rear rails also have no brim
PRINT_NOTE = "flat, rotated 90 degrees; screw-head recesses up"
FILAMENT = "printer:duramic-petg-240c.json"
PROFILE = {
    "atx_mobo_adapter_front": "profiles/motherboard-ears.json",
    "atx_mobo_adapter_rail": "profiles/motherboard-rails.json",
    "h12d_mobo_adapter_rail": "profiles/motherboard-rails.json",
}


def print_mesh(mesh):
    """Bed orientation of a section's STL: turned over about the X = Y diagonal, screw-head recesses up."""
    vertices, triangles, (width, depth, height) = mesh
    rotated = [(y, x, round(height - z, 5)) for x, y, z in vertices]
    return rotated, triangles, (depth, width, height)


def print_profiles(printer) -> dict[str, dict]:
    """Process profiles for the sections, keyed by file name under the build's print/profiles/."""
    # Center the long ATX sections; keep the 3 mm brim, omit only the skirt.
    ears = printer.load_profile("printer:process.json")
    ears.update({"name": "0.20mm PETG ATX ears @Qidi X-Plus Gen1", "setting_id": "PETG_ATX_EARS", "skirt_loops": "0"})
    # The rear rails' GPU-tab groove runs the full rail length, so on the
    # first layer it is part of the outer contour. An outer brim fills the
    # groove and, on H12D, the hex holes that open into it. No brim.
    rails = {
        **ears,
        "name": "0.20mm PETG rear rails no brim @Qidi X-Plus Gen1",
        "setting_id": "PETG_MOBO_RAILS",
        "brim_type": "no_brim",
        "brim_width": "0",
    }
    return {"motherboard-ears.json": ears, "motherboard-rails.json": rails}
