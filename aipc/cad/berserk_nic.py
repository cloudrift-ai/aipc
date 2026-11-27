"""Berserk's ConnectX-4 Lx on the LRFC6911N riser, beside Kenshin's side AIO.

Placed in the strip between the side radiator's inner face (X52.3) and
Kenshin's motherboard mount; the owner measured about 75 mm across it
(2026-11-19). Along the strip it sits as far rearward, toward Kenshin, as
the RTX 5090 allows, keeping the QSFP28 cage clear of Berserk (owner,
2026-11-26). Across the strip it sits as far toward Kenshin as it can, away
from the side AIO's hoses (owner, 2026-11-27): the plate stops just short of
Kenshin's mount rail and the riser hangs past the plate over the rail, short
of Kenshin's PCB edge. Shelf coordinates throughout (X right, Y rear, Z up).

The riser lies flat with its x16 slot along +Y, so the card stands upright
with its full-height bracket and QSFP28 cage facing the rack front. With the
bracket at the front, the riser's SFF-8643 socket faces +X (toward Kenshin's
board) and its SATA power socket hangs under the rear end of the board,
mating along the board from behind (owner, 2026-11-19). The SFF-8643 plug
lies along the top of the board with its cable leaving toward the SATA end
(owner, 2026-11-27), so nothing projects past the socket edge.

The printed holder is a flat base plate only (owner, 2026-11-19: the slot
holds the card rigidly enough, so no bracket support). A 6 mm base with
four slotted M4 shelf anchors carries the riser on two 8 mm bosses under
the slot-side holes, which lift the board clear of the 5 mm-deep SATA
socket; each takes an M3 self-tapping screw. The socket-side holes sit over
Kenshin's mount rail and stay empty; lands 0.5 mm under the plate's
socket-side edge stop the overhanging board from flexing. The two
socket-side anchors sit under the board, so the plate is bolted down before
the riser goes on. The plate ends 1 mm past the board at the front and rear
so the bracket tongue and the SATA plug hang free of it.

Hole pitch and SATA depth are owner-measured; board outline, slot and
socket positions are photo estimates; the bracket-to-slot offset is a
PCIe CEM estimate.
"""
import cadquery as cq
from hwkit import spec

RISER, NIC, DAC, SFF = ("linkreal-lrfc6911n", "nvidia-mcx4131a-gcat",
                        "qsfp28-passive-dac", "sff-8643-pcie-cable")
PART = "berserk_nic_holder"

d = spec.dim
RADIATOR_FACE_X = 52.328          # Kenshin GA II radiator inner face (shelf_layout)
OWNER_GAP = 75.0                  # owner: radiator to Kenshin motherboard mount, about 75 mm
KENSHIN_MOUNT_X = RADIATOR_FACE_X + OWNER_GAP
MOUNT_CLEARANCE = 2.0             # plate edge short of Kenshin's mount rail
# Kenshin's PCB edge past the rail's strip-side face: 139.2 -> 153.66 in the
# CAD adapter rail and board (model geometry, not measured on the shelf).
RAIL_TO_KENSHIN_PCB = 14.46
PCB_EDGE_GAP = 3.0                # riser edge short of Kenshin's PCB edge
MAX_OVERHANG = 15.0               # owner: plate no more than 15 mm past the board outline
# 2.6 mm pilot: the slicer profile has no hole compensation, so it prints near
# 2.5 mm for the M3 self-tapper; the 8 mm boss is capped by the rear boss's
# clearance to the SATA socket (print audit 2026-11-27).
BASE_T, BOSS_D, PILOT_D = 6.0, 8.0, 2.6
SATA_CLEARANCE = 3.0              # under the SATA socket and plug body
BOSS_H = d(RISER, "sata_underside_depth") + SATA_CLEARANCE

# Riser placement: local u along the board from the power/bracket end, v across
# it from the slot edge (v=0) to the socket edge.
# Owner, 2026-11-26: the QSFP cage sat against Berserk's PCIe post rail, so
# the holder slides rearward along the strip, toward Kenshin, until the card's
# rear end is CARD_TO_KENSHIN_GPU in front of the RTX 5090's front face
# (Y617.98 in shelf_layout, which asserts the gap). The riser board, its SATA
# socket and the plate pass under the 5090, which starts at Z24.
CARD_TO_KENSHIN_GPU = 5.0
L, W = d(RISER, "pcb_length"), d(RISER, "pcb_width")
RISER_X0 = KENSHIN_MOUNT_X + RAIL_TO_KENSHIN_PCB - PCB_EDGE_GAP - W
RISER_Y0 = 491.5
RISER_Z = BASE_T + BOSS_H
RISER_TOP = RISER_Z + d(RISER, "pcb_thickness")


def riser_xy(u, v):
    return RISER_X0 + v, RISER_Y0 + u


HOLES_UV = [(u, v) for u in (d(RISER, "hole_inset_end"), d(RISER, "hole_inset_end") + d(RISER, "hole_pitch_length"))
            for v in (d(RISER, "hole_inset_slot_edge"), d(RISER, "hole_inset_slot_edge") + d(RISER, "hole_pitch_width"))]
# Only the slot-side holes land on the plate; the socket-side pair is over Kenshin's rail.
SCREW_HOLES_UV = [(u, v) for u, v in HOLES_UV if v < W/2]

# SATA power socket under the rear (SATA) end, mating along the board.
SATA_U0 = L - d(RISER, "sata_length_along_board")
SATA_V = (d(RISER, "sata_center_from_slot_edge") - d(RISER, "sata_width")/2,
          d(RISER, "sata_center_from_slot_edge") + d(RISER, "sata_width")/2)

CARD_PLANE_X = RISER_X0 + d(RISER, "slot_center_from_edge")
BRACKET_Y = RISER_Y0 + d(RISER, "slot_start") - d(NIC, "bracket_to_slot_start")
# Same allowance shelf_layout uses for every PCIe card: card body from Z24
# over a Z17.125 board top.
CARD_ABOVE_BOARD = 24.0 - 17.125
CARD_Z = RISER_TOP + CARD_ABOVE_BOARD
CARD_X = (CARD_PLANE_X - d(NIC, "pcb_thickness")/2 - d(NIC, "primary_side_height"),
          CARD_PLANE_X + d(NIC, "pcb_thickness")/2 + d(NIC, "secondary_side_height"))
CAGE_X = CARD_PLANE_X - d(NIC, "qsfp_cage_offset_from_pcb")
CAGE_Z = CARD_Z + d(NIC, "qsfp_cage_height")
# Full-height bracket envelope: 18.42 mm CEM width, mostly on the component
# side; tongue taken down to the riser top (allowance), 0.86 mm sheet plus
# its outward bend.
BRACKET_X = (CARD_PLANE_X - 16.0, CARD_PLANE_X + 2.42)
BRACKET_Z = (RISER_TOP, RISER_TOP + d(NIC, "bracket_height"))
BRACKET_DEPTH = 2.4

# Plate: the radiator-side margin holds two shelf anchors clear of the slot's
# pins; the Kenshin side stops short of the mount rail, inside the board
# outline, with two anchors under the board. 5 mm past the front end, so the
# front boss's pilot is 4 mm or more from the plate edge (print audit
# 2026-11-27), and 1 mm past the rear end for the SATA plug.
MARGIN_RADIATOR, MARGIN_FRONT, MARGIN_END = 13.5, 5.0, 1.0
BASE = (RISER_X0 - MARGIN_RADIATOR, KENSHIN_MOUNT_X - MOUNT_CLEARANCE,
        RISER_Y0 - MARGIN_FRONT, RISER_Y0 + L + MARGIN_END)       # x0, x1, y0, y1
RISER_OVERHANG = RISER_X0 + W - BASE[1]   # board past the plate's Kenshin edge
SLOT_L, SLOT_W = 10.0, 5.5
EDGE_WALL = 4.0
_AX_RAD = BASE[0] + EDGE_WALL + SLOT_W/2
_AX_SOCK = BASE[1] - EDGE_WALL - SLOT_W/2
ANCHOR_U = (20.0, 95.0)
ANCHORS = tuple((x, RISER_Y0 + u) for x in (_AX_RAD, _AX_SOCK) for u in ANCHOR_U)
# Deflection stops 0.5 mm below the board, so they only touch when the board
# bends: one beside the slot's through-hole pins at mid-length (card
# insertion, print audit 2026-11-19), and three at the plate's Kenshin edge
# under the overhanging socket side: front, rear and beside the SFF-8643
# socket (plug loads, print audit 2026-11-27), clear of the anchors and the
# SATA socket.
STOP_SIZE = (10.0, 6.0)          # along u, across v
STOP_GAP = 0.5
_EDGE_STOP_V = BASE[1] - 1.0 - STOP_SIZE[1]/2 - RISER_X0
STOP_UV = ((L/2, 15.0), (5.0, _EDGE_STOP_V), ((d(RISER, "sff_start") + d(RISER, "sff_end"))/2, _EDGE_STOP_V), (110.0, _EDGE_STOP_V))


def holder():
    """Printable as installed: base on the bed, bosses up."""
    x0, x1, y0, y1 = BASE
    body = cq.Workplane("XY").box(x1-x0, y1-y0, BASE_T, centered=False).translate((x0, y0, 0))
    for u, v in SCREW_HOLES_UV:
        x, y = riser_xy(u, v)
        body = body.union(cq.Workplane("XY").center(x, y).circle(BOSS_D/2).extrude(BOSS_H).translate((0, 0, BASE_T)))
        body = body.cut(cq.Workplane("XY").center(x, y).circle(PILOT_D/2).extrude(BOSS_H+BASE_T-1).translate((0, 0, 1)))
    for uv in STOP_UV:
        sx, sy = riser_xy(*uv)
        body = body.union(cq.Workplane("XY").center(sx, sy).rect(STOP_SIZE[1], STOP_SIZE[0])
                          .extrude(BOSS_H - STOP_GAP).translate((0, 0, BASE_T)))
    for x, y in ANCHORS:
        body = body.cut(cq.Workplane("XY").center(x, y).slot2D(SLOT_L, SLOT_W, 90).extrude(BASE_T))
    assert body.val().isValid() and len(body.solids().vals()) == 1
    # Fit checks on the printed geometry itself.
    assert x0-RADIATOR_FACE_X >= 1.0, "plate must clear the radiator face"
    assert abs(x1 - (KENSHIN_MOUNT_X - MOUNT_CLEARANCE)) < .01, "plate edge just short of Kenshin's mount rail"
    assert CARD_X[0]-RADIATOR_FACE_X >= 2.5, "card heatsink to radiator face"
    for over in (RISER_X0-x0, RISER_Y0-y0, y1-(RISER_Y0+L)):
        assert 0 <= over <= MAX_OVERHANG, ("plate past the board outline", over)
    # The board hangs over Kenshin's rail but stops short of Kenshin's PCB edge.
    assert 0 < RISER_OVERHANG and abs(KENSHIN_MOUNT_X + RAIL_TO_KENSHIN_PCB - (RISER_X0 + W) - PCB_EDGE_GAP) < .01
    for u, v in SCREW_HOLES_UV:     # pilot to the plate's free edges
        x, y = riser_xy(u, v)
        assert min(x-x0, x1-x, y-y0, y1-y) - PILOT_D/2 >= EDGE_WALL - .01, ("pilot to plate edge", u, v)
    for u, v in HOLES_UV:
        x, y = riser_xy(u, v)
        on_plate = min(x-x0, x1-x, y-y0, y1-y) >= BOSS_D/2 - .01
        assert on_plate == ((u, v) in SCREW_HOLES_UV), ("boss placement", u, v)
    assert len(SCREW_HOLES_UV) == 2
    stops = [(riser_xy(*uv), uv) for uv in STOP_UV]
    for x, y in ANCHORS:
        assert x-SLOT_W/2-x0 >= EDGE_WALL-.01 and x1-(x+SLOT_W/2) >= EDGE_WALL-.01, (x, "slot side wall")
        assert y-SLOT_L/2-y0 >= EDGE_WALL and y1-(y+SLOT_L/2) >= EDGE_WALL, (y, "slot end wall")
        for (sx, sy), _ in stops:     # slots stay EDGE_WALL from every stop and boss
            assert (abs(x-sx) >= SLOT_W/2 + STOP_SIZE[1]/2 + EDGE_WALL - .01
                    or abs(y-sy) >= SLOT_L/2 + STOP_SIZE[0]/2 + EDGE_WALL - .01), ("slot to stop", x, y, sx, sy)
        for u, v in SCREW_HOLES_UV:
            bx, by = riser_xy(u, v)
            assert abs(x-bx) >= SLOT_W/2 + BOSS_D/2 + EDGE_WALL - .01 or abs(y-by) >= SLOT_L/2 + BOSS_D/2 + EDGE_WALL - .01, ("slot to boss", x, y)
    for (sx, sy), (u, v) in stops:
        for (tx, ty), _ in stops:   # stops do not merge
            assert (sx, sy) == (tx, ty) or abs(sx-tx) >= STOP_SIZE[1] + 1 or abs(sy-ty) >= STOP_SIZE[0] + 1
        assert x0 + 1.0 <= sx - STOP_SIZE[1]/2 and sx + STOP_SIZE[1]/2 <= x1 - 1.0, ("stop on the plate", u, v)
        assert y0 + 1.0 <= sy - STOP_SIZE[0]/2 and sy + STOP_SIZE[0]/2 <= y1 - 1.0, ("stop on the plate", u, v)
    # The slot stop sits beside (not under) the slot's pin rows; the edge stops
    # sit forward of the SATA socket.
    slot_v1 = d(RISER, "slot_center_from_edge") + d(RISER, "slot_width")/2
    assert STOP_UV[0][1] - STOP_SIZE[1]/2 >= slot_v1 + 1.0, "stop clear of the slot pins"
    for u, v in STOP_UV[1:]:
        assert u + STOP_SIZE[0]/2 <= SATA_U0 - 1.0, "edge stop forward of the SATA socket"
    # The radiator-side anchors sit outside the board, clear of the slot's pins;
    # the Kenshin-side ones under the board, clear of the pins too.
    assert _AX_RAD + SLOT_W/2 <= RISER_X0, "radiator-side anchors outside the board"
    assert _AX_SOCK - SLOT_W/2 - 6.0 >= RISER_X0 + slot_v1, "Kenshin-side washers clear of the slot pins"
    # Washer and M4 head (allowance 4 mm) under the board, clear of its underside.
    assert BASE_T + 4.0 <= RISER_Z - 1.0, "anchor heads under the board"
    # SATA socket and plug body hang clear of the plate top and the rear bosses.
    assert RISER_Z - d(RISER, "sata_underside_depth") - BASE_T >= SATA_CLEARANCE - .01
    for u, v in SCREW_HOLES_UV:
        if u > L/2:
            assert (u + BOSS_D/2 <= SATA_U0 - 1.0 or v + BOSS_D/2 <= SATA_V[0] or v - BOSS_D/2 >= SATA_V[1]), "rear boss under the SATA socket"
    # The full-height bracket's tongue drops in front of the riser: keep the plate behind it.
    assert y0 - BRACKET_Y >= 10.0, "plate front edge to the card bracket"
    return body


def bracket_envelope():
    """Full-height bracket in front of the card: CEM width and height; tongue
    down to the riser top is an allowance. Checked against the layout, not
    exported (the bracket belongs to the card)."""
    return (cq.Workplane("XY").box(BRACKET_X[1]-BRACKET_X[0], BRACKET_DEPTH, BRACKET_Z[1]-BRACKET_Z[0], centered=False)
            .translate((BRACKET_X[0], BRACKET_Y-BRACKET_DEPTH, BRACKET_Z[0])))


def riser_holes():
    """The riser board's four mounting holes, as cutters through the PCB."""
    cut = None
    for u, v in HOLES_UV:
        x, y = riser_xy(u, v)
        c = cq.Workplane("XY").center(x, y).circle(d(RISER, "hole_diameter")/2).extrude(d(RISER, "pcb_thickness")+.4).translate((0, 0, RISER_Z-.2))
        cut = c if cut is None else cut.union(c)
    return cut


def boxes():
    """(list, name, x, y, z, w, d, h, note); list is 'parts', 'connectors' or 'outboard'."""
    slot_v = d(RISER, "slot_center_from_edge")
    sx, sy = riser_xy(d(RISER, "slot_start"), slot_v - d(RISER, "slot_width")/2)
    plug_w, plug_h = d(DAC, "plug_width"), d(DAC, "plug_height")
    sata_x0, sata_x1 = (RISER_X0 + v for v in SATA_V)
    sata_y0 = RISER_Y0 + SATA_U0
    sata_d = d(RISER, "sata_underside_depth")
    edge = RISER_X0 + W
    out = [
        ("parts", "Berserk LRFC6911N riser board", RISER_X0, RISER_Y0, RISER_Z, W, L, d(RISER, "pcb_thickness"),
         "flat on the printed holder; board width, holes, slot and socket positions are photo estimates"),
        ("parts", "Berserk LRFC6911N riser x16 slot", sx, sy, RISER_TOP, d(RISER, "slot_width"), d(RISER, "slot_length"), d(RISER, "slot_height"),
         "x16 connector (x4 electrical); photo-estimated position, assumed height"),
        ("parts", "Berserk ConnectX-4 Lx card", CARD_X[0], BRACKET_Y, CARD_Z, CARD_X[1]-CARD_X[0], d(NIC, "card_length"), d(NIC, "card_height"),
         "MCX4131A-GCAT low-profile card standing in the riser slot, bracket face at the front; heatsink side toward the radiator (CEM component limits)"),
        ("connectors", "QSFP28 DAC Berserk plug", CAGE_X-plug_h/2, BRACKET_Y-d(DAC, "plug_length_outside"), CAGE_Z-plug_w/2,
         plug_h, d(DAC, "plug_length_outside"), plug_w,
         "DAC plug through the holder gate; cage height on the card assumed"),
        ("connectors", "Berserk riser SATA power plug", sata_x0, sata_y0, RISER_Z-sata_d, sata_x1-sata_x0,
         RISER_Y0+L-sata_y0+d(RISER, "sata_plug_projection"), sata_d,
         "SATA power socket under the riser's rear end (owner: about 5 mm deep) and the Hercules plug mating from behind; span is a photo estimate, projection an allowance"),
        ("connectors", "Berserk SFF-8643 riser plug", edge-d(SFF, "plug_width"), RISER_Y0+d(RISER, "sff_end"), RISER_TOP,
         d(SFF, "plug_width"), d(SFF, "plug_length"), d(SFF, "plug_height"),
         "SFF-8643 plug lying along the top of the riser at its socket edge, cable leaving toward the SATA end (owner, 2026-11-27); socket position is a photo estimate"),
    ]
    return out


def h12d_sff_plug(port_x, board_front_y, board_top_z):
    """Straight plug in the H12D front-edge port, mating toward the rack front."""
    w, h, length = d(SFF, "plug_width"), d(SFF, "plug_height"), d(SFF, "plug_length")
    return ("connectors", "Berserk SFF-8643 H12D plug", port_x-w/2, board_front_y-length, board_top_z+.1, w, length, h,
            "H12D-8D SFF-8643 port photo-estimated from the manual layout figure (middle of three, front edge, mating toward the front); under the V100 tails")


def kenshin_qsfp_plug(card):
    """Plug in Kenshin's card cage at the right shelf edge, mating toward -X."""
    plug_w, plug_h, length = d(DAC, "plug_width"), d(DAC, "plug_height"), d(DAC, "plug_length_outside")
    cy, cz = card.y + card.d/2, card.z + d(NIC, "qsfp_cage_height")
    return ("outboard", "QSFP28 DAC Kenshin plug", card.x1, cy-plug_h/2, cz-plug_w/2, length, plug_h, plug_w,
            "DAC plug in Kenshin's cage on the right edge; projects past the deck edge and the rack opening")


def dac_route(berserk_plug, kenshin_plug):
    """Berserk plug end -> under the AIO hose -> above the 24-pin, behind the V100 hood -> right-edge lane -> loop -> Kenshin plug end."""
    bx, by, bz = berserk_plug.x + berserk_plug.w/2, berserk_plug.y, berserk_plug.z + berserk_plug.h/2
    kx, ky, kz = kenshin_plug.x1, kenshin_plug.y + kenshin_plug.d/2, kenshin_plug.z + kenshin_plug.h/2
    r = d(DAC, "bend_radius")
    lane_x, cross_y, cross_z = 418.0, 415.0, 80.0
    return [(bx, by, bz), (bx+8, by-6, bz), (bx+20, cross_y, cross_z), (lane_x, cross_y, cross_z),
            (lane_x, ky-80, cross_z), (kx+r, ky-r, kz), (kx+r, ky, kz), (kx, ky, kz)]


def sff_route(riser_plug, h12d_plug):
    """Riser plug end (toward the SATA end) -> turn up and back over the plug -> forward over the riser's socket edge
    -> in front of the card bracket to the lane left of the V100 hood -> along the deck front -> H12D plug end."""
    rx, ry, rz = riser_plug.x + riser_plug.w/2, riser_plug.y1, riser_plug.z + riser_plug.h/2
    hx, hy, hz = h12d_plug.x + h12d_plug.w/2, h12d_plug.y, h12d_plug.z + h12d_plug.h/2
    lane_x, front_y, low_z, over_z = 86.0, hy-6.0, hz, 34.0
    return [(rx, ry, rz), (rx, ry+8, rz), (rx, ry+8, over_z), (rx, RISER_Y0+30, over_z), (lane_x, 405.0, 30.0),
            (lane_x, front_y, low_z), (hx, front_y, low_z), (hx, hy, hz)]


def report():
    x0, x1, y0, y1 = BASE
    return {
        "part": PART, "quantity": 1,
        "placement": "Kenshin side-AIO strip: radiator inner face X52.3 to Kenshin's motherboard mount, owner-measured about 75 mm; as far rearward (toward Kenshin) as the RTX 5090 allows",
        "card_rear_to_kenshin_5090_target_mm": CARD_TO_KENSHIN_GPU,
        "holder_x_range_mm": [round(x0, 2), round(x1, 2)], "holder_x_from_radiator_face_mm": round(x1-RADIATOR_FACE_X, 2),
        "plate_edge_to_Kenshin_mount_mm": MOUNT_CLEARANCE,
        "riser_past_plate_over_Kenshin_rail_mm": round(RISER_OVERHANG, 2),
        "riser_edge_to_Kenshin_PCB_edge_mm": PCB_EDGE_GAP,
        "Kenshin_PCB_edge_basis": f"owner-measured mount at X{KENSHIN_MOUNT_X:.1f} plus the CAD rail-to-PCB offset {RAIL_TO_KENSHIN_PCB} mm (not measured)",
        "holder_y_range_mm": [y0, y1],
        "plate_past_board_mm": {"radiator_side": MARGIN_RADIATOR, "socket_side": round(-RISER_OVERHANG, 2), "front": MARGIN_FRONT, "rear": MARGIN_END,
                                "limit": MAX_OVERHANG},
        "riser_origin_xyz_mm": [RISER_X0, RISER_Y0, RISER_Z], "riser_orientation": "slot along +Y at the radiator side, SFF-8643 plug lying along the socket edge with its cable toward the rear, SATA socket under the rear end",
        "riser_underside_above_plate_mm": BOSS_H, "sata_socket_clearance_mm": SATA_CLEARANCE,
        "card_plane_x_mm": round(CARD_PLANE_X, 2), "bracket_face_y_mm": round(BRACKET_Y, 2),
        "plate_front_to_bracket_mm": round(y0-BRACKET_Y, 2),
        "card_heatsink_to_radiator_face_mm": round(CARD_X[0]-RADIATOR_FACE_X, 2),
        "riser_fasteners": "two M3 self-tapping screws (board + 8-10 mm) into 2.6 mm pilots in 8 mm bosses, 8 mm tall, under the slot-side holes; the socket-side holes sit over Kenshin's rail and stay empty",
        "deflection_stops": f"four {STOP_SIZE[1]:g} x {STOP_SIZE[0]:g} mm lands {STOP_GAP:g} mm below the board: beside the slot at mid-length, and front, mid (beside the SFF-8643 socket) and rear at the plate's Kenshin edge under the overhanging socket side",
        "bracket": "no bracket support (owner: the slot holds the card); the full-height bracket stands free in front of the plate",
        "shelf_anchor_xy_mm": [[round(x, 2), round(y, 2)] for x, y in ANCHORS], "shelf_fastener": "4 x M4 with OD12 washers and steel backing",
        "print": "PETG, base on the bed as installed; vertical bosses and stops on a solid plate, no overhangs or supports",
        "assembly_order": "bolt the bare holder to the shelf (the Kenshin-side anchors are under the riser, the radiator-side ones under the card), screw the riser on, seat the card, then plug SFF-8643 and the DAC; the SATA socket is under the RTX 5090, so plug SATA before the 5090 goes in or before the riser is screwed down",
        "airflow": "the side AIO fans pull air from this strip through the radiator, across the card heatsink; the 300 LFM the card needs is not verified",
        "to_measure": ["gap from the riser's Kenshin-side edge to Kenshin's PCB edge (3 mm planned from the CAD rail-to-PCB offset)","riser board length and width, and the hole insets from its edges (photo-scaled)", "SATA-end hole centre to the socket's inner face",
                       "bracket face to x16 slot start on the card", "QSFP28 cage height on the card", "actual radiator-to-mount gap"],
        "physical_fit_verified": False,
    }
