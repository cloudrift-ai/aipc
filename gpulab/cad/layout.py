"""GPU lab node on a Hammond RSUS1931BK1 shelf.

Run with ``hwkit cad`` (``make cad BUILD=gpulab``). Builds the assembly, the
printed baseboard and the fit report; asserts on collisions, card spacing,
position counts and cable reach.

Coordinates (mm): X across the deck from the left edge, Y from the deck front
toward the rear, Z up from the deck top. The H12D-8D sits at the front right
with its I/O edge facing the rack front, on the same two printed sections as
AIPC's Berserk (hwkit.components.atx_mobo_mount), turned 180 degrees. The PSU
lies on its side at the front left, held by AIPC's printed PSU bracket
(hwkit.components.atx_psu_bracket) on its AC face; its modular face points to
the rear, so the power leads run back along the left edge past the card tails.
Both printed designs are AIPC library parts: this script builds the same
geometry, asserts it matches the library models and never exports them. Two identical 13-position baseboards run end to
end along the rest of the depth. Cards stand upright across the width: bracket
on the right (high X), tail to the left, PCB planes normal to Y on one
continuous 20.32 mm pitch.

Values below that are not part dimensions are layout allowances or come from
the PCIe CEM drawing and the AIPC survey; see the fit report for evidence.
"""

from __future__ import annotations

import json
import math

import cadquery as cq

from hwkit import paths, spec
from hwkit.components import atx_mobo_mount as mobo_mount
from hwkit.components import atx_psu_bracket as psu_bracket
from hwkit.components import hammond_shelf
from hwkit.components import pcie_post as post_hw
from hwkit.export import export_print
from hwkit.registry import classify_assembly

OUT = paths.MODELS
OUT.mkdir(parents=True, exist_ok=True)

# Shelf deck.
SHELF = spec.get("hammond-rsus1931bk1")
W, D, T = SHELF.dim("deck_width"), SHELF.dim("deck_depth"), SHELF.dim("sheet_thickness")

# Layout allowances.
EDGE = 10.0  # PSU and post line inset from the deck edges
FRONT_MARGIN = 0.0  # the H12D rail section's I/O-side edge is flush with the deck front edge (no room to spare)
REAR_MARGIN = 0.5  # baseboard B end before the deck rear edge
PSU_BRACKET_MARGIN = 1.0  # PSU bracket foot behind the deck front edge
MOUNT_GAP = 0.5  # least free space between the H12D mount sections and baseboard A (both printed, on the deck)
# AIPC's H12D rail keeps the post holes of Berserk's four dual-slot V100s on their bracket
# screw axes (aipc/cad/berserk_platform.py BRACKET_POST_X), 6 mm behind the I/O edge.
RAIL_POST_Y = 6.0
PLATE_T = 6.0  # baseboard thickness (same as the AIPC rails)
POSITIONS_PER_BOARD = 13
END_MARGIN = 7.0  # plate beyond the first and last post centre (AIPC EAR_WIDTH / 2)
AIR_GAP = {"open-air": 18.0, "flow-through": 18.0, "blower": 3.0}  # free space beside a card's cooler side
CARD_BOTTOM_ABOVE_RISER = 4.0  # card body starts this far above the riser PCB top (connector seat allowance)
CPU_COOLER_ENVELOPE = (90.0, 90.0, 100.0)  # no cooler chosen yet
CABLE_SLACK = 60.0  # bend and service loop allowance per MCIO route
NUT_AF, NUT_T = 5.5, 2.4  # ISO 4032 M3 nut
CHANNEL_W, CHANNEL_DEPTH, SLOT_W = 6.4, 3.0, 3.4  # sliding-nut channel under each riser hole line
SLOT_END_WEB = 3.0  # solid plate at each end of the screw slot
ANCHOR_D, ANCHOR_CSK_D = 4.5, 8.6  # M4 countersunk anchors through the steel
RISER_PLUG = (2.0, 22.0, 2.0, 14.0, 10.0)  # riser 6-pin plug: local x0, x1, y0, y1 from the back-side edge, height (allowance)
CABLE_D = {"12v-2x6": 10.0, "pcie-8pin": 9.0, "riser": 8.0, "atx-24pin": 15.0, "eps-8pin-cpu": 9.0}  # bundle diameters (allowance)
CABLE_LANE_X0, CABLE_LANE_STEP = 15.0, 7.0  # lanes along the left edge, past the card tails
TOP_BEND = 40.0  # straight lead above a top-edge connector before it bends (12V-2x6 guidance is about 35 mm)
CABLE_SLACK_FACTOR = 1.1  # buy leads 10% longer than the modeled route

# PCIe CEM 2.0 and the AIPC survey (aipc/cad/atx_shelf_mounts.py, aipc/cad/shelf_layout.py).
PITCH = spec.dim("huananzhi-h12d-8d", "slot_pitch") / 2  # 20.32 mm single-slot pitch
KEY_FROM_FACE = 59.05  # CEM Fig. 6-2: bracket outside face to connector key
SLOT_END_FROM_KEY = 12.0  # x16 connector bracket-side end beyond the key (allowance)
POST_BEYOND_FACE = 4.05  # AIPC: posts at PCB edge +6, bracket face at +1.95
POST_FROM_PLANE = 9.0  # AIPC survey: bracket tab hole 9 mm from the card PCB plane, cooler side
BACK_SIDE = 4.0  # card back side beyond its PCB plane (AIPC V100 allowance)
FLANGE_ABOVE_PCB = 141.0 - (mobo_mount.THICKNESS + spec.dim("keystone-1451b", "length") + 1.6)  # AIPC H12D survey
FLANGE_BELOW_ROD_TOP = 4.0  # AIPC: flange Z141, rod top Z145
ATX_SITES = {"A": (0.65, 0.4), "C": (5.55, 0.4), "F": (11.75, 1.3), "G": (0.65, 6.5), "H": (5.55, 6.5),
             "K": (0.65, 9.35), "L": (5.55, 9.35), "M": (11.75, 9.35)}  # ATX 2.2 datums (inches), H12D populated sites

# Cards in order from the board toward the rear, by capped power, so the heaviest leads stay shortest:
# 5090 400 W, 4090 320, 7900 XTX 320, R9700 270, B70 190, B60 160. The 3090 FE (250 W cap) goes last:
# a two-position blower there would put its rear post's 12 mm backing washer on the shelf's rear fold,
# and the flow-through 3090 vents into the open rack space past the deck end.
# Every value comes from its part.toml.
CARDS = ["zotac-rtx-5090-solid", "nvidia-rtx-4090-fe", "amd-rx-7900-xtx-reference", "amd-radeon-ai-pro-r9700",
         "intel-arc-pro-b70", "asrock-arc-pro-b60-creator", "nvidia-rtx-3090-fe"]


def box(x0, y0, z0, dx, dy, dz):
    return cq.Workplane("XY").box(dx, dy, dz, centered=False).translate((x0, y0, z0))


def cooler_type(part):
    role = part.role
    return next(kind for kind in AIR_GAP if f"({kind} cooler)" in role)


solids: dict[str, cq.Workplane] = {}
colors: dict[str, cq.Color] = {}


def add(name, shape, color):
    assert name not in solids, name
    solids[name] = shape
    colors[name] = color


# --- Board on the AIPC mount, CPU envelope, PSU and bracket, host adapters -----------------------
BOARD = spec.get("huananzhi-h12d-8d")
BW, BD, BT = BOARD.dim("pcb_width"), BOARD.dim("pcb_depth"), BOARD.dim("pcb_thickness")
STANDOFF_L = spec.dim("keystone-1451b", "length")
RAIL_T = mobo_mount.THICKNESS
# Board-local frame, as in AIPC: x from the PCB low-X edge, y from the edge opposite the I/O, I/O edge at y = BD.
planes = [BOARD.dim("slot1_plane_x") - k * BOARD.dim("slot_pitch") for k in range(4)]
# Same rule as AIPC's berserk_platform: each dual-slot card's rod holes sit on its
# bracket screw notches, the PCB plane and one 20.32 mm slot pitch toward the cooler.
rail_post_x = sorted(round(x, 2) for p in planes for x in (p, p - BOARD.dim("slot_pitch") / 2))
sections, _joints = mobo_mount.build("gpulab", 0.0, 0.0, BW, BD, rail_post_x, RAIL_POST_Y)
io_reach = max(f["shape"].val().BoundingBox().ymax for f in sections.values()) - BD  # rail beyond the I/O edge
far_reach = -min(f["shape"].val().BoundingBox().ymin for f in sections.values())  # bars beyond the opposite edge
BX, BY = W - EDGE - BW, FRONT_MARGIN + io_reach  # front right; I/O edge at Y = BY, facing the rack front
BZ = RAIL_T + STANDOFF_L
BOARD_TOP = BZ + BT


def board_xy(x_local, from_io_edge):
    """Board-local x (from the low-X PCB edge with the I/O edge toward +Y, as in AIPC) to shelf XY.

    The board is turned 180 degrees from Berserk's orientation, so the I/O edge faces the deck front.
    """
    return BX + BW - x_local, BY + from_io_edge


def board_shape(shape):
    """Board-local shape (I/O edge at y = BD) turned into place."""
    return shape.rotate((0, 0, 0), (0, 0, 1), 180).translate((BX + BW, BY + BD, 0))


def library_match(part_id, print_shape):
    """The same printed part: this build's copy and the library model differ by less than 0.5 mm3."""
    model = cq.importers.importStep(str(spec.get(part_id).model_step)).val()
    ours = print_shape.val()
    diff = ours.cut(model).Volume() + model.cut(ours).Volume()
    assert diff < 0.5, (part_id, "differs from the library model", round(diff, 3))


SECTION_PART = {"front": "h12d_mobo_adapter_rail", "rear": "atx_mobo_adapter_front"}
mount_anchors = []
for group, frame in sections.items():
    library_match(SECTION_PART[group], frame["print_shape"])
    add(f"printed_H12D_mount_{group}_section", board_shape(frame["shape"]), cq.Color(0.23, 0.78, 0.77))
    mount_anchors += [board_xy(x, BD - y) for x, y in frame["standalone_anchors"]]

add("H12D_8D_board", box(BX, BY, BZ, BW, BD, BT), cq.Color(0.1, 0.35, 0.15))
hole_centers = {s: board_xy(x, BD - y) for f in sections.values() for s, (x, y) in f["hole_centers"].items()}
standoff_sites = {}
for site, (u, v) in ATX_SITES.items():
    x, y = board_xy(u * 25.4, v * 25.4)
    hx, hy = hole_centers[site]
    assert abs(hx - x) < 1e-6 and abs(hy - y) < 1e-6, (site, "board hole off the mount's screw slot")
    standoff_sites[site] = (x, y)
    add(f"H12D_6_32_standoff_{site}", cq.Workplane("XY").center(x, y).polygon(6, 6.35).circle(1.8).extrude(STANDOFF_L)
        .translate((0, 0, RAIL_T)), cq.Color(0.85, 0.75, 0.4))
    # From below, before the section goes down: head in the 3 mm counterbore, shank through the slot.
    add(f"H12D_6_32_screw_{site}", cq.Workplane("XY").center(x, y).circle(2.75).extrude(2.5).translate((0, 0, 0.3))
        .union(cq.Workplane("XY").center(x, y).circle(1.8).extrude(RAIL_T + 5.0 - 2.8).translate((0, 0, 2.8))),
        cq.Color(0.65, 0.65, 0.68))
for i, (x, y) in enumerate(mount_anchors, 1):  # M3 with 7 mm washers through the steel; the front three go in before the PCB
    add(f"H12D_mount_M3_shelf_bolt_{i}", cq.Workplane("XY").center(x, y).circle(1.5).extrude(RAIL_T + T + 4).translate((0, 0, -T - 4))
        .union(cq.Workplane("XY").center(x, y).circle(3.5).extrude(2.5).translate((0, 0, RAIL_T))), cq.Color(0.65, 0.65, 0.68))
cpu_x, cpu_y = board_xy(BOARD.dim("cpu_center_x"), BOARD.dim("cpu_center_from_io_edge"))
cw, cd, ch = CPU_COOLER_ENVELOPE
add("H12D_SP3_CPU_and_cooler_envelope", box(cpu_x - cw / 2, cpu_y - cd / 2, BOARD_TOP, cw, cd, ch), cq.Color(0.55, 0.55, 0.6))

PSU = spec.get("corsair-ws3000")
PSU_X = EDGE  # front left, on its side: the 86 mm face is the footprint width; modular face toward the rear
PSU_Y = PSU_BRACKET_MARGIN + psu_bracket.FOOT_REACH  # AC face; the bracket and its foot sit in front of it
PSU_FACE_Y = PSU_Y + PSU.dim("depth")
add("PSU_Corsair_WS3000", box(PSU_X, PSU_Y, 0.0, PSU.dim("height"), PSU.dim("depth"), PSU.dim("width")), cq.Color(0.15, 0.15, 0.17))
# AIPC's bracket, turned 180 degrees: its 86 mm frame spans the PSU face from PSU_X; the LED bypass overhangs the low-X side.
BRACKET_FACE_W = 86.0
bracket_print = psu_bracket.bracket(berserk=True)
library_match("psu_bracket", bracket_print)


def psu_local(x, depth):
    """Bracket-local x and depth in front of the AC face to shelf XY."""
    return PSU_X + BRACKET_FACE_W - x, PSU_Y - depth


bracket = psu_bracket.installed(bracket_print, 0.0, 0.0).rotate((0, 0, 0), (0, 0, 1), 180).translate((PSU_X + BRACKET_FACE_W, PSU_Y, 0))
assert bracket.val().BoundingBox().ymin >= PSU_BRACKET_MARGIN - 1e-6 and bracket.val().BoundingBox().xmin >= 0
add("printed_PSU_bracket", bracket, cq.Color(0.68, 0.58, 0.77))
psu_anchors = [psu_local(x, depth) for x, depth in psu_bracket.SHELF_ANCHORS]
for i, (x, y) in enumerate(psu_anchors, 1):
    add(f"PSU_bracket_M4_anchor_{i}", cq.Workplane("XY").center(x, y).circle(2.0).extrude(6.0 + T + 4).translate((0, 0, -T - 4))
        .union(cq.Workplane("XY").center(x, y).circle(4.5).extrude(2.5).translate((0, 0, 6.0))), cq.Color(0.65, 0.65, 0.68))

HOST = spec.get("cpayne-cp0120-mcio-host-adapter")
host_ports = []
for k in range(4):
    plane_x, _ = board_xy(BOARD.dim("slot1_plane_x") - k * BOARD.dim("slot_pitch"), 0)
    # Turned board: the component side faces +X; the card body runs +Y from the I/O edge.
    x0 = plane_x - BACK_SIDE
    y0 = BY
    z0 = BOARD_TOP + CARD_BOTTOM_ABOVE_RISER
    add(f"host_adapter_slot{k + 1}_CP0120", box(x0, y0, z0, HOST.dim("thickness"), HOST.dim("length"), HOST.dim("height")),
        cq.Color(0.1, 0.1, 0.12))
    for port in range(2):
        host_ports.append({"slot": k + 1, "port": port + 1, "xyz": (plane_x + 6, y0 + HOST.dim("length"), z0 + 20 + 30 * port)})

# --- Baseboard positions --------------------------------------------------------------------------
N = 2 * POSITIONS_PER_BOARD
POST_X = W - EDGE
FACE_X = POST_X - POST_BEYOND_FACE
KEY_X = FACE_X - KEY_FROM_FACE
last_post_y = D - REAR_MARGIN - END_MARGIN
plane_y = [last_post_y - POST_FROM_PLANE - (N - 1 - i) * PITCH for i in range(N)]
post_y = [y + POST_FROM_PLANE for y in plane_y]

RISER = spec.get("cpayne-cp0231-mcio-device-adapter")
RL, RW, RT = RISER.dim("pcb_length"), RISER.dim("pcb_width"), RISER.dim("pcb_thickness")
STANDOFF_H = spec.dim("m3-ff-standoff-10mm", "length")
RISER_Z = PLATE_T + STANDOFF_H
RISER_TOP = RISER_Z + RT
# Riser local x runs from its power-plug end; the slot's bracket end sits SLOT_END_FROM_KEY past the key.
RISER_X0 = KEY_X + SLOT_END_FROM_KEY - RISER.dim("slot_bracket_end_x")
HOLE_X = (RISER_X0 + RISER.dim("hole_x_inner"), RISER_X0 + RISER.dim("hole_x_outer"))
PLATE_X0 = HOLE_X[0] - CHANNEL_W / 2 - 7.0
PLATE_X1 = POST_X + post_hw.OPENING_LENGTH / 2 + 4.0  # 4 mm from the hex corner to the edge (docs/printing.md)


def baseboard(first):
    """One 13-position baseboard in shelf coordinates; ``first`` is its first position index."""
    ys = post_y[first : first + POSITIONS_PER_BOARD]
    y0, y1 = ys[0] - END_MARGIN, ys[-1] + END_MARGIN
    plate = box(PLATE_X0, y0, 0, PLATE_X1 - PLATE_X0, y1 - y0, PLATE_T)
    hexes = [(math.cos(math.radians(90)) * x - math.sin(math.radians(90)) * y, math.sin(math.radians(90)) * x + math.cos(math.radians(90)) * y)
             for x, y in post_hw.opening_points()]  # turned so one corner points at the card (-X)
    for y in ys:
        assert y - post_hw.OPENING_WIDTH / 2 - (ys[0] - END_MARGIN) >= 4.0 - 1e-6, "post hole too close to the plate end"
        plate = plate.cut(cq.Workplane("XY").polyline([(POST_X + u, y + v) for u, v in hexes]).close().extrude(PLATE_T))
    for x in HOLE_X:
        plate = plate.cut(box(x - CHANNEL_W / 2, y0 - 1, 0, CHANNEL_W, y1 - y0 + 2, CHANNEL_DEPTH))
        # The screw slot stops short of the ends so the plate stays one piece; nuts enter the channel ends.
        plate = plate.cut(box(x - SLOT_W / 2, y0 + SLOT_END_WEB, 0, SLOT_W, y1 - y0 - 2 * SLOT_END_WEB, PLATE_T))
    anchors = [((HOLE_X[0] + HOLE_X[1]) / 2, y) for y in (y0 + 20, (y0 + y1) / 2, y1 - 20)]
    plate = plate.faces(">Z").workplane(centerOption="ProjectedOrigin", origin=(0, 0, 0)).pushPoints(anchors).cskHole(ANCHOR_D, ANCHOR_CSK_D, 90)
    return plate, (y0, y1), anchors


BOARD_A, SPAN_A, ANCHORS_A = baseboard(0)
BOARD_B, SPAN_B, ANCHORS_B = baseboard(POSITIONS_PER_BOARD)
shift = SPAN_B[0] - SPAN_A[0]
assert abs(shift - POSITIONS_PER_BOARD * PITCH) < 1e-6, "baseboard B must be a translated copy of A"
assert abs(BOARD_B.val().Volume() - BOARD_A.val().Volume()) < 1e-3
seam = SPAN_B[0] - SPAN_A[1]
assert seam > 0, ("baseboards overlap", seam)
add("printed_gpulab_baseboard_A", BOARD_A, cq.Color(0.23, 0.78, 0.77))
add("printed_gpulab_baseboard_B", BOARD_B, cq.Color(0.23, 0.78, 0.77))
for tag, anchors in (("A", ANCHORS_A), ("B", ANCHORS_B)):
    for i, (x, y) in enumerate(anchors, 1):
        add(f"baseboard_{tag}_M4_anchor_{i}", cq.Workplane("XY").center(x, y).circle(2.0).extrude(PLATE_T + T + 4).translate((0, 0, -T - 4)),
            cq.Color(0.65, 0.65, 0.68))

# --- Cards, risers and posts ----------------------------------------------------------------------
rod_length = spec.dim("obt-pcie-support", "rod_length")
rod_top = post_hw.BASE_HEIGHT + rod_length
post_seat_z = rod_top - FLANGE_BELOW_ROD_TOP
card_flange_z = RISER_TOP + FLANGE_ABOVE_PCB
placements = []
BOARD_CLEARANCE = 1.5  # riser PCB in front of the board's far edge: both PCBs sit at about Z 16 on their mounts
# Position 0's riser would reach over the board corner: start at the first position whose riser clears it.
first_free = next(i for i, y in enumerate(plane_y) if y - RW / 2 >= BY + BD + BOARD_CLEARANCE)
next_free = first_free
for n, card_id in enumerate(CARDS, 1):
    part = spec.get(card_id)
    kind = cooler_type(part)
    thick, height, length = part.dim("thickness"), part.dim("height"), part.dim("length")
    last = n == len(CARDS)
    # The rearmost card's cooler side faces the open deck end, so it needs no position for its air gap.
    positions = math.ceil((thick + (0.0 if last else AIR_GAP[kind])) / PITCH)
    declared = next(r["count"] for r in part.requires if r["type"] == "gpu-baseboard-position")
    assert positions <= declared, (card_id, "positions", positions, "part.toml says", declared)
    i = next_free
    next_free += positions
    assert next_free <= N, ("cards need more than the baseboard positions", card_id, next_free, N)
    py = plane_y[i]
    x0 = FACE_X - length
    assert x0 >= 0, (card_id, "card tail past the deck edge", x0)
    if last:
        # Its intake faces the open rack space past the deck end; the card itself must stay on the deck.
        rear_free = D - (py - BACK_SIDE + thick)
        assert rear_free >= REAR_MARGIN, (card_id, "card past the deck rear", rear_free)
    add(f"GPU_{card_id.replace('-', '_')}", box(x0, py - BACK_SIDE, RISER_TOP + CARD_BOTTOM_ABOVE_RISER, length, thick, height),
        cq.Color(0.35, 0.35, 0.38))
    # Riser board centred on the card plane, standoffs on the two nut channels.
    riser = box(RISER_X0, py - RW / 2, RISER_Z, RL, RW, RT)
    for a, b in ((52.0, 81.0), (92.0, 121.0)):  # MCIO receptacles under the PCB (photo-estimate)
        riser = riser.union(box(RISER_X0 + a, py + RW / 2 - 10, RISER_Z - RISER.dim("mcio_height_below_pcb"), b - a, 10, RISER.dim("mcio_height_below_pcb")))
    px0, px1, py0, py1, ph = RISER_PLUG
    riser = riser.union(box(RISER_X0 + px0, py - RW / 2 + py0, RISER_TOP, px1 - px0, py1 - py0, ph))
    slot_len = 89.0
    riser = riser.union(box(KEY_X + SLOT_END_FROM_KEY - slot_len, py - 3.75, RISER_TOP, slot_len, 7.5, CARD_BOTTOM_ABOVE_RISER))
    add(f"riser_{n}_CP0231", riser, cq.Color(0.08, 0.08, 0.1))
    holes = [(x, py - RW / 2 + yy) for x in HOLE_X for yy in (RISER.dim("hole_y_near"), RISER.dim("hole_y_far"))]
    slot_spans = [(lo + SLOT_END_WEB + 1.6, hi - SLOT_END_WEB - 1.6) for lo, hi in (SPAN_A, SPAN_B)]
    for hx, hy in holes:
        assert any(lo <= hy <= hi for lo, hi in slot_spans), (card_id, "riser screw outside the baseboard slots", round(hy, 2))
    for j, (hx, hy) in enumerate(holes, 1):
        add(f"riser_{n}_riser_standoff_{j}", cq.Workplane("XY").center(hx, hy).polygon(6, 5.5 * 2 / math.sqrt(3)).circle(1.6)
            .extrude(STANDOFF_H).translate((0, 0, PLATE_T)), cq.Color(0.85, 0.75, 0.4))
        add(f"riser_{n}_riser_M3_screw_{j}", cq.Workplane("XY").center(hx, hy).circle(1.5).extrude(PLATE_T - CHANNEL_DEPTH + 4)
            .translate((0, 0, CHANNEL_DEPTH)), cq.Color(0.65, 0.65, 0.68))
        add(f"riser_{n}_riser_M3_nut_{j}", cq.Workplane("XY").center(hx, hy).polygon(6, NUT_AF * 2 / math.sqrt(3)).circle(1.5)
            .extrude(NUT_T).translate((0, 0, CHANNEL_DEPTH - NUT_T)), cq.Color(0.65, 0.65, 0.68))
    posts = [post_y[i], post_y[i + 1]]
    for j, ypost in enumerate(posts, 1):
        tag = f"{card_id.replace('-', '_')}"
        base = (cq.Workplane("XY").polygon(6, post_hw.BASE_AF * 2 / math.sqrt(3)).extrude(post_hw.BASE_HEIGHT)
                .cut(cq.Workplane("XY").circle(1.5).extrude(post_hw.BASE_HEIGHT)).translate((POST_X, ypost, 0)))
        add(f"{tag}_M3_SW5p5_14mm_standoff_{j}", base, cq.Color(0.8, 0.7, 0.4))
        add(f"{tag}_metal_OBT_PCIe_post_{j}_survey",
            cq.Workplane("XY").center(POST_X, ypost).circle(3.0).extrude(rod_length).translate((0, 0, post_hw.BASE_HEIGHT)),
            cq.Color(0.62, 0.62, 0.64))
        add(f"{tag}_OBT_9mm_stud_{j}", cq.Workplane("XY").center(POST_X, ypost).circle(1.5).extrude(post_hw.OBT_STUD_LENGTH)
            .translate((0, 0, post_hw.BASE_HEIGHT - post_hw.OBT_STUD_LENGTH)), cq.Color(0.62, 0.62, 0.64))
        add(f"{tag}_M3x8_post_screw_{j}", cq.Workplane("XY").center(POST_X, ypost).circle(1.5).extrude(post_hw.BOTTOM_SCREW_LENGTH)
            .translate((0, 0, -T - post_hw.BACKER_T - post_hw.SMALL_WASHER_T)), cq.Color(0.65, 0.65, 0.68))
        add(f"{tag}_post_backing_washer_{j}", cq.Workplane("XY").center(POST_X, ypost).circle(6).circle(2.2).extrude(post_hw.BACKER_T)
            .translate((0, 0, -T - post_hw.BACKER_T)), cq.Color(0.5, 0.5, 0.55))
    placements.append({"card": card_id, "cooler": kind, "positions": list(range(i, i + positions)),
                       "pcb_plane_y_mm": round(py, 2), "post_y_mm": [round(y, 2) for y in posts],
                       "body_y_mm": [round(py - BACK_SIDE, 2), round(py - BACK_SIDE + thick, 2)],
                       "body_x_mm": [round(x0, 2), round(FACE_X, 2)],
                       "air_gap_mm": round(positions * PITCH - thick, 2), "riser": n,
                       "riser_mcio_xyz": (RISER_X0 + 86.5, py + RW / 2, RISER_Z - 4),
                       "riser_plug_xyz": (RISER_X0 + px0, py - RW / 2 + (py0 + py1) / 2, RISER_TOP + ph / 2),
                       "card_top_z": RISER_TOP + CARD_BOTTOM_ABOVE_RISER + height, "tail_x": x0,
                       "body_center_y": py - BACK_SIDE + thick / 2, "power": [(r["type"], r["count"]) for r in part.requires
                                                                             if r["type"] in ("12v-2x6", "pcie-8pin")],
                       "connector_from_tail": part.dim("power_connector_from_tail")})


# --- Power cables (approximate) --------------------------------------------------------------------
def tube(points, d):
    """Round bundle along a polyline: cylinders between points, spheres at the joints.

    All pieces are fused in one fuzzy boolean. Fusing them one at a time with an exact boolean
    dropped whole segments where a short leg runs between two overlapping joint spheres (the B70
    and 3090 leads), sometimes with a shape that still passed isValid().
    """
    pieces = []
    for (a, b) in zip(points, points[1:], strict=False):
        va, vb = cq.Vector(*a), cq.Vector(*b)
        length = (vb - va).Length
        if length < 1e-6:
            continue
        pieces.append(cq.Solid.makeCylinder(d / 2, length, va, (vb - va).normalized()))
    for pt in points[1:-1]:
        pieces.append(cq.Solid.makeSphere(d / 2, cq.Vector(*pt), angleDegrees1=-90, angleDegrees2=90))
    shape = (pieces[0].fuse(*pieces[1:], tol=1e-4) if len(pieces) > 1 else pieces[0]).clean()
    assert shape.isValid() and len(shape.Solids()) == 1, ("cable bundle is not one valid solid", points[0])
    return cq.Workplane("XY").add(shape)


face_slots = [(PSU_X + 12 + 18 * c, z) for z in (25.0, 55.0, 85.0, 115.0, 140.0) for c in range(4)]
cables, cable_targets = [], {}
# Stock reach per lead kind: GPU 8-pin inputs take the first connector of a dual cable, risers may take the second.
STOCK_REACH = {"12v-2x6": PSU.dim("cable_12v_2x6_length"), "pcie-8pin": PSU.dim("cable_pcie_first_connector"),
               "riser": PSU.dim("cable_pcie_length"), "atx-24pin": PSU.dim("cable_atx24_length"),
               "eps-8pin-cpu": PSU.dim("cable_eps_length")}


def add_cable(name, points, kind, target):
    d = CABLE_D[kind]
    length = sum((cq.Vector(*b) - cq.Vector(*a)).Length for a, b in zip(points, points[1:], strict=False))
    add(name, tube(points, d), cq.Color(0.9, 0.75, 0.1) if kind == "riser" else cq.Color(0.95, 0.55, 0.1))
    cable_targets[name] = {target, "PSU_Corsair_WS3000"}
    need = length * CABLE_SLACK_FACTOR
    cables.append({"cable": name, "kind": kind, "to": target, "route_mm": round(length), "buy_at_least_mm": round(need),
                   "stock_mm": STOCK_REACH[kind], "extension_needed": need > STOCK_REACH[kind]})


def from_psu(k):
    x, z = face_slots[k]
    return (x, PSU_FACE_Y, z), (x, PSU_FACE_Y + 12, z)


k = 0
lane = 0
for place in placements:  # GPU leads: back along the left edge, then to the tail end or over the top edge
    target = f"GPU_{place['card'].replace('-', '_')}"
    leads = [kind for kind, count in place["power"] for _ in range(count)]
    for j, kind in enumerate(leads):
        start, out = from_psu(k)
        k += 1
        lx, lz = CABLE_LANE_X0 + CABLE_LANE_STEP * lane, 60.0 + 9.0 * lane
        lane += 1
        y = place["body_center_y"] + (j - (len(leads) - 1) / 2) * 12.0
        ztop = place["card_top_z"]
        if place["connector_from_tail"] == 0:
            zc = ztop - 20.0
            pts = [start, out, (lx, out[1], lz), (lx, y, lz), (lx, y, zc), (place["tail_x"], y, zc)]
        else:
            xc = place["tail_x"] + place["connector_from_tail"] + 25.0 * j
            pts = [start, out, (lx, out[1], lz), (lx, y, lz), (lx, y, ztop + TOP_BEND), (xc, y, ztop + TOP_BEND), (xc, y, ztop)]
        assert lx + CABLE_D[kind] / 2 < min(p["tail_x"] for p in placements), "cable lane runs into a card tail"
        add_cable(f"cable_{place['card'].replace('-', '_')}_{kind.replace('-', '_')}_{j + 1}", pts, kind, target)
for n, place in enumerate(placements, 1):  # riser leads: low along the left edge, then under the cards in the gap before each card
    start, out = from_psu(k)
    k += 1
    lx = CABLE_LANE_X0 + CABLE_LANE_STEP * (n - 1)
    rx, ry, rz = place["riser_plug_xyz"]
    low = RAIL_T + 2.5 + 1.0 + CABLE_D["riser"] / 2  # over the mount's shelf-bolt heads
    pts = [start, out, (lx, out[1], low), (lx, ry, low), (rx - 6.0, ry, low), (rx - 6.0, ry, rz), (rx, ry, rz)]
    add_cable(f"cable_riser_{n}_pcie_6pin", pts, "riser", f"riser_{n}_CP0231")
for kind, xl, idx in (("atx-24pin", BOARD.dim("atx24_x"), 1), ("eps-8pin-cpu", BOARD.dim("eps_x"), 1), ("eps-8pin-cpu", BOARD.dim("eps_x") - 30.0, 2)):
    start, out = from_psu(k)
    k += 1
    tx, ty = board_xy(xl, BD - 8.0)
    zb = BOARD_TOP + 40.0
    pts = [start, out, (out[0], out[1], zb), (tx, out[1], zb), (tx, ty, zb), (tx, ty, BOARD_TOP)]
    add_cable(f"cable_board_{kind.replace('-', '_')}_{idx}", pts, kind, "H12D_8D_board")

# --- Collision checks -----------------------------------------------------------------------------
def overlaps(a, b):
    return all(getattr(a, k + "min") < getattr(b, k + "max") - 1e-6 and getattr(a, k + "max") > getattr(b, k + "min") + 1e-6 for k in "xyz")


# Pairs that touch by design: fasteners in what they fasten.
TOUCH_OK = (("_post_screw_", "_14mm_standoff_"), ("_OBT_9mm_stud_", "_14mm_standoff_"), ("_OBT_PCIe_post_", "_14mm_standoff_"),
            ("riser_M3_screw", "riser_standoff"), ("riser_M3_screw", "riser_M3_nut"), ("riser_M3_screw", "printed_gpulab"),
            ("_M4_anchor_", "printed_gpulab"), ("_6_32_screw_", "_6_32_standoff_"), ("_OBT_9mm_stud_", "_OBT_PCIe_post_"),
            ("_M3_shelf_bolt_", "printed_H12D_mount"), ("PSU_bracket_M4_anchor_", "printed_PSU_bracket"))
names = list(solids)
boxes = {n: solids[n].val().BoundingBox() for n in names}
collision_pairs = 0
for a_i, a in enumerate(names):
    for b in names[a_i + 1 :]:
        if not overlaps(boxes[a], boxes[b]):
            continue
        if a.startswith("cable_") and b.startswith("cable_"):
            continue  # leads may bundle and touch
        if (a in cable_targets and b in cable_targets[a]) or (b in cable_targets and a in cable_targets[b]):
            continue  # a lead ends in its own connector
        if any((p in a and q in b) or (p in b and q in a) for p, q in TOUCH_OK):
            continue
        collision_pairs += 1
        vol = solids[a].val().intersect(solids[b].val()).Volume()
        assert vol < 0.01, ("collision", a, b, round(vol, 3))

# The cards must clear each other with their air gaps, and the board area.
for first, second in zip(placements, placements[1:], strict=False):
    gap = second["body_y_mm"][0] - first["body_y_mm"][1]
    need = AIR_GAP[first["cooler"]]
    assert gap >= need - 0.01, ("air gap", first["card"], second["card"], gap, need)
assert placements[0]["body_y_mm"][0] > BY + BD, ("first card over the board", placements[0]["body_y_mm"][0], BY + BD)
# The sections' far-side bars against baseboard A, within the baseboard's X span (the two ears lie outside it).
slab = box(PLATE_X0, 0, 0, PLATE_X1 - PLATE_X0, D, RAIL_T)
mount_free = SPAN_A[0] - max(solids[f"printed_H12D_mount_{g}_section"].intersect(slab).val().BoundingBox().ymax for g in sections)
assert mount_free >= MOUNT_GAP, ("H12D mount sections reach baseboard A", round(mount_free, 2))
riser_free = placements[0]["pcb_plane_y_mm"] - RW / 2 - (BY + BD)

# Cable reach: each riser's MCIO input to its host adapter port, routed along X, then Y, plus height.
routes = []
riser_mcio_x = placements[0]["riser_mcio_xyz"][0]
ports = sorted(host_ports, key=lambda p: abs(p["xyz"][0] - riser_mcio_x))  # ports nearest the riser inputs for the farthest cards
for place, port in zip(sorted(placements, key=lambda p: -p["pcb_plane_y_mm"]), ports, strict=False):
    (hx, hy, hz), (rx, ry, rz) = port["xyz"], place["riser_mcio_xyz"]
    run = abs(hx - rx) + abs(hy - ry) + abs(hz - rz) + CABLE_SLACK
    cable = spec.dim("cpayne-mcio-8i-cable-0p75m", "length")
    assert run <= cable, ("MCIO cable too short", place["card"], round(run), cable)
    routes.append({"card": place["card"], "host_slot": port["slot"], "host_port": port["port"],
                   "route_mm": round(run), "cable_mm": cable, "spare_mm": round(cable - run)})

# --- Deck drill plan, shelf envelope, assembly ----------------------------------------------------
drill = []
for (x, y) in mount_anchors:
    assert 6 <= x <= W - 6 and 6 <= y <= D - 6, ("mount anchor too near the deck edge", x, y)
    drill.append({"part": "H12D mount M3 anchor", "xy_mm": [round(x, 2), round(y, 2)], "diameter_mm": 3.5})
for (x, y) in psu_anchors:
    assert 6 <= x <= W - 6 and 6 <= y <= D - 6, ("PSU anchor too near the deck edge", x, y)
    drill.append({"part": "PSU bracket M4 anchor", "xy_mm": [round(x, 2), round(y, 2)], "diameter_mm": 5.0})
for place in placements:
    for y in place["post_y_mm"]:
        drill.append({"part": f"{place['card']} post M3", "xy_mm": [POST_X, y], "diameter_mm": 3.5})
for tag, anchors in (("A", ANCHORS_A), ("B", ANCHORS_B)):
    for x, y in anchors:
        drill.append({"part": f"baseboard {tag} M4 anchor", "xy_mm": [round(x, 2), round(y, 2)], "diameter_mm": 4.5})
deck = box(0, 0, -T, W, D, T)
for hole in drill:
    deck = deck.cut(cq.Workplane("XY").center(*hole["xy_mm"]).circle(hole["diameter_mm"] / 2).extrude(T).translate((0, 0, -T)))

assembly = cq.Assembly(name="gpulab")
assembly.add(deck, name="RSUS1931BK1_drill_plan_deck_gpulab", color=cq.Color(0.5, 0.54, 0.58))
for name, shape in solids.items():
    assert shape.val().isValid(), name
    assembly.add(shape, name=name, color=colors[name])
shelf_report = hammond_shelf.add_to_assembly(assembly, W, D, T, OUT)
assembly.save(str(paths.ASSEMBLY_STEP))

export_print("gpulab_baseboard", BOARD_A.translate((-PLATE_X0, -SPAN_A[0], 0)), 2,
             "13-position GPU baseboard: post holes and riser nut channels; two prints end to end")
bom = classify_assembly(assembly)
assert not bom["errors"], bom["errors"]

# --- Report ---------------------------------------------------------------------------------------
masses = {pid: (p.dims["mass"].value or 0) * p.quantity for pid, p in spec.load_all().items()
          if "mass" in p.dims and p.data.get("on_shelf", True)}
top = max(s.val().BoundingBox().zmax for s in solids.values())
report = {
    "status": "design; nothing bought or fitted. Riser outline, host adapter envelope and card post offsets are not measured.",
    "deck_mm": [W, D], "positions": N, "pitch_mm": PITCH,
    "board_mount": {"parts": list(SECTION_PART.values()), "source": "AIPC library models, hwkit.components.atx_mobo_mount",
                    "io_edge_y_mm": round(BY, 2), "pcb_bottom_z_mm": BZ, "rail_beyond_io_edge_mm": round(io_reach, 2),
                    "bars_beyond_far_edge_mm": round(far_reach, 2), "free_to_baseboard_A_mm": round(mount_free, 2),
                    "riser_1_free_to_board_edge_mm": round(riser_free, 2),
                    "unused_rail_post_holes": "the rail keeps Berserk's eight V100 post holes; the host adapters use none",
                    "anchors_xy_mm": [[round(x, 2), round(y, 2)] for x, y in mount_anchors]},
    "psu": {"ac_face_y_mm": PSU_Y, "modular_face_y_mm": PSU_FACE_Y, "bracket": "psu_bracket (AIPC), turned 180 degrees",
            "bracket_anchors_xy_mm": [[round(x, 2), round(y, 2)] for x, y in psu_anchors],
            "lie_on": "the same side as AIPC's PSUs, so the two upper rear-face #6-32 holes meet the bracket"},
    "baseboard": {"count": 2, "positions_each": POSITIONS_PER_BOARD,
                  "size_mm": [round(PLATE_X1 - PLATE_X0, 2), round(SPAN_A[1] - SPAN_A[0], 2), PLATE_T],
                  "spans_y_mm": [[round(v, 2) for v in SPAN_A], [round(v, 2) for v in SPAN_B]], "seam_mm": round(seam, 2),
                  "x_mm": [round(PLATE_X0, 2), round(PLATE_X1, 2)], "nut_channel_x_mm": [round(x, 2) for x in HOLE_X],
                  "post_x_mm": POST_X, "post_y_mm": [round(y, 2) for y in post_y]},
    "card_heights": {"riser_pcb_top_z_mm": RISER_TOP, "card_flange_z_mm": round(card_flange_z, 3), "post_seat_z_mm": post_seat_z,
                     "flange_minus_seat_mm": round(card_flange_z - post_seat_z, 3),
                     "basis": "AIPC survey: flange 123.875 mm above an H12D PCB on 6 mm rail + 3/8 in standoffs (the riser PCB stands in for it); OBT rod length is an allowance"},
    "cards": placements, "first_position_used": first_free, "rear_card_free_to_deck_end_mm": round(rear_free, 1), "positions_used": next_free - first_free, "mcio_routes": routes,
    "max_component_z_mm": round(top, 1),
    "power_cables": cables, "power_cable_basis": "approximate orthogonal routes; connector positions and bundle diameters are allowances; "
    "stock_mm is the PSU's published cable length (8-pin GPU inputs to the first connector of a dual cable, 600 mm)",
    "shelf_mass_kg": round(sum(masses.values()), 2), "shelf_rating_kg": SHELF.dim("load_rating"),
    "drill_plan": drill, "collision_pairs_checked": collision_pairs,
    "hammond": {k: shelf_report[k] for k in ("static_boolean_pairs_checked", "continuous_travel_envelope_pairs_checked")},
}
(OUT / "gpulab-fit-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(f"gpulab: {len(placements)} cards on positions {first_free}-{next_free - 1} of {N}, top Z {top:.0f} mm, "
      f"{report['shelf_mass_kg']} kg on the shelf, flange-seat {card_flange_z - post_seat_z:+.2f} mm")
