"""Berserk's ConnectX-4 Lx on the LRFC6911N riser, beside Kenshin's side AIO.

Placed in the strip between the side radiator's inner face (X52.3) and
Kenshin's motherboard mount; the owner measured about 75 mm across it
(2026-11-19). Shelf coordinates throughout (X right, Y rear, Z up).

The riser lies flat with its x16 slot along +Y, so the card stands upright
with its full-height bracket and QSFP28 cage facing the rack front. With the
bracket at the front, the riser's SFF-8643 socket faces +X (toward Kenshin's
board) and its SATA power socket hangs under the rear end of the board,
mating along the board from behind (owner, 2026-11-19).

The printed holder is a flat base plate only (owner, 2026-11-19: the slot
holds the card rigidly enough, so no bracket support). A 6 mm base with
four slotted M4 shelf anchors carries the riser on four 8 mm bosses, which
lift the board clear of the 5 mm-deep SATA socket; each takes an M3
self-tapping screw. The plate stays within 15 mm of the board outline on
every side, and ends 1 mm past the board at the front and rear so the
bracket tongue and the SATA plug hang free of it.

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
MAX_OVERHANG = 15.0               # owner: plate no more than 15 mm past the board outline
BASE_T, BOSS_D, PILOT_D = 6.0, 8.0, 2.5
SATA_CLEARANCE = 3.0              # under the SATA socket and plug body
BOSS_H = d(RISER, "sata_underside_depth") + SATA_CLEARANCE

# Riser placement: local u along the board from the power/bracket end, v across
# it from the slot edge (v=0) to the socket edge.
RISER_X0, RISER_Y0 = 65.3, 457.0
RISER_Z = BASE_T + BOSS_H
RISER_TOP = RISER_Z + d(RISER, "pcb_thickness")
L, W = d(RISER, "length"), d(RISER, "pcb_width")


def riser_xy(u, v):
    return RISER_X0 + v, RISER_Y0 + u


HOLES_UV = [(u, v) for u in (d(RISER, "hole_inset_end"), d(RISER, "hole_inset_end") + d(RISER, "hole_pitch_length"))
            for v in (d(RISER, "hole_inset_slot_edge"), d(RISER, "hole_inset_slot_edge") + d(RISER, "hole_pitch_width"))]

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

# Plate: side margins hold the shelf anchors; 1 mm past each board end.
MARGIN_RADIATOR, MARGIN_SOCKET, MARGIN_END = 11.5, 13.0, 1.0
BASE = (RISER_X0 - MARGIN_RADIATOR, RISER_X0 + W + MARGIN_SOCKET,
        RISER_Y0 - MARGIN_END, RISER_Y0 + L + MARGIN_END)       # x0, x1, y0, y1
SLOT_L, SLOT_W = 10.0, 5.5
EDGE_WALL = 4.0
_AX_RAD = BASE[0] + EDGE_WALL + SLOT_W/2
_AX_SOCK = BASE[1] - EDGE_WALL - SLOT_W/2
ANCHORS = tuple((x, RISER_Y0 + u) for x in (_AX_RAD, _AX_SOCK) for u in (20.0, 95.0))
# Deflection stop under the slot's mid-length, beside the slot's through-hole
# pins: 0.5 mm below the board, so it only touches when card insertion bends
# the 114 mm span (print audit 2026-11-19).
STOP_UV = (L/2, 15.0)
STOP_SIZE = (10.0, 6.0)          # along u, across v
STOP_GAP = 0.5
# Material-saving window under the board, clear of bosses, anchors and the stop.
WINDOW = (RISER_X0 + 20.0, RISER_X0 + W - 11.0, RISER_Y0 + 12.0, RISER_Y0 + 103.0)


def holder():
    """Printable as installed: base on the bed, bosses up."""
    x0, x1, y0, y1 = BASE
    body = cq.Workplane("XY").box(x1-x0, y1-y0, BASE_T, centered=False).translate((x0, y0, 0))
    wx0, wx1, wy0, wy1 = WINDOW
    body = body.cut(cq.Workplane("XY").box(wx1-wx0, wy1-wy0, BASE_T, centered=False).translate((wx0, wy0, 0)))
    for u, v in HOLES_UV:
        x, y = riser_xy(u, v)
        body = body.union(cq.Workplane("XY").center(x, y).circle(BOSS_D/2).extrude(BOSS_H).translate((0, 0, BASE_T)))
        body = body.cut(cq.Workplane("XY").center(x, y).circle(PILOT_D/2).extrude(BOSS_H+BASE_T-1).translate((0, 0, 1)))
    sx, sy = riser_xy(*STOP_UV)
    body = body.union(cq.Workplane("XY").center(sx, sy).rect(STOP_SIZE[1], STOP_SIZE[0])
                      .extrude(BOSS_H - STOP_GAP).translate((0, 0, BASE_T)))
    for x, y in ANCHORS:
        body = body.cut(cq.Workplane("XY").center(x, y).slot2D(SLOT_L, SLOT_W, 90).extrude(BASE_T))
    assert body.val().isValid() and len(body.solids().vals()) == 1
    # Fit checks on the printed geometry itself.
    assert x0-RADIATOR_FACE_X >= 1.0, "plate must clear the radiator face"
    assert x1-RADIATOR_FACE_X <= OWNER_GAP-5, "holder must fit the owner-measured 75 mm strip"
    assert CARD_X[0]-RADIATOR_FACE_X >= 2.5, "card heatsink to radiator face"
    for over in (RISER_X0-x0, x1-(RISER_X0+W), RISER_Y0-y0, y1-(RISER_Y0+L)):
        assert 0 <= over <= MAX_OVERHANG, ("plate past the board outline", over)
    for u, v in HOLES_UV:
        x, y = riser_xy(u, v)
        assert min(x-x0, x1-x, y-y0, y1-y) >= BOSS_D/2 - .01, ("boss inside the plate", u, v)
        assert not (wx0-BOSS_D/2 < x < wx1+BOSS_D/2 and wy0-BOSS_D/2 < y < wy1+BOSS_D/2), "boss over the window"
    for x, y in ANCHORS:
        assert x-SLOT_W/2-x0 >= EDGE_WALL-.01 and x1-(x+SLOT_W/2) >= EDGE_WALL-.01, (x, "slot side wall")
        assert y-SLOT_L/2-y0 >= EDGE_WALL and y1-(y+SLOT_L/2) >= EDGE_WALL, (y, "slot end wall")
        assert x+SLOT_W/2 <= wx0-EDGE_WALL or x-SLOT_W/2 >= wx1+EDGE_WALL, (x, "slot to window")
    # The stop sits on solid plate, beside (not under) the slot's pin rows.
    slot_v1 = d(RISER, "slot_center_from_edge") + d(RISER, "slot_width")/2
    assert STOP_UV[1] - STOP_SIZE[1]/2 >= slot_v1 + 1.0, "stop clear of the slot pins"
    assert sx + STOP_SIZE[1]/2 <= wx0 - 2.0, "stop on solid plate"
    # Washer and M4 head (allowance 4 mm) under the board, clear of its underside.
    assert BASE_T + 4.0 <= RISER_Z - 1.0, "anchor heads under the board"
    # SATA socket and plug body hang clear of the plate top and the rear bosses.
    assert RISER_Z - d(RISER, "sata_underside_depth") - BASE_T >= SATA_CLEARANCE - .01
    for u, v in HOLES_UV:
        if u > L/2:
            assert v + BOSS_D/2 <= d(RISER, "sata_v_start") or v - BOSS_D/2 >= d(RISER, "sata_v_end"), "rear boss under the SATA plug"
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
    sata_x0, sata_x1 = (RISER_X0 + d(RISER, k) for k in ("sata_v_start", "sata_v_end"))
    sata_y0 = RISER_Y0 + d(RISER, "sata_start")
    sata_d = d(RISER, "sata_underside_depth")
    sff_c = RISER_Y0 + (d(RISER, "sff_start") + d(RISER, "sff_end"))/2
    sff_z = RISER_TOP + d(SFF, "plug_height")/2
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
        ("connectors", "Berserk SFF-8643 riser plug", edge, sff_c-d(SFF, "plug_width")/2, sff_z-d(SFF, "plug_height")/2,
         d(SFF, "plug_length"), d(SFF, "plug_width"), d(SFF, "plug_height"),
         "straight SFF-8643 plug; passes over Kenshin's 6 mm motherboard mount, short of the PCB edge in CAD"),
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
    """Riser plug end -> rise over the mount -> forward along the board edge -> left of the V100 hood -> along the deck front -> H12D plug end."""
    rx, ry, rz = riser_plug.x1, riser_plug.y + riser_plug.d/2, riser_plug.z + riser_plug.h/2
    hx, hy, hz = h12d_plug.x + h12d_plug.w/2, h12d_plug.y, h12d_plug.z + h12d_plug.h/2
    lane_x, front_y, low_z = 86.0, hy-6.0, hz
    return [(rx, ry, rz), (rx+3, ry, 30.0), (rx+3, ry-50, 30.0), (lane_x, 405.0, 30.0),
            (lane_x, front_y, low_z), (hx, front_y, low_z), (hx, hy, hz)]


def report():
    x0, x1, y0, y1 = BASE
    return {
        "part": PART, "quantity": 1,
        "placement": "Kenshin side-AIO strip: radiator inner face X52.3 to Kenshin's motherboard mount, owner-measured about 75 mm",
        "holder_x_range_mm": [round(x0, 2), round(x1, 2)], "holder_x_from_radiator_face_mm": round(x1-RADIATOR_FACE_X, 2),
        "holder_y_range_mm": [y0, y1],
        "plate_past_board_mm": {"radiator_side": MARGIN_RADIATOR, "socket_side": MARGIN_SOCKET, "front": MARGIN_END, "rear": MARGIN_END,
                                "limit": MAX_OVERHANG},
        "riser_origin_xyz_mm": [RISER_X0, RISER_Y0, RISER_Z], "riser_orientation": "slot along +Y at the radiator side, SFF-8643 socket facing +X, SATA socket under the rear end",
        "riser_underside_above_plate_mm": BOSS_H, "sata_socket_clearance_mm": SATA_CLEARANCE,
        "card_plane_x_mm": round(CARD_PLANE_X, 2), "bracket_face_y_mm": round(BRACKET_Y, 2),
        "plate_front_to_bracket_mm": round(y0-BRACKET_Y, 2),
        "card_heatsink_to_radiator_face_mm": round(CARD_X[0]-RADIATOR_FACE_X, 2),
        "riser_fasteners": "four M3 self-tapping screws (board + 8-10 mm) into 2.5 mm pilots in 8 mm bosses, 8 mm tall",
        "slot_deflection_stop": f"{STOP_SIZE[1]:g} x {STOP_SIZE[0]:g} mm land beside the slot at mid-length, {STOP_GAP:g} mm below the board",
        "bracket": "no bracket support (owner: the slot holds the card); the full-height bracket stands free in front of the plate",
        "shelf_anchor_xy_mm": [[round(x, 2), round(y, 2)] for x, y in ANCHORS], "shelf_fastener": "4 x M4 with OD12 washers and steel backing",
        "print": "PETG, base on the bed as installed; vertical bosses and a through window, no overhangs or supports",
        "assembly_order": "bolt the bare holder to the shelf (the radiator-side anchor is under the card), screw the riser on, seat the card, then plug SATA from behind, SFF-8643 and the DAC",
        "airflow": "the side AIO fans pull air from this strip through the radiator, across the card heatsink; the 300 LFM the card needs is not verified",
        "to_measure": ["riser board length and width, and the hole insets from its edges", "SATA socket span on the underside",
                       "bracket face to x16 slot start on the card", "QSFP28 cage height on the card", "actual radiator-to-mount gap"],
        "physical_fit_verified": False,
    }
