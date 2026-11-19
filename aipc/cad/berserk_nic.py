"""Berserk's ConnectX-4 Lx on the LRFC6911N riser, beside Kenshin's side AIO.

Placed in the strip between the side radiator's inner face (X52.3) and
Kenshin's motherboard mount; the owner measured about 75 mm across it
(2026-11-19). Shelf coordinates throughout (X right, Y rear, Z up).

The riser lies flat with its x16 slot along +Y, so the card stands upright
with its bracket and QSFP28 cage facing the rack front. With the bracket at
the front, the riser's SATA and SFF-8643 sockets face +X (toward Kenshin's
board); that follows from the photographed layout (slot on one long edge,
sockets on the other, slot key at the power-circuit end).

The printed holder is one piece: a 6 mm base with three M4 shelf slots,
four riser bosses (three M3 self-tapping screws, one locating peg under the
gate) and a gate in front of the card bracket. The bracket face bears on the
radiator-side post and the bridge's rear face (the riser-side column stands
clear of the bracket); the bracket tab rests on the bridge, which is printed
solid and drilled through the tab's own hole at assembly, so the unmeasured
bracket-to-slot offset cannot misplace it. The QSFP28 plug passes through the
gate opening.

Riser and card interfaces are photo estimates or assumptions: measure the
riser holes, the bracket-to-slot offset and the tab height before printing.
"""
import cadquery as cq
from hwkit import spec

RISER, NIC, DAC, SFF = ("linkreal-lrfc6911n", "nvidia-mcx4131a-gcat",
                        "qsfp28-passive-dac", "sff-8643-pcie-cable")
PART = "berserk_nic_holder"

d = spec.dim
RADIATOR_FACE_X = 52.328          # Kenshin GA II radiator inner face (shelf_layout)
OWNER_GAP = 75.0                  # owner: radiator to Kenshin motherboard mount, about 75 mm
BASE_T, BOSS_H, BOSS_D, PILOT_D = 6.0, 3.0, 8.0, 2.5
PEG_D, PEG_H = 2.8, 1.5   # locates the riser's front hole (hole 3.2 mm, assumed)

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
# The front slot-edge hole sits under the gate bridge, out of driver reach: it
# gets a plain bearing pad, the other three take M3 self-tapping screws.
PAD_UV = HOLES_UV[0]
SCREW_UV = HOLES_UV[1:]

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

# Gate in front of the bracket: two columns and a bridge under the bracket tab.
GATE_Y = (BRACKET_Y - 20.0, BRACKET_Y)
POST_X = (53.5, 59.5)
COL_X = (74.5, 80.5)
COL_Y = (GATE_Y[0], RISER_Y0 - 1.0)     # stops in front of the riser board
BRIDGE_T = 6.0
# Tab underside estimated about 72 mm above the slot board (79.2 mm LP bracket);
# the bridge sits 6 mm lower so the card always seats, then shim up to the tab.
BRIDGE_TOP = RISER_TOP + 66.0
TAB_SCREW = (CARD_PLANE_X, BRACKET_Y - 7.0)   # nominal; drilled 2.5 mm at assembly through the tab
TAB_SCREW_MAX = 8.0                      # M3 self-tapping: tab + shim + at most 6 mm into the bridge
WEB_REACH = 20.0                         # forward web reach (guideline 15-30 mm)
POST_GUSSET = (10.0, 34.0)               # X reach, height of the post's inward gusset
# 45-degree corner chamfers under the bridge shorten the bridged span; the
# riser-side one is wider. Both stay clear of the QSFP28 plug below.
POST_CHAMFER, COL_CHAMFER = 3.0, 4.0

BASE = (53.5, 121.0, GATE_Y[0] - WEB_REACH, 600.0)  # x0, x1, y0, y1
WINDOW = (76.0, 98.0, 480.0, 556.0)
ANCHORS = ((95.0, BASE[2] + 12.0), (90.0, 590.0), (114.0, 545.0))
SLOT_L, SLOT_W = 10.0, 5.5


def holder():
    """Printable as installed: base on the bed, gate bridge spans 15 mm."""
    x0, x1, y0, y1 = BASE
    body = cq.Workplane("XY").box(x1-x0, y1-y0, BASE_T, centered=False).translate((x0, y0, 0))
    wx0, wx1, wy0, wy1 = WINDOW
    body = body.cut(cq.Workplane("XY").box(wx1-wx0, wy1-wy0, BASE_T, centered=False).translate((wx0, wy0, 0)))
    for u, v in HOLES_UV:
        x, y = riser_xy(u, v)
        body = body.union(cq.Workplane("XY").center(x, y).circle(BOSS_D/2).extrude(BOSS_H).translate((0, 0, BASE_T)))
    px, py = riser_xy(*PAD_UV)
    body = body.union(cq.Workplane("XY").center(px, py).circle(PEG_D/2).extrude(PEG_H).translate((0, 0, BASE_T+BOSS_H)))
    for u, v in SCREW_UV:
        x, y = riser_xy(u, v)
        body = body.cut(cq.Workplane("XY").center(x, y).circle(PILOT_D/2).extrude(BOSS_H+BASE_T-1).translate((0, 0, 1)))
    gate_h = BRIDGE_TOP
    post = cq.Workplane("XY").box(POST_X[1]-POST_X[0], GATE_Y[1]-GATE_Y[0], gate_h, centered=False).translate((POST_X[0], GATE_Y[0], 0))
    col = cq.Workplane("XY").box(COL_X[1]-COL_X[0], COL_Y[1]-COL_Y[0], gate_h, centered=False).translate((COL_X[0], COL_Y[0], 0))
    bridge = (cq.Workplane("XY").box(COL_X[1]-POST_X[0], GATE_Y[1]-GATE_Y[0], BRIDGE_T, centered=False)
              .translate((POST_X[0], GATE_Y[0], BRIDGE_TOP-BRIDGE_T)))
    body = body.union(post).union(col).union(bridge)
    # Forward webs tie both columns into the base for plug insertion loads.
    for xa, xb in (POST_X, COL_X):
        web = (cq.Workplane("YZ").polyline(((y0, BASE_T), (GATE_Y[0], BASE_T), (GATE_Y[0], 40.0)))
               .close().extrude(xb-xa).translate((xa, 0, 0)))
        body = body.union(web)
    under = BRIDGE_TOP - BRIDGE_T
    gate_d = GATE_Y[1] - GATE_Y[0]
    # Corner chamfers in the gate opening, full gate depth (XZ profile along +Y).
    for pts in (((POST_X[1], under-POST_CHAMFER), (POST_X[1]+POST_CHAMFER, under), (POST_X[1], under)),
                ((COL_X[0], under-COL_CHAMFER), (COL_X[0]-COL_CHAMFER, under), (COL_X[0], under))):
        body = body.union(cq.Workplane("XZ").polyline(pts).close().extrude(-gate_d).translate((0, GATE_Y[0], 0)))
    # Behind the riser-side column the bridge would hang 10 mm over air (the
    # column stops in front of the riser). A 45-degree wedge carries it, and
    # reaches low enough to sit under the column-side chamfer at the rear.
    behind = GATE_Y[1] - COL_Y[1]
    wedge_low = under - COL_CHAMFER - behind
    body = body.union(cq.Workplane("YZ").polyline(((COL_Y[1], wedge_low), (GATE_Y[1], wedge_low+behind),
                                                    (GATE_Y[1], under), (COL_Y[1], under)))
                      .close().extrude(COL_X[1]-COL_X[0]).translate((COL_X[0], 0, 0)))
    # Inward gusset on the post (X stiffness), in front of the bracket and
    # below the QSFP28 plug.
    gx, gz = POST_GUSSET
    body = body.union(cq.Workplane("XZ").polyline(((POST_X[1], BASE_T), (POST_X[1]+gx, BASE_T), (POST_X[1], BASE_T+gz)))
                      .close().extrude(-(COL_Y[1]-GATE_Y[0])).translate((0, GATE_Y[0], 0)))
    for x, y in ANCHORS:
        body = body.cut(cq.Workplane("XY").center(x, y).slot2D(SLOT_L, SLOT_W, 90).extrude(BASE_T))
    assert body.val().isValid() and len(body.solids().vals()) == 1
    # Fit checks on the printed geometry itself.
    assert POST_X[0]-RADIATOR_FACE_X >= 1.0, "gate post must clear the radiator face"
    assert BASE[1]-RADIATOR_FACE_X <= OWNER_GAP-5, "holder must fit the owner-measured 75 mm strip"
    assert CARD_X[0]-RADIATOR_FACE_X >= 2.5, "card heatsink to radiator face"
    for x, y in ANCHORS:
        assert x-SLOT_W/2-BASE[0] >= 4 and BASE[1]-(x+SLOT_W/2) >= 4, (x, "slot side wall")
        assert y-SLOT_L/2-BASE[2] >= 4 and BASE[3]-(y+SLOT_L/2) >= 4, (y, "slot end wall")
    assert COL_Y[1] <= RISER_Y0 and GATE_Y[1] <= BRACKET_Y
    assert BASE_T + POST_GUSSET[1] <= CAGE_Z - d(DAC, "plug_width")/2 - 5, "post gusset below the plug"
    assert PEG_D <= d(RISER, "hole_diameter") - .3
    # The QSFP28 plug clears both chamfers and the bridge.
    plug_x0 = CAGE_X - d(DAC, "plug_height")/2
    plug_x1 = CAGE_X + d(DAC, "plug_height")/2
    plug_top = CAGE_Z + d(DAC, "plug_width")/2
    assert plug_x0 - POST_X[1] >= 1 and COL_X[0] - plug_x1 >= 1
    assert under - POST_CHAMFER + (plug_x0 - POST_X[1]) - plug_top >= 1.5, "post chamfer over plug"
    assert COL_X[0] - COL_CHAMFER >= plug_x1 or under - (plug_x1 - (COL_X[0]-COL_CHAMFER)) - plug_top >= 1.5
    assert under - plug_top >= 3
    return body


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
    sata_y0, sata_y1 = (RISER_Y0 + d(RISER, k) for k in ("sata_start", "sata_end"))
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
        ("connectors", "Berserk riser SATA power plug", edge, sata_y0, RISER_TOP, d(RISER, "sata_plug_projection"), sata_y1-sata_y0, 9.0,
         "right-angle SATA power plug from the Hercules; projection is an allowance"),
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
    return {
        "part": PART, "quantity": 1,
        "placement": "Kenshin side-AIO strip: radiator inner face X52.3 to Kenshin's motherboard mount, owner-measured about 75 mm",
        "holder_x_range_mm": [BASE[0], BASE[1]], "holder_x_from_radiator_face_mm": round(BASE[1]-RADIATOR_FACE_X, 2),
        "holder_y_range_mm": [BASE[2], BASE[3]], "gate_top_z_mm": round(BRIDGE_TOP, 2),
        "riser_origin_xyz_mm": [RISER_X0, RISER_Y0, RISER_Z], "riser_orientation": "slot along +Y at the radiator side, sockets facing +X",
        "card_plane_x_mm": round(CARD_PLANE_X, 2), "bracket_face_y_mm": round(BRACKET_Y, 2),
        "card_heatsink_to_radiator_face_mm": round(CARD_X[0]-RADIATOR_FACE_X, 2),
        "riser_fasteners": "three M3 self-tapping screws into 2.5 mm pilots in 8 mm bosses; the front slot-edge hole sits on a 2.8 mm locating peg under the gate bridge (no driver access): hold the riser down when pulling the card",
        "bracket": "plug loads go through the radiator-side post and the bridge's rear face; the riser-side column stands clear of the bracket. The bridge is printed solid: shim up to the tab, drill 2.5 mm through the tab hole, fit an M3 self-tapping screw no longer than 8 mm",
        "shelf_anchor_xy_mm": list(ANCHORS), "shelf_fastener": "3 x M4 with OD12 washers and steel backing",
        "print": "PETG, base on the bed as installed; 45-degree chamfers cut the gate bridge to an 8 mm span, a 45-degree wedge carries the bridge behind the riser-side column, 20 mm forward webs and an inward post gusset; no supports. Independent print audit 2026-11-19",
        "assembly_order": "bolt the bare holder to the shelf, screw the riser on, seat the card, fit the tab screw, then plug SATA, SFF-8643 and the DAC",
        "airflow": "the side AIO fans pull air from this strip through the radiator, across the card heatsink; the 300 LFM the card needs is not verified",
        "to_measure": ["riser board width, hole positions and socket positions", "bracket face to x16 slot start on the card",
                       "bracket tab height above the riser", "QSFP28 cage height on the card", "actual radiator-to-mount gap",
                       "whether the bracket's lower tongue clears the riser board, which runs 9 mm in front of the bracket plane"],
        "physical_fit_verified": False,
    }
