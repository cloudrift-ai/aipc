"""Hammond RSUS1931BK1 sliding-shelf layout for Kenshin and Berserk.

Regenerate with make cad. Dimensions
are millimetres. The drilled shelf and printed brackets are fit prototypes:
the rack, shelf, board holes and cards must be surveyed before drilling.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from itertools import combinations

import cadquery as cq
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from psu_bracket_preview import render as render_psu_preview
from motherboard_mounts_preview import render as render_motherboard_mounts_preview
from aio_fan_mount_preview import render as render_aio_fan_mount_preview
import berserk_platform as bp
import berserk_aio_brace as aio_brace
import kenshin_aio_mount as k_aio
import berserk_nic as nic
import rack_gpu_exhaust as gpu_exhaust
import tilted_gpu_cooling as t_cool
import atx_shelf_mounts as atx_mount
from hwkit.components import atx_psu_bracket as psu_bracket
from hwkit.components import pcie_post as post_hw
from hwkit.components import hammond_shelf as rail_assembly
from pcie_post_mount_preview import render as render_pcie_post_preview
from hwkit import spec
from hwkit.export import export_print
from hwkit.registry import classify_assembly
from rack_shelf_coordinates import (BUILD_FORWARD_SHIFT, shelf_y, SHELF_W, SHELF_D, KENSHIN_RAIL_DEPTH,
                                    SHELF_T, BERSERK_DX, BERSERK_DY, K_TX, K_TY, k_xy, k_shape)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "models"
OUT.mkdir(parents=True, exist_ok=True)

# Solid Hammond deck. Published dimensions and illustrative factory-slide
# geometry are documented in hammond_shelf.py; physical interfaces unmeasured.
VENT_X, VENT_ROWS = (), 0
VENT_LENGTH, VENT_WIDTH, VENT_FIRST_Y, VENT_PITCH_Y = 0, 0, 0, 1
H115I_FRAME_X = (120.0, 260.0)
H115I_SCREW_X = (127.75, 252.25, 267.75, 392.25)
B_PSU_Y, B_PSU_REAR_Y = 0.0, 245.0
# GA II Lite Performance 360: published radiator397x120x27, fans124x120x28.
# Rear fans pull through the radiator; existing frames bear its lower edge.
# Outer fans clamp through the 6mm frames; one plain middle spacer keeps
# all three fans coplanar for their factory side bridge connectors.
K_LEFT_SHIFT = 2.0  # retained component-local datum before the installed 180-degree turn
K_REAR_SHIFT = 8.0  # retained local datum; installation follows k_xy/k_shape
K_AIO_X, K_AIO_Y, K_AIO_Z = 12.5, 787.5, 20.0+k_aio.SUPPORT_T
K_AIO_FRAME_REAR_Y = K_AIO_Y + 33.0
K_AIO_FAN_Y = K_AIO_FRAME_REAR_Y
K_AIO_FRAME_X = k_aio.FRAME_X
K_AIO_FRAME_W, K_AIO_FRAME_H = k_aio.FRAME_W, k_aio.FRAME_H
K_AIO_FOOT_X, K_AIO_FOOT_W, K_AIO_REACH = k_aio.FOOT_X, k_aio.FOOT_W, k_aio.REACH
K_AIO_ANCHORS = k_aio.ANCHORS
RAD_FOOT_REACH = 40.0  # preserve the fitted sandwich's feet and shelf anchors
RAD_ANCHORS = ((24.0, 28.0), (116.0, 28.0))
PSU_SHELF_ANCHORS = psu_bracket.SHELF_ANCHORS
PSU_FOOT_REACH = psu_bracket.FOOT_REACH
# EIA-310 minimum clear opening between rack rails. Anything above the deck
# must pass the front rails when the shelf slides, so side overhang is capped
# at half the difference (13.67 mm each side), less a 1 mm margin.
RACK_OPENING_W = 450.0
SIDE_OVERHANG_LIMIT = (RACK_OPENING_W - SHELF_W) / 2
SIDE_MARGIN = 1.0
# Hercules sticks out past the left deck edge: wider fan lane to the V100s.
PSU_BERSERK_X = -10.0
GPU_REST_X, GPU_REST_Y, GPU_REST_ANCHOR_Y = 45.0 - K_LEFT_SHIFT, 334.0, 12.5
GPU_REST_D = 42.0
REAR_ASSEMBLY_LIMIT_Y = K_AIO_FAN_Y + 28 + 4  # washer and head survey envelope (radiator-local)
# The whole GA II group (radiator, frames, fans, spacer, screws) is
# built in its radiator-local frame above (length along +X, hose end at low X,
# fans toward +Y) and turned +90 degrees about Z onto the deck's left edge:
# radiator length along +Y with the hose end toward the front, fans
# exhausting toward -X past the deck edge. Screw heads stop 1 mm inside the
# rack opening. K_AIO_FRONT_Y puts the rear bearing frame's whole footprint
# 0.5 mm inside the deck rear; the radiator end then overhangs the rear.
K_AIO_FRONT_Y = SHELF_D - .5 - (K_AIO_FRAME_X[1] + K_AIO_FRAME_W) + K_AIO_X
K_AIO_DX = REAR_ASSEMBLY_LIMIT_Y - SIDE_OVERHANG_LIMIT + SIDE_MARGIN
K_AIO_DY = K_AIO_FRONT_Y - K_AIO_X


def k_aio_xy(x, y):
    return K_AIO_DX - y, x + K_AIO_DY


def k_aio_pt(p):
    return [*k_aio_xy(p[0], p[1]), *p[2:]]


def k_aio_shape(shape):
    return shape.rotate((0, 0, 0), (0, 0, 1), 90).translate((K_AIO_DX, K_AIO_DY, 0))


# HX1200i on its side along the rear edge, rear (AC) face toward -X, beside
# the radiator's rear frame. Its body starts 0.1 mm behind Kenshin's turned
# rear PCB edge (see K_TY) and overhangs the deck rear.
K_PSU_FACE_X = 130.0
K_PSU_Y = k_xy(atx_mount.BOARDS['Kenshin'][0], 0)[1] + 0.1
# Allowance for parts past the deck rear (HX1200i, side-AIO radiator); the
# cabinet depth behind the rear rails is unmeasured.
REAR_OVERHANG_LIMIT = 35.0
U = 44.45
COMPONENT_Z_LIMIT = 5 * U  # 222.25mm component planning band, not overall rack allocation
LOWER_Z_REFERENCE = 4 * U
RAIL_T, STANDOFF_H = 6.0, spec.dim('keystone-1451b', 'length')
SHELF_SLOT_LENGTH, SHELF_SLOT_WIDTH = 10.0, 5.5  # M4, front-to-rear adjustment in printed mounts
BERSERK_X, KENSHIN_X, BOARD_Z, BOARD_T = bp.X, 8.0 - K_LEFT_SHIFT, RAIL_T + STANDOFF_H, 1.6
# Baseline single-fan revision offsets Kenshin and its cards/AIO 8 mm rearward.
# The shared forward shift now moves both PCs, PSUs and all assembly interfaces.
FRONT_Y, REAR_Y = shelf_y(80.0), shelf_y(425.0 + K_REAR_SHIFT)
# The front fascia appears to turn down below the deck. A 20 mm lift leaves
# room for the radiator's bearing ledges and shelf fasteners.
# The previous 56 mm lift had no modeled clearance or airflow benefit.
RAD_Z, RAD_H = 20.0, spec.dim('corsair-h115i', 'radiator_height')
RAD_TOP = RAD_Z + RAD_H
RAD_FRAME_SLOT_L, RAD_FRAME_SLOT_W = 7.0, 4.5
# Owner's 2026-10-17 approximate measurement: blue vertical face overhangs13mm.
# Front -> rear: fans, original5mm bracket, radiator. Independent of board shift.
RAD_FRAME_FRONT_Y = 9.0
RAD_FRAME_T, RAD_D, RAD_FAN_D = 5.0, spec.dim('corsair-h115i', 'radiator_thickness'), spec.dim('corsair-h115i', 'fan_depth')
RAD_Y = RAD_FRAME_FRONT_Y + RAD_FRAME_T
RAD_FAN_Y = RAD_FRAME_FRONT_Y - RAD_FAN_D
_V100 = spec.get('nvidia-v100-pcie-16gb')
V100_W, V100_D, V100_H = _V100.dim('thickness'), _V100.dim('length'), _V100.dim('height')
_RTX = spec.get('zotac-rtx-5090-solid')
_GA2 = spec.get('lian-li-ga2-lite-360')
_H115I = spec.get('corsair-h115i')
_HERC = spec.get('rosewill-hercules-1600')
_HX = spec.get('corsair-hx1200i')
_NIC = spec.get('nvidia-mcx4131a-gcat')
# Installed drive per M.2 slot, in bp.M2_STANDOFFS order. Which slot holds the
# 3500 is not recorded; both are 2280 drives with the same envelope.
_M2_SLOTS = [spec.get(i) for i in ('micron-3400-2tb', 'micron-3400-2tb', 'micron-3500-2tb')]
V100_SLOTS = bp.GPU_BODY_X
V100_FRONT_Y = shelf_y(100.0)+BERSERK_DY
V100_TAIL_Y = V100_FRONT_Y + V100_D
BERSERK_BOARD_Y = bp.FRONT_Y
COOL_X, COOL_Y, COOL_Z = t_cool.X0, t_cool.CY, t_cool.CZ
COOL_W, COOL_H, COOL_FAN_D = t_cool.WIDTH, t_cool.HEIGHT, t_cool.FAN_DEPTH
COOL_PANEL_T, COOL_PILOT_D = t_cool.PANEL, 3.3
COOL_FAN_SIZE, COOL_FAN_HOLES, COOL_FAN_FLANGE_T = 140.0, 124.5, 4.0
COOL_FAN_CLEARANCE_D = 4.5
COOL_FAN_BB = t_cool.fan_envelope().val().BoundingBox()
COOL_FAN_MODEL = "Sanyo Denki 9GV1412P1S001"
# Official San Ace catalog pp185–188: dimensioned drawing, not manufacturer CAD.
COOL_FAN_SOURCE = "https://publish.sanyodenki.com/San_Ace_E/book/data/San_Ace_E.pdf"


@dataclass(frozen=True)
class Box:
    name: str
    x: float
    y: float
    z: float
    w: float
    d: float
    h: float
    note: str

    @property
    def x1(self):
        return self.x + self.w

    @property
    def y1(self):
        return self.y + self.d

    @property
    def z1(self):
        return self.z + self.h

    def shape(self):
        if self.name == "V100 pressure fan": return t_cool.fan_envelope()
        return cq.Workplane("XY").box(self.w, self.d, self.h,
                                     centered=(False, False, False)).translate(
                                         (self.x, self.y, self.z))


def hex_rotation(system: str):
    """Hex base clocking: one corner toward the PCB, which turns with Kenshin."""
    return post_hw.BASE_ROTATION_DEG + (-90 if system.lower().startswith("kenshin") else 0)


class PostBaseEnvelope(Box):
    """Purchased hex base in the orientation required by its clearance slot."""
    def shape(self):
        turn = -90 if self.name.startswith("Kenshin") else 0
        return (cq.Workplane("XY").polyline(post_hw.base_hex_points()).close()
                .extrude(self.h).rotate((0,0,0),(0,0,1),turn)
                .translate((self.x+self.w/2,self.y+self.d/2,self.z)))


# Selected upgrade, not installed inventory. NVIDIA's dimensioned product
# brief establishes V100 body length/height; 40 mm thickness and slot/flange
# positions remain provisional. Existing 1080 Ti ownership stays in inventory.
parts = [
    Box("Berserk ATX board", BERSERK_X, BERSERK_BOARD_Y, BOARD_Z, bp.WIDTH, bp.DEPTH, BOARD_T,
        "H12D-8D + BMC; manufacturer photograph and ATX datums, delivered revision and interfaces unmeasured"),
    *(Box(f"Berserk V100 16GB {slot}", x, V100_FRONT_Y, 24, V100_W, V100_D, V100_H,
          "NVIDIA PCIe 16GB passive card; factory drawing body, provisional slot and 40 mm thickness; remove shipping extenders")
      for slot, x in V100_SLOTS.items()),
    Box("Berserk SP3 CPU and pump survey", bp.CPU_CENTER[0]-37.5, bp.CPU_CENTER[1]-37.5, BOARD_Z + BOARD_T, 75, 75, 50,
        "EPYC 7702P; photo-estimated socket center. H115i retained conditionally: verify SP3 mount, cold-plate coverage and hose reach"),
    *(Box(f"Berserk RDIMM {i+1} survey", bp.photo_xy(830,py)[0]-2.5,
          bp.photo_xy(1160,py)[1], BOARD_Z+BOARD_T, 5, 139, 32,
          "8x32GB Micron DDR4-2933 ECC RDIMMs installed; photo-based socket locations and provisional module height")
      for i,py in enumerate((42,84,126,168,618,660,702,744))),
    Box("Berserk BMC module survey", bp.photo_xy(1280,1350)[0], bp.photo_xy(1280,1350)[1],
        BOARD_Z+BOARD_T, 70, 48, 7,
        "Included BMC; photo envelope with provisional7mm installed height; verify heatsinks/headers and GPU underside clearance"),
    Box("V100 pressure fan", COOL_FAN_BB.xmin, COOL_FAN_BB.ymin, COOL_FAN_BB.zmin,
        COOL_FAN_BB.xlen, COOL_FAN_BB.ylen, COOL_FAN_BB.zlen,
        "Sanyo 9GV1412P1S001, 45-degree upward exhaust; bounding box only, shape is rotated; occupies reserved upper duct volume"),
    *(Box(f"Berserk M2 SSD {i+1}", x - m2.dim('width')/2, y - m2.dim('length'), BOARD_Z + BOARD_T,
          m2.dim('width'), m2.dim('length'), m2.dim('thickness'),
          f"{m2.name} at photo-estimated M.2 standoffs; connector end assumed toward the front; clearance beneath the V100s unverified")
      for i, ((x, y), m2) in enumerate(zip(bp.M2_STANDOFFS, _M2_SLOTS, strict=True))),
    Box("Kenshin ATX board", KENSHIN_X, REAR_Y, BOARD_Z, spec.dim('gigabyte-x870e-aorus-pro', 'pcb_width'), spec.dim('gigabyte-x870e-aorus-pro', 'pcb_depth'), BOARD_T,
        "Gigabyte X870E footprint; PCIe slot position approximate"),
    Box("Kenshin RTX 5090", 48 - K_LEFT_SHIFT, shelf_y(339.3 + K_REAR_SHIFT), 24, _RTX.dim('thickness'), _RTX.dim('length'), _RTX.dim('height'),
        "Zotac published envelope; socket position to measure"),
    Box("5090 straight power-cable keepout", 48 - K_LEFT_SHIFT, shelf_y(339.3 + K_REAR_SHIFT), 24 + _RTX.dim('height'), _RTX.dim('thickness'), _RTX.dim('length'), 35,
        "conservative full-card sweep; actual connector area is smaller"),
    Box("Kenshin GA II Lite pump", 208.5 - K_LEFT_SHIFT, shelf_y(529 + K_REAR_SHIFT), BOARD_Z + BOARD_T, 74, 74, 67,
        "GA2L36PB owned replacement per 2025-05-30 receipt; socket and hose ports provisional"),
    Box("Berserk H115i radiator", 104, RAD_Y, RAD_Z, _H115I.dim('radiator_length'), RAD_D, RAD_H,
        "owner photo confirms original bracket between fan and radiator; bracket front Y~-13 measured; radiator envelope remains approximate"),
    Box("H115i intake fans", 120, RAD_FAN_Y, RAD_Z, 2 * _H115I.dim('fan_size'), RAD_FAN_D, _H115I.dim('fan_size'),
        "two existing 140mm fans in front of the original brackets and radiator; intended push front-to-rear; arrows need checking"),
    Box("Berserk owned Hercules 1600W PSU", PSU_BERSERK_X, B_PSU_Y, 0, _HERC.dim('height'), _HERC.dim('depth'), _HERC.dim('width'),
        "245 mm planning depth allows a few mm beyond ~241 mm nominal; fan +X, AC rear"),
    Box("Kenshin owned HX1200i PSU", K_PSU_FACE_X, K_PSU_Y, 0, _HX.dim('depth'), _HX.dim('height'), _HX.dim('width'),
        "ATX unit on its side along the rear edge; AC inlet faces -X, fan faces the rack rear (+Y); overhangs the deck rear; rear intake clearance unmeasured"),
    Box("Kenshin GA II Lite radiator", K_AIO_X, K_AIO_Y, K_AIO_Z, _GA2.dim('radiator_length'), _GA2.dim('radiator_thickness'), _GA2.dim('radiator_height'),
        "Lian Li GA2L36PB published dimensions; 105mm mounting pitch and hose ports provisional"),
    *(Box(f"Kenshin AIO exhaust fan {i+1}", 29 + 120*i,
          K_AIO_FAN_Y, K_AIO_Z - 2, _GA2.dim('fan_width'), _GA2.dim('fan_depth'), _GA2.dim('fan_envelope_height'),
          "Owned Performance fan; pull through radiator toward rear. All fans coplanar on 6mm frames/spacer for factory side bridges. 2mm side connector allowance is provisional.")
      for i in range(3)),
]
connectors = [
    *(Box(f"V100 {slot} angled EPS plug target", x + 25, V100_FRONT_Y - bp.EPS_PROJECTION,
          94, 15, bp.EPS_PROJECTION, 22,
          "18mm target projection only, not a measured product; use CPU/EPS pinout after V100 dual-PCIe-to-EPS adapter, verify exit direction, current rating and bends")
      for slot, x in V100_SLOTS.items()),
    Box("Berserk AC plug + tail", PSU_BERSERK_X + 16, B_PSU_REAR_Y, 99, 54, 60, 41,
        "Owner reports PSU top-to-connector gap >10mm on 2026-10-18; model uses10mm minimum at inlet-side upper boundary. Remaining plug dimensions and straight-tail sweep are provisional; verify molded plug body after seating."),
    Box("Kenshin low-profile C13 plug + bend", K_PSU_FACE_X - 60, K_PSU_Y + 12.5, 97, 60, 54, 41,
        "side/upward-exit cord survey inside the bracket window, behind the -X rear face; verify inlet and bend radius"),
    Box("Berserk Ethernet RJ45 boot + bend", 305+BERSERK_DX, V100_TAIL_Y, 25, 28, 27, 50,
        "H12D dual2.5GbE position estimated from manufacturer photo; BMC management port/cable within I/O service reserve still needs survey"),
    Box("Kenshin 24-pin survey", 278 - K_LEFT_SHIFT, REAR_Y, 14, 50, 74, 58,
        "conservative reserve starts at PCB front edge; official board diagram shows header close to edge; survey latch and cable projection"),
    # Owner's 2026-11-16 mock-up: the ConnectX card sits in the next slot behind
    # the 5090 and stays reachable from the side. Slot position is a photo
    # estimate; the card body uses the datasheet low-profile size.
    Box("Kenshin ConnectX-4 Lx card", 22.0, REAR_Y + spec.dim('gigabyte-x870e-aorus-pro', 'pcb_depth') - _NIC.dim('card_length'), 24,
        20.0, _NIC.dim('card_length'), _NIC.dim('card_height'),
        "MCX4131A-GCAT low-profile card in a chipset slot behind the RTX 5090 (owner photo); slot centre and installed thickness are photo estimates; QSFP28 cage and DAC face the shelf's right side"),
]


def turn_k_box(box):
    # -90 degrees about Z: local far-X / near-Y corner becomes the new minimum.
    x, y = k_xy(box.x1, box.y)
    return replace(box, x=x, y=y, w=box.d, d=box.w)


def k_aio_box(box):
    x, y = k_aio_xy(box.x, box.y1)
    return replace(box, x=x, y=y, w=box.d, d=box.w)


K_TURNED_PARTS = {'Kenshin ATX board', 'Kenshin RTX 5090',
                 '5090 straight power-cable keepout', 'Kenshin GA II Lite pump',
                 'Kenshin 24-pin survey', 'Kenshin ConnectX-4 Lx card'}
K_AIO_PARTS = {'Kenshin GA II Lite radiator', *(f'Kenshin AIO exhaust fan {i+1}' for i in range(3))}
# Radiator-local boxes keep their factory-hole construction below.
k_aio_local_boxes = {p.name: p for p in parts if p.name in K_AIO_PARTS}
parts = [turn_k_box(p) if p.name in K_TURNED_PARTS else k_aio_box(p) if p.name in K_AIO_PARTS else p
         for p in parts]
connectors = [turn_k_box(p) if p.name in K_TURNED_PARTS else p for p in connectors]
# Kenshin's card is a real part (the owned ConnectX), placed by the mock-up.
parts.append(connectors.pop(next(i for i,b in enumerate(connectors) if b.name == "Kenshin ConnectX-4 Lx card")))
# Berserk's ConnectX on the LRFC6911N riser in the strip beside Kenshin's
# side AIO, its plugs, and the H12D end of the SFF-8643 cable. The H12D
# ports are photo-estimated from the manual's layout figure: three ports on
# the board's front edge, the middle one at 22.6% of the PCB width from the
# shelf-left (V100 PCIE4) side.
H12D_SFF_PORT_X = BERSERK_X + (440-365)/(440-108)*bp.WIDTH
outboard_connectors = []
for kind, *fields in [*nic.boxes(), nic.h12d_sff_plug(H12D_SFF_PORT_X, BERSERK_BOARD_Y, BOARD_Z+BOARD_T)]:
    {"parts": parts, "connectors": connectors}[kind].append(Box(*fields))
_k_nic = next(b for b in parts if b.name == "Kenshin ConnectX-4 Lx card")
outboard_connectors.append(Box(*nic.kenshin_qsfp_plug(_k_nic)[1:]))
# Items allowed past the deck side edges, up to the rack opening.
SIDE_OVERHANG_PARTS = {'Berserk owned Hercules 1600W PSU', *K_AIO_PARTS}


def overlap(a: Box, b: Box) -> bool:
    if "V100 pressure fan" in (a.name,b.name): return a.shape().val().intersect(b.shape().val()).Volume() > .01
    return a.x < b.x1 and a.x1 > b.x and a.y < b.y1 and a.y1 > b.y and a.z < b.z1 and a.z1 > b.z


def solid_shelf_deck():
    """Dimensioned outer deck; gauge thickness and bend details need measurement."""
    deck = (cq.Workplane("XY").box(SHELF_W, SHELF_D, SHELF_T,
                                      centered=(False, False, False))
            .translate((0, 0, -SHELF_T)))
    assert len(deck.solids().vals()) == 1 and deck.val().isValid()
    return deck


base_shelf_deck = solid_shelf_deck()
cq.exporters.export(base_shelf_deck, str(OUT / "rsus1931bk1-solid-deck.step"))


allowed = {
    frozenset(("Kenshin AIO exhaust fan 1", "Kenshin AIO exhaust fan 2")),
    frozenset(("Kenshin AIO exhaust fan 2", "Kenshin AIO exhaust fan 3")),
    *(frozenset(("Berserk ATX board", f"Berserk V100 16GB {slot}")) for slot in V100_SLOTS),
    frozenset(("Kenshin ATX board", "Kenshin RTX 5090")),
    frozenset(("Kenshin ATX board", "Kenshin GA II Lite pump")),
    frozenset(("Kenshin RTX 5090", "5090 straight power-cable keepout")),
    frozenset(("Kenshin ATX board", "Kenshin 24-pin survey")),
    frozenset(("Berserk LRFC6911N riser x16 slot", "Berserk ConnectX-4 Lx card")),
}
for box in parts + connectors:
    side = SIDE_OVERHANG_LIMIT - SIDE_MARGIN if box.name in SIDE_OVERHANG_PARTS else 0
    assert box.x >= -side and box.x1 <= SHELF_W + side, box.name
    depth_limit = SHELF_D + REAR_OVERHANG_LIMIT if box.name in {"Kenshin owned HX1200i PSU", "Kenshin low-profile C13 plug + bend"} or box.name in K_AIO_PARTS else SHELF_D
    front_limit = -BUILD_FORWARD_SHIFT if box.name in {"Berserk H115i radiator", "H115i intake fans", "Berserk owned Hercules 1600W PSU"} else 0
    assert box.y >= front_limit and box.y1 <= depth_limit, box.name
    assert box.z >= 0 and box.z1 <= (400 if box.name == "V100 pressure fan" else COMPONENT_Z_LIMIT), box.name
# Preserve real fitted AIO placement and expose the unresolved planned upgrade.
# These are conflicts, never allowed physical contacts or a fit approval.
planned_upgrade_conflicts = []
for i, a in enumerate(parts + connectors):
    for b in (parts + connectors)[i + 1:]:
        if not overlap(a,b) or frozenset((a.name,b.name)) in allowed:
            continue
        if a.name == "Berserk H115i radiator" and b.name.startswith("V100 ") and b.name.endswith("angled EPS plug target"):
            planned_upgrade_conflicts.append({"components":[a.name,b.name],
                "overlap_y_mm":round(min(a.y1,b.y1)-max(a.y,b.y),3),
                "status":"unresolved planned GPU power clearance; measure/reroute or revise spacing before upgrade"})
        elif b.name == "Berserk SFF-8643 H12D plug" and a.name.startswith("Berserk V100"):
            planned_upgrade_conflicts.append({"components":[a.name,b.name],
                "overlap_z_mm":round(min(a.z1,b.z1)-max(a.z,b.z),3),
                "status":"unresolved: the photo-estimated H12D SFF-8643 ports sit under the V100 tails; locate the ports and measure the tail underside, or use a low-profile/right-angle plug, before the V100 upgrade"})
        elif b.name == "Berserk BMC module survey" and a.name.startswith("Berserk V100"):
            planned_upgrade_conflicts.append({"components":[a.name,b.name],
                "overlap_z_mm":round(min(a.z1,b.z1)-max(a.z,b.z),3),
                "status":"unresolved conservative envelopes: BMC height and GPU underside are unmeasured; inspect actual clearance before assembly"})
        else:
            raise AssertionError(f"collision {a.name} / {b.name}")


# export_print comes from hwkit.export: it writes parts/printed/<name>/ and checks the spec quantity.


# Proposed holes are drilled into the solid deck after surveying the actual
# folded edges, factory slide attachments and underside tool access.
shelf_attachment_holes = []


def add_shelf_hole(part: str, x: float, y: float, slot_length: float = SHELF_SLOT_LENGTH, slot_width: float = SHELF_SLOT_WIDTH, fastener: str = "M4", diameter: float = 5.0, axis: str | None = None):
    """Steel hole under a printed slot. Kenshin's turned parts slot along shelf X."""
    if part == 'gpu_5090_rest_drill_plan':
        x,y = k_xy(x,y)  # rest is laid out in Kenshin's local frame
    if axis is None:
        axis = "X" if part.startswith("kenshin_") or part == 'gpu_5090_rest_drill_plan' else "Y"
    assert 6 <= x <= SHELF_W - 6 and 6 <= y <= SHELF_D - 6, (part, x, y)
    shelf_attachment_holes.append({"part": part, "center_xy_mm": [round(x, 3), round(y, 3)],
                                   "diameter_mm": diameter, "fastener": fastener+" with steel backing",
                                   "printed_bracket_slot_mm": [slot_length, slot_width],
                                   "printed_bracket_slot_axis": "shelf X (side-to-side)" if axis == "X" else "shelf Y (front-to-rear)",
                                   "verified": False})


def slot_offset(site, offset):
    """Displacement along the printed slot of ``site``."""
    return (offset, 0) if site["printed_bracket_slot_axis"].startswith("shelf X") else (0, offset)


def shelf_slot_xy(x: float, y: float, height: float):
    """Printed shelf-facing M4 slot; the corresponding steel hole stays round."""
    return (cq.Workplane("XY").center(x, y)
            .slot2D(SHELF_SLOT_LENGTH, SHELF_SLOT_WIDTH, 90).extrude(height))


def shelf_slot_xz(x: float, depth: float, y_offset: float = 0):
    """Slot in a vertical print plane that lies along shelf Y after rotation."""
    return (cq.Workplane("XZ").center(x, depth)
            .slot2D(SHELF_SLOT_LENGTH, SHELF_SLOT_WIDTH, 90)
            .extrude(-6).translate((0, y_offset, 0)))


def kenshin_aio_end_frame():
    return k_aio.frame()


def kenshin_aio_frame_on_shelf(print_shape: cq.Workplane, x0: float):
    # Flat rear face on bed; all feet and ledges project toward the rack front.
    return print_shape.rotate((0,0,0),(1,0,0),90).translate((x0,K_AIO_FRAME_REAR_Y,k_aio.SUPPORT_T))


k_aio_frame = kenshin_aio_end_frame()


def k_aio_frame_installed(x0: float):
    return k_aio_shape(kenshin_aio_frame_on_shelf(k_aio_frame, x0))

# A plain flat ring supports/seals the center fan without tiny loose spacers.
# 120mm radiator flanges meet edge-to-edge; the former132mm tops would overlap.
k_aio_spacer = cq.Workplane("XY").box(119,119,6,centered=(False,False,False))
k_aio_spacer = k_aio_spacer.cut(cq.Workplane("XY").center(59.5,59.5).circle(55).extrude(6))
for x in (7,112):
    for y in (7,112):
        k_aio_spacer = k_aio_spacer.cut(cq.Workplane("XY").center(x,y).circle(2.25).extrude(6))
k_aio_spacer_local = k_aio_spacer.rotate((0,0,0),(1,0,0),90).translate((151.5,K_AIO_FRAME_REAR_Y,K_AIO_Z+.5))
k_aio_spacer_installed = k_aio_shape(k_aio_spacer_local)


def radiator_screw_frame():
    """Fan-flush frame; retain the fitted sandwich's ledge and shelf interface."""
    # The 140 mm fan occupies the upper 140 mm. Shorter factory-screw slots
    # leave 4.25 mm at the top without extending the rim above the fan.
    frame = cq.Workplane("XY").box(140, RAD_TOP, 5, centered=(False, False, False))
    frame = frame.cut(cq.Workplane("XY").center(70, 70).circle(63).extrude(5))
    # Side ears expose both shelf bolts beside the bearing ledge. The former
    # centerline bolts were hidden beneath it even before fitting the radiator.
    foot = (cq.Workplane("XY").box(116, 6, RAD_FOOT_REACH, centered=(False, False, False))
            .translate((12, 154, 0)))
    frame = frame.union(foot)
    # In assembly the ledge top is Z=20, directly beneath the radiator's
    # bottom edge behind the sandwich face. Screws locate it; ledges carry weight.
    ledge = (cq.Workplane("XY").box(64, 6, 26.5,
                                    centered=(False, False, False))
             .translate((38, 140, 4.5)))
    for gx in (38, 98):
        # A single continuous web connects ledge and foot. Separate opposed
        # triangles left a small V-notch with no clearance or load-path use.
        ledge = ledge.union(cq.Workplane("YZ")
                            .polyline(((140, 0), (160, 0), (160, RAD_FOOT_REACH), (140, 31)))
                            .close().extrude(4).translate((gx, 0, 0)))
    frame = frame.union(ledge)
    # Standard square 140 mm fan pitch is 124.5 mm. Keep the installed axes;
    # 7 x 4.5 mm slots retain vertical adjustment without oversized openings.
    for x in (7.75, 132.25):
        for y in (7.75, 132.25):
            frame = frame.cut(cq.Workplane("XY").center(x, y)
                              .slot2D(RAD_FRAME_SLOT_L, RAD_FRAME_SLOT_W, 90).extrude(5))
    for x, depth in RAD_ANCHORS:
        frame = frame.cut(shelf_slot_xz(x, depth, 154))
    assert 7.75 - RAD_FRAME_SLOT_L / 2 >= 4
    assert 7.75 - RAD_FRAME_SLOT_W / 2 >= 4
    return frame


rad_frame = radiator_screw_frame()
aio_brace_installed = aio_brace.installed(RAD_Y + RAD_D)
aio_brace_print = aio_brace.printable()


def radiator_frame_on_shelf(print_shape: cq.Workplane, x0: float):
    # (print X,Y,Z) -> (shelf X, RAD_FRAME_FRONT_Y+print Z, 160-print Y).
    return print_shape.rotate((0, 0, 0), (1, 0, 0), -90).translate(
        (x0, RAD_FRAME_FRONT_Y, RAD_TOP))


# The shelf-facing ledge must actually bear under the nominal radiator, not
# merely touch its front face. Sample a thin layer across its bottom surface.
ledge_contact_witness = (cq.Workplane("XY")
                         .box(64, 26, .2, centered=(False, False, False))
                         .translate((158, RAD_Y, RAD_Z - .1)))
assert (radiator_frame_on_shelf(rad_frame, H115I_FRAME_X[0])
        .intersect(ledge_contact_witness).val().Volume() > 100)

render_aio_fan_mount_preview(
    OUT / "aio-fan-aligned-mounts.png",
    radiator_frame_on_shelf(rad_frame, 0).translate((0, -RAD_FRAME_FRONT_Y, 0)),
    kenshin_aio_frame_on_shelf(k_aio_frame, 0).translate((0, -K_AIO_FRAME_REAR_Y, -k_aio.SUPPORT_T)))


# The PSU bracket geometry is shared: hwkit.components.atx_psu_bracket.
PSU_REAR_HOLES_LOCAL_XZ = psu_bracket.PSU_REAR_HOLES_LOCAL_XZ
BERSERK_LED_CENTER = psu_bracket.BERSERK_LED_CENTER
BERSERK_LED_RELIEF_WH = psu_bracket.BERSERK_LED_RELIEF_WH
BERSERK_LED_OUTER_WEB = psu_bracket.BERSERK_LED_OUTER_WEB
assert (psu_bracket.SLOT_LENGTH, psu_bracket.SLOT_WIDTH) == (SHELF_SLOT_LENGTH, SHELF_SLOT_WIDTH)
psu_screw_frame = psu_bracket.bracket


# One bracket serves both PSUs: the 8 mm top bar and LED relief are harmless on
# a unit without a side LED; only the bypass web passes the 86 mm face.
psu_frame=psu_screw_frame(berserk=True)
psu_frame_berserk=psu_frame_kenshin=psu_frame


def psu_frame_on_shelf(print_shape: cq.Workplane, system: str):
    if system == "Berserk":
        return psu_bracket.installed(print_shape, PSU_BERSERK_X, B_PSU_REAR_Y)
    # HX1200i rear face points -X: turn the bracket +90 degrees about Z.
    return (psu_bracket.installed(print_shape, 0, 0).rotate((0, 0, 0), (0, 0, 1), 90)
            .translate((K_PSU_FACE_X, K_PSU_Y, 0)))


def psu_anchor_xy(system: str, x: float, depth: float):
    """Shelf anchor of the shared bracket from its local (x, depth behind face)."""
    if system == "Berserk":
        return PSU_BERSERK_X + x, B_PSU_REAR_Y + depth
    return K_PSU_FACE_X - depth, K_PSU_Y + x


PSU_FRAMES = {"Berserk": psu_frame_berserk, "Kenshin": psu_frame_kenshin}
for system, frame in PSU_FRAMES.items():
    placed_frame = psu_frame_on_shelf(frame, system).val()
    frame_bounds = placed_frame.BoundingBox()
    assert len(frame.solids().vals()) == 1 and frame.val().isValid()
    assert -SIDE_OVERHANG_LIMIT + SIDE_MARGIN <= frame_bounds.xmin and frame_bounds.xmax <= SHELF_W
    for box in parts + connectors:
        assert placed_frame.intersect(box.shape().val()).Volume() < .01, \
            f"{system} PSU frame / {box.name} interference"

gpu_rest = (cq.Workplane("XY").box(50, GPU_REST_D, 24, centered=(False, False, False))
            .cut(cq.Workplane("XY").box(32, 13, 1.5, centered=(False, False, False))
                 .translate((9, 25, 22.5)))
            .cut(shelf_slot_xy(10, GPU_REST_ANCHOR_Y, 24))
            .cut(shelf_slot_xy(40, GPU_REST_ANCHOR_Y, 24)))
for x in (10, 40):
    # Recess a 9 mm OD washer and <=4 mm high M4 head below the card.
    # The elongated recess preserves the shelf slot's adjustment travel.
    gpu_rest = gpu_rest.cut(cq.Workplane("XY").center(x, GPU_REST_ANCHOR_Y)
                           .slot2D(17, 12, 90).extrude(6)
                           .translate((0, 0, 18)))
assert 25 - (GPU_REST_ANCHOR_Y + 17 / 2) >= 4  # land to contact recess
assert GPU_REST_ANCHOR_Y-17/2 >=4  # screw recess to block end
assert 10 - 12 / 2 >= 4  # counterbore to side edge

# Berserk NIC holder: printed as installed, in shelf coordinates.
nic_holder = nic.holder()
for box in parts + connectors + outboard_connectors:
    body = box.shape().cut(nic.riser_holes()) if box.name == "Berserk LRFC6911N riser board" else box.shape()
    assert nic_holder.val().intersect(body.val()).Volume() < .01, ("NIC holder", box.name)
# The card's full-height bracket stands free in front of the holder.
nic_bracket = nic.bracket_envelope()
assert nic_holder.val().intersect(nic_bracket.val()).Volume() < .01, "NIC holder / card bracket"
for box in parts + connectors + outboard_connectors:
    if box.name not in ("Berserk ConnectX-4 Lx card", "QSFP28 DAC Berserk plug"):
        assert nic_bracket.val().intersect(box.shape().val()).Volume() < .01, ("NIC bracket", box.name)
# The holder sits as far toward Kenshin as the RTX 5090 allows (owner, 2026-11-26).
_rtx = next(b for b in parts if b.name == "Kenshin RTX 5090")
_bnic = next(b for b in parts if b.name == "Berserk ConnectX-4 Lx card")
NIC_TO_RTX_GAP = _rtx.y - _bnic.y1
assert nic.CARD_TO_KENSHIN_GPU <= NIC_TO_RTX_GAP <= nic.CARD_TO_KENSHIN_GPU + 1.0, ("NIC card to 5090", NIC_TO_RTX_GAP)


def nominal_board_mounts():
    """ATX 2.01 datums; H12D photo has A/C/F/G/H/K/L/M only."""
    result=[]
    for system,(x0,y0,w,d) in atx_mount.BOARDS.items():
        for i,(site,(u,v)) in enumerate(atx_mount.SITES.items(),1):
            if system == "Berserk" and site not in bp.POPULATED_SITES: continue
            mx,my = x0+25.4*u, y0+d-25.4*v
            if system == 'Kenshin': mx,my = k_xy(mx,my)
            result.append({"system":system,"number":i,"center_x_mm":round(mx,3),
                "center_y_mm":round(my,3),"ATX_site":site,"board_edge_uv_in":[u,v],
                "population":"manufacturer photo; delivered PCB unverified" if system=="Berserk" else "verify PCB; B optional",
                "mount_type":"interlocking shelf frame with recessed screw into female standoff"})
    return result

mounts = nominal_board_mounts()
mount_holes = []


def fan_inlet_cutout(cx, cz, depth):
    """Factory recommended inlet panel opening: 138 square intersect Ø147."""
    return (cq.Workplane("XZ").center(cx, cz).rect(138, 138).extrude(-depth)
            .intersect(cq.Workplane("XZ").center(cx, cz).circle(73.5).extrude(-depth)))


def pressure_fan_shape(box):
    return t_cool.fan()


def mounted_component_shape(box: Box):
    """Side-AIO parts are cut in radiator-local coordinates, then mirrored."""
    local = k_aio_local_boxes.get(box.name)
    if local is None:
        return _mounted_component_shape(box)
    first = len(mount_holes)
    shape = _mounted_component_shape(local)
    for hole in mount_holes[first:]:
        hole["center_mm"] = k_aio_pt(hole["center_mm"])
    return k_aio_shape(shape)


def _mounted_component_shape(box: Box):
    """Cut visible nominal fastener holes in the component reference solids.

    These are alignment marks in a survey envelope, not permission to drill a
    board, PSU, radiator or fan. In particular, radiator marks are shallow.
    """
    shape = box.shape()
    if box.name.endswith("ATX board"):
        system = box.name.split()[0]
        for m in (m for m in mounts if m["system"] == system):
            x, y = m["center_x_mm"], m["center_y_mm"]
            shape = shape.cut(cq.Workplane("XY").center(x, y).circle(1.85)
                              .extrude(BOARD_T + .4).translate((0, 0, BOARD_Z - .2)))
            mount_holes.append({"component": box.name, "interface": "board-to-standoff",
                                "center_mm": [x, y, BOARD_Z], "diameter_mm": 3.7,
                                "verified": False})
    elif box.name == "Berserk H115i radiator":
        for x in H115I_SCREW_X:
            for z in (RAD_Z + 7.75, RAD_Z + 132.25):
                # Blind recesses in this *envelope* show the screw axes on
                # both faces; a through bore would imply drilling the cooler.
                for face, y, direction in (("H115i sandwich factory thread", RAD_Y, -3),
                                ("H115i unused rear factory thread", RAD_Y + RAD_D, 3)):
                    shape = shape.cut(cq.Workplane("XZ").center(x, z)
                                      .circle(2.5).extrude(direction).translate((0, y, 0)))
                    if face == "H115i unused rear factory thread" and x == aio_brace.X0 + aio_brace.SCREW_X:
                        face = "H115i hose brace rear factory thread"
                    mount_holes.append({"component": box.name, "interface": face,
                                        "center_mm": [x, y, z], "diameter_mm": 5,
                                        "blind_depth_mm": 3, "verified": False})
    elif box.name == "Berserk LRFC6911N riser board":
        shape = shape.cut(nic.riser_holes())
        for u, v in nic.HOLES_UV:
            mount_holes.append({"component": box.name, "interface": "riser-to-holder (photo-estimated)" if (u, v) in nic.SCREW_HOLES_UV
                                else "unused: over Kenshin's mount rail",
                                "center_mm": [*nic.riser_xy(u, v), nic.RISER_Z], "diameter_mm": spec.dim(nic.RISER, "hole_diameter"),
                                "verified": False})
    elif box.name == "Kenshin GA II Lite radiator":
        for cx in (91,211,331):
            for x in (cx-52.5,cx+52.5):
                for z in (K_AIO_Z+7.5,K_AIO_Z+112.5):
                    for face,y,direction in (("Kenshin AIO unused inward factory thread",K_AIO_Y,-3),
                                              ("Kenshin AIO rear factory thread",K_AIO_Y + 27,3)):
                        shape = shape.cut(cq.Workplane("XZ").center(x,z).circle(2.25).extrude(direction).translate((0,y,0)))
                        mount_holes.append({"component":box.name,"interface":face,"center_mm":[x,y,z],
                                            "diameter_mm":4.5,"blind_depth_mm":3,"verified":False})
    elif box.name.startswith("Kenshin AIO exhaust fan"):
        for cx in (box.x + 62,):
            shape = shape.cut(cq.Workplane("XZ").center(cx,K_AIO_Z+60).circle(55).extrude(-28).translate((0,box.y,0)))
            for x in (cx-52.5,cx+52.5):
                for z in (K_AIO_Z+7.5,K_AIO_Z+112.5):
                    shape = shape.cut(cq.Workplane("XZ").center(x,z).circle(2.25).extrude(-28).translate((0,box.y,0)))
                    mount_holes.append({"component":box.name,"interface":"Kenshin AIO fan factory clearance",
                                        "center_mm":[x,box.y,z],"diameter_mm":4.5,"verified":False})
    elif "owned Hercules" in box.name or "owned HX1200i" in box.name:
        for local_x, local_z in PSU_REAR_HOLES_LOCAL_XZ:
            z = box.z + local_z
            # Blind reference recess on the PSU's rear face. The real unit
            # has factory threaded inserts; nothing is drilled in its case.
            if box.name == 'Kenshin owned HX1200i PSU':
                x, y = box.x, box.y + local_x  # rear face at low X
                shape = shape.cut(cq.Workplane("YZ").center(y, z).circle(2.5)
                                  .extrude(3).translate((x, 0, 0)))
            else:
                x, y = box.x + local_x, box.y1
                shape = shape.cut(cq.Workplane("XZ").center(x, z).circle(2.5)
                                  .extrude(3).translate((0, y, 0)))
            mount_holes.append({"component": box.name,
                                "interface": "PSU rear factory thread-to-frame",
                                "center_mm": [x, y, z],
                                "diameter_mm": 5, "blind_depth_mm": 3,
                                "verified": False})
    elif box.name == "V100 pressure fan":
        shape=t_cool.fan()
        for x in (-t_cool.PITCH/2,t_cool.PITCH/2):
            for v in (-t_cool.PITCH/2,t_cool.PITCH/2):
                mount_holes.append({"component":box.name,"interface":"pressure fan factory clearance",
                    "center_mm":t_cool.point(x,v,t_cool.PANEL),"axis":[0,t_cool.S,t_cool.S],"diameter_mm":4.5,"verified":False})
    elif box.name == "H115i intake fans":
        pressure = box.name.startswith("V100 pressure fan")
        fan_radius = 70
        if pressure:
            shape = pressure_fan_shape(box)
        half_pitch = COOL_FAN_HOLES / 2 if pressure else 62.25
        fan_centers_x = (190.0, 330.0) if box.name == "H115i intake fans" else (box.x + fan_radius,)
        for cx in fan_centers_x:
            if not pressure:
                shape = shape.cut(cq.Workplane("XZ").center(cx, box.z + fan_radius)
                                  .circle(63).extrude(-box.d).translate((0, box.y, 0)))
            for x in (cx - half_pitch, cx + half_pitch):
                for z in (box.z + fan_radius - half_pitch, box.z + fan_radius + half_pitch):
                    shape = shape.cut(cq.Workplane("XZ").center(x, z)
                                      .circle(2.25).extrude(-box.d)
                                      .translate((0, box.y, 0)))
                    mount_holes.append({"component": box.name,
                                        "interface": "pressure fan factory clearance" if pressure else "fan-to-radiator",
                                        "center_mm": [x, box.y, z], "diameter_mm": 4.5,
                                        "verified": False})
    assert shape.val().isValid(), box.name
    if box.name.endswith("ATX board") or box.name in ("Berserk H115i radiator", "H115i intake fans") or (box.name == "Kenshin GA II Lite radiator" or box.name.startswith("Kenshin AIO exhaust fan")) or "owned Hercules" in box.name or "owned HX1200i" in box.name:
        assert shape.val().Volume() < box.shape().val().Volume() - .1, box.name
    return shape


assembly = cq.Assembly(name="Kenshin_Berserk_Hammond_sliding_shelf")
colors = [(0.18, .43, .73), (.15, .6, .75), (.25, .7, .32), (.96, .73, .15),
          (.5, .4, .65), (.72, .35, .3), (.82, .35, .3), (.83, .61, .23),
          (.9, .7, .3)]
fan_shapes = {}
for i, box in enumerate(parts):
    shape = mounted_component_shape(box)
    if box.name.startswith("Kenshin AIO exhaust fan") or box.name == "H115i intake fans": fan_shapes[box.name] = shape
    assembly.add(shape, name=box.name.replace(" ", "_"),
                 color=cq.Color(*colors[i % len(colors)]))
for box in connectors:
    assembly.add(box.shape(), name=box.name.replace(" ", "_"),
                 color=cq.Color(.96, .55, .1))

# Broad shelf-mounted rear-array hood with an integral45-degree outlet.
v100_plenum,screw_fit_sample,post_slots=t_cool.parts()
inlet_y=t_cool.INLET_Y
plenum_post_slots=[{"post_xy_mm":p,"slot_width_mm":8,"radial_clearance_mm":1} for p in post_slots]
cooling_solids=[("V100 GPU shroud",v100_plenum)]
for name,solid in cooling_solids:
    for box in parts+connectors:
        assert solid.val().intersect(box.shape().val()).Volume()<.01,(name,box.name)
    assembly.add(solid,name=name.replace(" ","_"),color=cq.Color(.23,.78,.77))
printed_cooling=t_cool.print_parts()
well_print=printed_cooling["v100_gpu_shroud"]
cooling_hardware,cooling_fasteners=t_cool.hardware()
for name,shape in cooling_hardware.items():
    if 'driver' in name:continue
    assembly.add(shape,name="V100_"+name,color=cq.Color(.65,.65,.68))
fan_holes=[r["center_mm"] for r in cooling_fasteners]
plenum_joint_checks=[]  # Integral fan panel; no separate base or joining screws.
# Three internal shelf bolts carry the hood. Fan/duct are fitted afterwards.
for x,y in t_cool.ANCHORS:
    bolt=(cq.Workplane('XY').center(x,y).circle(2).extrude(16).translate((0,0,-9))
          .union(cq.Workplane('XY').center(x,y).circle(6).circle(2.75).extrude(1).translate((0,0,6)))
          .union(cq.Workplane('XY').center(x,y).circle(4).extrude(4).translate((0,0,7)))
          .union(cq.Workplane('XY').center(x,y).circle(6).circle(2.75).extrude(1).translate((0,0,-SHELF_T-1)))
          .union(cq.Workplane('XY').center(x,y).polygon(6,8.08).circle(2).extrude(3.2).translate((0,0,-SHELF_T-4.2))))
    assert bolt.val().intersect(v100_plenum.val()).Volume()<.01
    assembly.add(bolt,name=f'V100_hood_shelf_M4_{x}_{y}',color=cq.Color(.65,.65,.68))
    for dy in (-1.25,0,1.25):
        driver=cq.Workplane('XY').center(x,y+dy).circle(3).extrude(210).translate((0,0,11))
        assert driver.val().intersect(v100_plenum.val()).Volume()<.01,(x,y,dy,'long driver through bare fan opening')
metal_shelf_holes = []  # only purchased GPU tail spacers use these anchors
for slot, x in V100_SLOTS.items():
    px, py = x + 20, V100_FRONT_Y + 10
    pedestal = (cq.Workplane("XY").center(px, py).polygon(6, 7 / (3 ** .5) * 2).circle(2).extrude(20))
    pad = cq.Workplane("XY").box(18, 18, 4, centered=(False, False, False)).translate((px - 9, py - 9, 20))
    assembly.add(pedestal, name=f"{slot}_metal_tail_support_survey", color=cq.Color(.6, .6, .63))
    assembly.add(pad, name=f"{slot}_silicone_contact_pad_survey", color=cq.Color(.3, .3, .32))
    metal_shelf_holes.append({"part": f"{slot}-metal-tail-support", "center_xy_mm": [px, py],
        "diameter_mm": 5.0, "fastener": "M4 from below with steel washer into stock M4 female/female 20 mm spacer; 4 mm silicone contact pad",
        "contact_surface_z_mm": 24, "verified": False})
    mount_holes.append({"component": f"V100 {slot} tail support", "interface": "surveyed bearing contact, no GPU drilling",
        "center_mm": [px, py, 24], "verified": False})
for center in fan_holes:
    mount_holes.append({"component": "V100 integral fan panel", "interface": "fan inlet-flange through-bolt clearance",
                        "center_mm": center, "axis": [0,t_cool.S,t_cool.S], "diameter_mm": COOL_FAN_CLEARANCE_D, "verified": False})

# Metal bases pass through the adapter and bear directly on steel. The
# manufacturer's base drawing and owner-reported OBT thread are distinct
# from the unmeasured rod body / fixed GPU seating-nut height.
PCIE_POST_SURVEY_H, PCIE_POST_SURVEY_D = 141.0, 6.0
GPU_BACKER_T = post_hw.BACKER_T
post_thread_stack = post_hw.thread_stack(SHELF_T)
gpu_post_holes = []
gpu_backer_boxes = []
gpu_post_base_keepouts = []
through_post_access = []
# Stock M4 DIN9021 washer under a smaller M3 washer: no cut/drilled bar.
gpu_backer = cq.Workplane("XY").center(6, 6).circle(6).circle(2.2).extrude(GPU_BACKER_T)
cq.exporters.export(gpu_backer, str(OUT / "pcie-post-backing-washer-reference.step"))
post_locations = []
gpu_flange_holes = []
for system, label, points in (
    *(("Berserk", slot, tuple((x, V100_TAIL_Y + 6) for x in bp.BRACKET_POST_X[slot])) for slot in V100_SLOTS),
    # Kenshin's pair is turned with the board: same X, two Y positions.
    ("Kenshin", "RTX5090", tuple(k_xy(x, shelf_y(679+K_REAR_SHIFT)) for x in (53-K_LEFT_SHIFT, 73-K_LEFT_SHIFT))),
):
    post_h = PCIE_POST_SURVEY_H
    for i, (px, py) in enumerate(points, 1):
        shared = atx_mount.is_shared_post(system,px,py)
        base_z = 0.
        screw_length = post_hw.BOTTOM_SCREW_LENGTH
        rod_top = post_h - 10 + post_hw.BASE_HEIGHT  # Survey rod envelope only; fixed nut height unmeasured.
        adapter_name = f"{system.lower()}_mobo_adapter_{atx_mount.LABELS[system]['front']}_drill_plan" if shared else None
        bx, by = px - 6, py - 6
        gpu_backer_boxes.append(Box(f"{system} {label} purchased post backing washer {i}", bx, by,
            -SHELF_T - GPU_BACKER_T, 12, 12, GPU_BACKER_T,
            "stock Two M4 DIN9021 OD12/ID4.4/T1 washers plus two OD7x0.5 M3 washers beneath; no machining"))
        assembly.add(gpu_backer.translate((bx, by, -SHELF_T - GPU_BACKER_T)),
                     name=f"{system}_{label}_stock_backing_washer_{i}", color=cq.Color(.5, .5, .55))
        gpu_post_holes.append({"part": f"{system}_{label}_metal_post_{i}",
                               "center_xy_mm": [px, py], "diameter_mm": 3.5,
                               "fastener": "M3x8 from below through two OD7x0.5 and two OD12x1 washers and steel into Wurth970140324 14mm M3 female/female base; base passes freely through plastic",
                               "clearance_through_adapter": adapter_name,
                               "printed_bracket_slot_mm": [atx_mount.POST_SLOT_LENGTH,atx_mount.POST_SLOT_WIDTH] if shared else None,
                               "printed_base_opening": post_hw.opening_spec() if shared else None,
                               "verified": False})
        gpu_post_base_keepouts.append(PostBaseEnvelope(f"{system} {label} metal post base {i}",
                                          px - post_hw.BASE_AF/3**.5, py - post_hw.BASE_AF/3**.5, base_z,
                                          2*post_hw.BASE_AF/3**.5, 2*post_hw.BASE_AF/3**.5, post_hw.BASE_HEIGHT,
                                          "clocked hex, corner toward PCB; metal base seats on steel"))
        post_locations.append({"system": system, "card": label, "post": i,
                               "x_mm": px, "y_mm": py,
                               "top_z_survey_mm": rod_top,"GPU_flange_z_survey_mm":post_h,
                               "base_z_mm":base_z,"clearance_adapter":adapter_name,
                               "rod_length_survey_mm":PCIE_POST_SURVEY_H-10,
                               "height_note":"131mm rod envelope retained, not measured. Rod seat Z14 is2.5mm below old Z16.5, and1.525mm below PCB underside. OBT lower seating nut is fixed: verify flange meets it with card fully seated; do not pull card to fit."})
        standoff = (cq.Workplane("XY").polygon(6, post_hw.BASE_AF / (3 ** .5) * 2).extrude(post_hw.BASE_HEIGHT)
                    .rotate((0,0,0),(0,0,1),hex_rotation(system)).translate((px,py,0)))
        standoff = standoff.cut(cq.Workplane("XY").center(px, py).circle(1.5).extrude(post_hw.BASE_HEIGHT))
        assembly.add(standoff.translate((0,0,base_z)), name=f"{system}_{label}_M3_SW5p5_14mm_standoff_{i}",
                     color=cq.Color(.8, .7, .4))
        assembly.add(cq.Workplane("XY").center(px, py)
                     .circle(PCIE_POST_SURVEY_D / 2).extrude(post_h - 10)
                     .translate((0, 0, post_hw.BASE_HEIGHT+base_z)),
                     name=f"{system}_{label}_metal_OBT_PCIe_post_{i}_survey",
                     color=cq.Color(.62, .62, .64))
        # M3x8 through doubled stock washers and nominal 16-gauge shelf
        # gives 3.48 mm nominal engagement; check the opposing OBT end thread.
        shaft = cq.Workplane("XY").center(px, py).circle(1.5).extrude(screw_length).translate((0, 0, -SHELF_T-GPU_BACKER_T-post_hw.SMALL_WASHER_T))
        washer = cq.Workplane("XY").center(px, py).circle(3.5).circle(1.6).extrude(post_hw.SMALL_WASHER_T).translate((0, 0, -SHELF_T-GPU_BACKER_T-post_hw.SMALL_WASHER_T))
        head = cq.Workplane("XY").center(px, py).circle(2.75).extrude(3).translate((0, 0, -SHELF_T-GPU_BACKER_T-post_hw.SMALL_WASHER_T-3))
        assembly.add(shaft.union(head).union(washer),
                     name=f"{system}_{label}_M3x{screw_length}_and_washer_{i}_survey", color=cq.Color(.65, .65, .68))
        # Show the actual reported male tip and the remaining axial gap.
        assembly.add(cq.Workplane("XY").center(px,py).circle(1.5)
                     .extrude(post_hw.OBT_STUD_LENGTH)
                     .translate((0,0,post_hw.BASE_HEIGHT-post_hw.OBT_STUD_LENGTH)),
                     name=f"{system}_{label}_OBT_9mm_stud_{i}",color=cq.Color(.62,.62,.64))
        if shared:
            through_post_access.append({"part":adapter_name,"center_xy_mm":[px,py],
                **post_thread_stack, "adapter_thickness_mm":6,
                "printed_base_opening":post_hw.opening_spec(),
                "base_seats_on":"steel shelf at Z0; plastic is clearance only",
                "under_shelf_washers_mm":[[12,4.4,1],[12,4.4,1],[7,3.2,.5],[7,3.2,.5]],
                "thread_fit_verified":False,
                "access":"bottom screwdriver and SW5.5 open wrench above adapter; point one hex corner toward PCB. Hold base with wrench when tightening either end, not plastic. Assemble before GPUs. Fixed lower OBT nut height must match fully seated card.",
                "drill_use":"locate base with fully seated card; mark and drill steel3.5mm on sound steel. Enlarged plastic slot is clearance, not a drill bushing."})
        if label != "NIC-carrier":
            gpu_flange_holes.append({"component": f"{system} {label} flange survey",
                                     "interface": "card flange-to-metal post",
                                     "center_mm": [px, py, post_h],
                                     "diameter_mm": 6.5, "verified": False})
    # A deliberately separate survey flange shows the hole axes over the two
    # support posts. It is not a claim about the real card's bracket shape.
    fx0, fy0 = min(p[0] for p in points) - 8, min(p[1] for p in points) - 8
    flange = (cq.Workplane("XY").box(max(p[0] for p in points) + 8 - fx0,
                                    max(p[1] for p in points) + 8 - fy0, 3,
                                    centered=(False, False, False))
              .translate((fx0, fy0, post_h)))
    for px, py in points:
        flange = flange.cut(cq.Workplane("XY").center(px, py)
                             .circle(3.25).extrude(3)
                             .translate((0, 0, post_h)))
    if label != "NIC-carrier":
        assembly.add(flange, name=f"{system}_{label}_GPU_flange_hole_pattern_survey",
                     color=cq.Color(.8, .8, .83))
# Check rear support posts against the shortened extraction duct and feet.
for post in post_locations:
    post_shape=cq.Workplane("XY").center(post["x_mm"],post["y_mm"]).circle(3).extrude(post["top_z_survey_mm"])
    for name,other in cooling_solids:
        assert other.val().intersect(post_shape.val()).Volume()<.01, ("post/cooling collision",post,name)

for m in mounts:
    if m["system"] == "Kenshin" and m["ATX_site"] == "B":
        continue  # optional legacy site: never model a post against unsurveyed PCB
    x, y = m["center_x_mm"], m["center_y_mm"]
    assembly.add(cq.Workplane("XY").center(x, y).circle(3).extrude(STANDOFF_H)
                 .translate((0, 0, RAIL_T)),
                 name=f"{m['system']}_nominal_6_32_standoff_{m['number']}",
                 color=cq.Color(.85, .82, .7))

adapter_parts = []
installed_adapter_shapes = {}
bridge_boxes = []
adapter_web_boxes = []
adapter_seams = []
adapter_support_patterns = []
optional_mobo_shelf_anchors = []
rear_io_service_keepouts = [atx_mount.io_keepout(system) for system in ("Berserk","Kenshin")]
for reserve in rear_io_service_keepouts:
    x0,x1=reserve["x_range_mm"];y0,y1=reserve["y_range_mm"];z0,z1=reserve["z_range_mm"]
    assembly.add(Box("rear I/O service reserve",x0,y0,z0,x1-x0,y1-y0,z1-z0, reserve["basis"]).shape(),
                 name=reserve["system"]+"_rear_IO_no_ear_service_reserve",color=cq.Color(.8,.3,.25,.12))


def largest_triangle(points):
    return max(abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
               for a,b,c in combinations(points,3))


for system in ("Berserk", "Kenshin"):
    frames,joints=atx_mount.build(system)
    adapter_seams.extend({"system":system,**j} for j in joints)
    for label,frame in frames.items():
        shape=frame["shape"]
        bb=shape.val().BoundingBox()
        assert 0<=bb.xmin and bb.xmax<=SHELF_W and 0<=bb.ymin and bb.ymax<=SHELF_D
        for obstruction in parts+connectors+gpu_post_base_keepouts:
            assert shape.val().intersect(obstruction.shape().val()).Volume()<.01,(label,obstruction.name)
        group_mounts=[m for m in mounts if m["system"]==system and m["ATX_site"] in frame["sites"]]
        for m in group_mounts:
            hx,hy=frame["hole_centers"][m["ATX_site"]]
            assert abs(hx-m["center_x_mm"])<1e-5 and abs(hy-m["center_y_mm"])<1e-5,(label,m)
            m["adapter_part"]=label
        required=[m for m in group_mounts if not (system=="Kenshin" and m["ATX_site"]=="B")]
        triangle=largest_triangle([(m["center_x_mm"],m["center_y_mm"]) for m in required])
        assert len(required)>=4 and triangle>1000
        for sx,sy in frame["post_slots"]:
            # User-requested regular hex removes adjustment travel. Verify
            # the complete face allowance at its fixed axis and orientation,
            # independently of the polyline used to cut the opening.
            witness=(cq.Workplane("XY").polygon(6,(post_hw.BASE_AF+2*post_hw.BODY_FACE_CLEARANCE)/3**.5*2)
                     .extrude(6).rotate((0,0,0),(0,0,1),hex_rotation(system))
                     .translate((sx,sy,0)).val())
            assert shape.val().intersect(witness).Volume()<.01,(label,"snug hex face clearance",sx,sy)
        for x,y in frame["standalone_anchors"]:
            add_shelf_hole(label,x,y,8,frame["shelf_slot_mm"][1],frame["shelf_fastener"],frame["shelf_hole_diameter_mm"])
            shelf_attachment_holes[-1]["install_before_PCB"] = frame["install_anchors_before_PCB"]
        adapter_support_patterns.append({"part":label,"required_ATX_sites":[m["ATX_site"] for m in required],
            "optional_ATX_sites":["B"] if system=="Kenshin" and "B" in frame["sites"] else [],
            "required_motherboard_screw_count":len(required),"largest_motherboard_triangle_area_mm2":round(triangle,3),
            "shelf_anchor_count":len(frame["anchors"]),"shelf_anchor_centers_mm":frame["anchors"],
            "through_post_centers_mm":frame["through_post_centers"],"common_post_slot_centers_mm":frame["post_slots"],
            "post_slot_mm":frame["post_slot_mm"],"interchangeable_with":frame["interchangeable_with"],"shelf_anchor_end":frame["anchor_end"],
            "post_opening":frame["post_opening"],
            "optional_shelf_anchor_centers_mm":frame["optional_anchors"],
            "optional_anchor_access":"under PCB; secure before motherboard; optional hardware omitted from required BOM/drill count",
            "shelf_slot_mm":frame["shelf_slot_mm"],
            "checked_Y_adjustment_mm":[-2,2],
            "adjustment_datum":"printed slot center, not active post center",
            "shelf_fastener":frame["shelf_fastener"],"top_washer_OD_mm":frame["top_washer_od_mm"],
            "backing_washer_OD_mm":frame["backing_washer_od_mm"],
            "bar_width_mm":frame["bar_width_mm"],"ear_width_mm":frame["ear_width_mm"],
            "rear_rail_depth_mm":frame["rear_rail_depth_mm"],"post_slots_are_selectable":True,
            "gpu_tab_relief":frame["gpu_tab_relief"],
            "installed_origin_xy_mm":frame["origin"],"bounds_xy_mm":frame["bounds"],
            "independent_shelf_fasteners":True,"anchors_before_PCB":frame["install_anchors_before_PCB"],"joint_role":"three full-depth drop-in dovetails, including perpendicular C-H key; shelf and board retain Z"})
        for x,y in frame["optional_anchors"]:
            optional_mobo_shelf_anchors.append({"part":label,"center_xy_mm":[x,y],"printed_bracket_slot_mm":[8,4],
                "optional":True,"steel_hole_diameter_mm":3.5,"fastener":"M3 with OD7x0.5 top/back steel washers and nut; solid steel only; install before PCB",
                "washer_and_head_top_z_mm":9.5,"PCB_bottom_z_mm":RAIL_T+STANDOFF_H,"verified":False})
        adapter_parts.append((label,frame["print_shape"],frame["origin"]))
        installed_adapter_shapes[label]=shape
        adapter_web_boxes.append(Box(label+" envelope",bb.xmin,bb.ymin,0,bb.xlen,bb.ylen,RAIL_T,"bounding envelope only; interlocking open frame"))
        assembly.add(shape,name=label,color=cq.Color(.23,.78,.77))
    all_anchors=[a for frame in frames.values() for a in frame["anchors"]]
    assert largest_triangle(all_anchors)>8000

# The entire hex envelope must pass through plastic, leaving no clamp contact.
for joint in through_post_access:
    x,y=joint["center_xy_mm"]; shape=installed_adapter_shapes[joint["part"]].val()
    body=(cq.Workplane("XY").polygon(6,(post_hw.BASE_AF+2*post_hw.BODY_FACE_CLEARANCE)/3**.5*2)
          .extrude(RAIL_T).rotate((0,0,0),(0,0,1),hex_rotation(joint["part"])).translate((x,y,0)).val())
    assert shape.intersect(body).Volume()<.01,(joint,"through-base clearance")
assert len(through_post_access)==10
# Geometric equivalence is checked after normalization, not inferred from ATX naming.
for left,right in (("berserk_mobo_adapter_left_drill_plan","kenshin_mobo_adapter_right_drill_plan"),):
    pair=[next(sh for name,sh,_ in adapter_parts if name==n).val() for n in (left,right)]
    assert pair[0].cut(pair[1]).Volume()<.01 and pair[1].cut(pair[0]).Volume()<.01

# One model file per unique printed geometry. Installed copies that are
# geometrically identical (checked above) share a model; quantities cover both PCs.
INSTALLED_MODELS = {
    "berserk_mobo_adapter_left_drill_plan": "atx_mobo_adapter_front",
    "kenshin_mobo_adapter_right_drill_plan": "atx_mobo_adapter_front",
    "kenshin_mobo_adapter_left_drill_plan": "atx_mobo_adapter_rail",
    "berserk_mobo_adapter_right_drill_plan": "h12d_mobo_adapter_rail",
    "psu_screw_frame_berserk_drill_plan": "psu_bracket",
    "psu_screw_frame_kenshin_drill_plan": "psu_bracket",
}
MOBO_PURPOSE = {
    "atx_mobo_adapter_front": "shelf-front motherboard section, common to every ATX board here: two M3 front ears, three optional inner slots, 25mm rails and three drop-in XY keys",
    "atx_mobo_adapter_rail": "standard ATX rear-rail section: eight regular hex6.0mm-AF holes at PCB rear+10mm,0.25mm face clearance, corner toward PCB; three independent M3 anchors and provisional2x2mm GPU-tab groove; original recesses-up print orientation without supports",
    "h12d_mobo_adapter_rail": "H12D-8D rear-rail section: eight regular hex6.0mm-AF holes at PCB rear+6mm,0.25mm face clearance, corner toward PCB; three independent M3 anchors and provisional2x2mm GPU-tab groove; original recesses-up print orientation without supports",
}
mobo_models = {}
for label, shape, _ in adapter_parts:
    mobo_models.setdefault(INSTALLED_MODELS[label], [shape, 0])[1] += 1

print_manifest = [
    *(export_print(name, shape, 1, "GPU exhaust to provisional inner ceiling; see gpu-exhaust-report.json for interfaces and print orientation")
      for name, shape in gpu_exhaust.print_parts().items()),
    *(export_print(name, shape, count, MOBO_PURPOSE[name])
      for name, (shape, count) in mobo_models.items()),
    export_print("psu_bracket", psu_frame, 2,
                 "compact HT-PLA-GF rear PSU bracket for any 86x150mm ATX PSU face: 8mm top bar, 9x40mm LED relief, 30mm foot, two upper screws and side-by-side shelf slots"),
    export_print("fan140_aio_frame", rad_frame, 2,
                 "140mm fan-flush radiator frame; 124.5mm pitch, 7x4.5mm slots, bearing ledge and two slotted shelf anchors"),
    export_print("fan140_aio_hose_brace", aio_brace_print, 1,
                 "140mm radiator hose-end brace: two rear factory radiator screws, broad triangular 8 mm web and two slotted shelf anchors; print on full side web"),
    export_print("gpu_rest", gpu_rest, 1,
                 "secondary GPU rest; recessed M4 heads and 9 mm washers; shim after card measurement"),
    export_print("fan120_aio_frame", k_aio_frame, 2,
                 f"120mm fan-flush radiator frame; 105mm pitch, 7x4.5mm slots, {k_aio.REACH:g}mm foot inside the radiator footprint, bearing ledge and two slotted anchors; rear face down"),
    export_print(nic.PART, nic_holder.translate((-nic.BASE[0], -nic.BASE[2], 0)), 1,
                 "Berserk NIC riser holder: flat 6mm base plate, four slotted M4 anchors, four 8mm riser bosses and a slot deflection stop clearing the SATA socket; within 15mm of the board; base on bed"),
    export_print("fan120_aio_center_spacer", k_aio_spacer, 1,
                 "plain 119x119x6 middle fan spacer for a 360mm radiator; keeps three fans coplanar; four clearance holes, no captive nuts"),
    export_print("v100_gpu_shroud", well_print, 1,
                 "single broad rear-array hood;6mm beveled shelf base and three internalM4 slots;flush exterior and four permanent4mm chamber ribs;integral45-degree fan panel;HT-PLA-GF;fan face down without removable supports"),
    export_print("tnut_fit_coupon", screw_fit_sample, 1,
                 "non-installed24x22x10mm HT-PLA-GF coupon: rectangular M4 T-nut pocket"),

]

# Printed bracket positions and exact PSU rear faces remain a fit survey.
for label, frame in PSU_FRAMES.items():
    assembly.add(psu_frame_on_shelf(frame, label),
                 name=f"printed_{label}_PSU_two_upper_screw_frame_survey",
                 color=cq.Color(.68, .58, .77))
for label, x, y in (("Kenshin", GPU_REST_X, GPU_REST_Y),):  # local, turned with the board
    assembly.add(k_shape(gpu_rest.translate((x, y, 0))), name=f"printed_{label}_GPU_rest_survey",
                 color=cq.Color(.23, .78, .77))
assembly.add(nic_holder, name="printed_Berserk_NIC_riser_holder", color=cq.Color(.86,.36,.62))
for box in outboard_connectors:
    assembly.add(box.shape(), name=box.name.replace(" ", "_"), color=cq.Color(.96, .55, .1))
for x, side in zip(H115I_FRAME_X, ("left", "right")):
    assembly.add(radiator_frame_on_shelf(rad_frame, x),
                 name=f"printed_H115i_{side}_screw_frame_drill_plan_survey",
                 color=cq.Color(.44, .72, .73))
k_aio_foot_boxes = []
assembly.add(aio_brace_installed, name="Berserk_H115i_hose_end_shelf_brace",
             color=cq.Color(.20,.62,.67))
assembly.add(k_aio_spacer_installed, name="Kenshin_AIO_middle_fan_6mm_spacer",color=cq.Color(.44,.72,.73))
for index, fan_x in enumerate(K_AIO_FRAME_X, 1):
    assembly.add(k_aio_frame_installed(fan_x),
                 name=f"printed_Kenshin_AIO_{index}_bearing_frame_drill_plan_survey",
                 color=cq.Color(.44, .72, .73))
    foot_box = k_aio_box(Box("Kenshin AIO frame central foot", fan_x + K_AIO_FOOT_X, K_AIO_FRAME_REAR_Y - K_AIO_REACH,
                   k_aio.SUPPORT_T, K_AIO_FOOT_W, K_AIO_REACH, 6,
                   "two M4 slotted shelf anchors; foot bears on the deck"))
    assert foot_box.x >= 0 and foot_box.x1 <= SHELF_W and foot_box.y >= 0 and foot_box.y1 <= SHELF_D
    for bridge in bridge_boxes:
        assert not overlap(foot_box, bridge), f"fan tongue / board bridge: {bridge.name}"
    for obstruction in gpu_post_base_keepouts:
        assert not overlap(foot_box, obstruction), f"fan tongue / GPU post foot: {obstruction.name}"
    k_aio_foot_boxes.append(foot_box)
placed_prints = list(installed_adapter_shapes.items())
placed_prints += [
    ("Berserk PSU frame", psu_frame_on_shelf(psu_frame_berserk, "Berserk")),
    ("Kenshin PSU frame", psu_frame_on_shelf(psu_frame_kenshin, "Kenshin")),
    ("H115i left screw frame", radiator_frame_on_shelf(rad_frame, H115I_FRAME_X[0])),
    ("H115i right screw frame", radiator_frame_on_shelf(rad_frame, H115I_FRAME_X[1])),
    ("H115i hose brace", aio_brace_installed),
    ("5090 rest", k_shape(gpu_rest.translate((GPU_REST_X, GPU_REST_Y, 0)))),
    ("Berserk NIC holder", nic_holder),
    ("front Kenshin AIO frame", k_aio_frame_installed(K_AIO_FRAME_X[0])),
    ("rear Kenshin AIO frame", k_aio_frame_installed(K_AIO_FRAME_X[1])),
    ("Kenshin AIO center spacer", k_aio_spacer_installed),
    *cooling_solids,
]

for i, (name, solid) in enumerate(placed_prints):
    a = solid.val().BoundingBox()
    for other_name, other in placed_prints[i + 1:]:
        b = other.val().BoundingBox()
        if a.xmin < b.xmax and a.xmax > b.xmin and a.ymin < b.ymax and a.ymax > b.ymin and a.zmin < b.zmax and a.zmax > b.zmin:
            assert solid.val().intersect(other.val()).Volume() < 0.01, f"printed part collision: {name} / {other_name}"

ki=atx_mount.io_keepout("Kenshin")
kx0,kx1=ki["x_range_mm"]; ky0,ky1=ki["y_range_mm"]; kz0,kz1=ki["z_range_mm"]
k_io_reserve=Box("Kenshin rear I/O service reserve",kx0,ky0,kz0,kx1-kx0,ky1-ky0,kz1-kz0,"40mm port approach; exact ports unmeasured")
assert v100_plenum.val().intersect(k_io_reserve.shape().val()).Volume()<.01,"Kenshin ports need clear approach past V100 hood"

cable_routes = {
    **{f"Kenshin AIO hose {i+1}": {"od_mm": 14,
        "available_length_mm": 400,
        "points_mm": [(*k_aio_xy(20, K_AIO_Y), 80+i*15), (80, k_aio_xy(20, 0)[1]+12, 80+i*15),
                      (270+i*16, 480, 80)],
        "note": "Provisional 400 mm hose route from the front radiator tank, past the radiator's inner face in front of Berserk's NIC holder, to the pump; dry-fit ports, broad arcs and minimum bend radius. Polyline length is a lower bound."}
       for i in range(2)},
    "Berserk AC": {"od_mm": 9.14, "points_mm": [(PSU_BERSERK_X+43,B_PSU_REAR_Y+60,123.5),(75,320,205),
                                                   (75,SHELF_D+80,205)],
        "note":"Rises over the side-AIO hose end and runs rearward above the radiator's inner side and the 5090 tail; provisional lane. Disconnect external cord before sliding shelf."},
    "Kenshin AC": {"od_mm": 9.14, "points_mm": [(K_PSU_FACE_X-30,K_PSU_Y+39.5,118),(K_PSU_FACE_X-30,SHELF_D+80,118)],
        "note":"Left-facing PSU inlet beside the radiator's rear frame; the cord leaves straight out of the rack rear. Disconnect external cord before sliding shelf."},
    "Berserk Ethernet": {"od_mm": 6, "points_mm": [(295,V100_TAIL_Y+27,50),(295,V100_TAIL_Y+27,160),
                                                     (SHELF_W+12,V100_TAIL_Y+27,160),(SHELF_W+12,SHELF_D+80,160)],
        "note":"Rises at the RJ45 boot above Kenshin's side-facing I/O and card brackets, then runs rearward in the right-edge lane."},
    **{f"V100 {slot} power": {"od_mm": 10,
        "points_mm": [(x+32,V100_FRONT_Y-12,105),(x+32,V100_FRONT_Y-12,210),
                      (111-index*12,V100_FRONT_Y-12,210),(70-index*12,5,210),(70-index*12,5,110)],
        "note": "Candidate low-profile CPU/EPS tails above the front radiator to the PSU; measure connector bulk, pinout and bend radius."}
       for index,(slot,x) in enumerate(V100_SLOTS.items())},
    "QSFP28 DAC": {"od_mm": spec.dim(nic.DAC, "cable_od"),
        "points_mm": nic.dac_route(next(b for b in connectors if b.name == "QSFP28 DAC Berserk plug"), outboard_connectors[0]),
        "note": "Berserk plug end, under the AIO hose, up behind the V100 hood and over Kenshin's 24-pin, rearward in the right-edge lane above the I/O reserve, then out past the deck edge and back into Kenshin's cage. Corners stand for bends of at least the allowance radius; the loop at Kenshin's end is outside the rack opening."},
    "Berserk SFF-8643 cable": {"od_mm": spec.dim(nic.SFF, "cable_od"),
        "points_mm": nic.sff_route(next(b for b in connectors if b.name == "Berserk SFF-8643 riser plug"),
                                   next(b for b in connectors if b.name == "Berserk SFF-8643 H12D plug")),
        "note": "Riser plug end, up over Kenshin's motherboard mount beside the PCB edge, forward to the left of the V100 hood, across the deck front under the V100 tails' front ends to the H12D port. Provisional; the port position is photo-estimated."},
}
cable_clearance_checks = []
planned_upgrade_cable_conflicts = []
for label, route in cable_routes.items():
    points = route["points_mm"]
    route["polyline_length_mm"] = round(sum((cq.Vector(*b)-cq.Vector(*a)).Length
        for a,b in zip(points,points[1:])),2)
    if label.startswith("Kenshin AIO hose"):
        assert route["polyline_length_mm"] < route["available_length_mm"] - 40, label
    radius = route["od_mm"] / 2
    for i, (start, end) in enumerate(zip(points, points[1:]), 1):
        delta = cq.Vector(*end) - cq.Vector(*start)
        segment = cq.Solid.makeCylinder(radius, delta.Length, cq.Vector(*start),
                                        delta.normalized())
        terminal_names = {
            "Berserk AC": {"Berserk AC plug + tail", "Berserk owned Hercules 1600W PSU"},
            "Kenshin AC": {"Kenshin low-profile C13 plug + bend", "Kenshin owned HX1200i PSU"},
            "Berserk Ethernet": {"Berserk Ethernet RJ45 boot + bend"},
            "QSFP28 DAC": {"QSFP28 DAC Berserk plug"},
            "Berserk SFF-8643 cable": {"Berserk SFF-8643 riser plug", "Berserk SFF-8643 H12D plug"},
        }.get(label, set())
        if label.startswith("V100 "):
            slot = label.split()[1]
            terminal_names = {f"V100 {slot} angled EPS plug target", "Berserk owned Hercules 1600W PSU"}
        if label.startswith("Kenshin AIO hose"):
            terminal_names = {"Kenshin GA II Lite pump", "Kenshin GA II Lite radiator"}
        segment_conflicts = []
        for box in parts + connectors:
            if box.name in terminal_names:
                continue
            intersection_volume = segment.intersect(box.shape().val()).Volume()
            if intersection_volume >= .01:
                if label.startswith("V100 ") and box.name == "Berserk H115i radiator":
                    conflict = {"route":label,"segment":i,"component":box.name,
                                "intersection_volume_mm3":round(intersection_volume,3),
                                "status":"unresolved planned power route; not physically fitted"}
                    planned_upgrade_cable_conflicts.append(conflict)
                    segment_conflicts.append(conflict)
                else:
                    raise AssertionError((label,i,box.name))
        for metal_label, metal in cooling_solids:
            assert segment.intersect(metal.val()).Volume() < .01, (label, i, metal_label)
        assert segment.intersect(aio_brace_installed.val()).Volume() < .01, (label, i, "H115i hose brace")
        for x0 in K_AIO_FRAME_X:
            assert segment.intersect(k_aio_frame_installed(x0).val()).Volume() < .01, (label,i,"side AIO frame")
        if label in ("QSFP28 DAC", "Berserk SFF-8643 cable"):
            # The NIC cables also clear the printed holder, the GPU support
            # rods, the outboard Kenshin plug and the other cable routes.
            assert segment.intersect(nic_holder.val()).Volume() < .01, (label, i, "NIC holder")
            assert segment.intersect(nic_bracket.val()).Volume() < .01, (label, i, "NIC card bracket")
            for post in post_locations:
                rod = cq.Workplane("XY").center(post["x_mm"],post["y_mm"]).circle(3).extrude(post["top_z_survey_mm"])
                assert segment.intersect(rod.val()).Volume() < .01, (label, i, post["card"], post["post"])
            if label == "Berserk SFF-8643 cable":
                assert segment.intersect(outboard_connectors[0].shape().val()).Volume() < .01, (label, i)
            for other, other_route in cable_routes.items():
                if other == label:
                    continue
                pts = other_route["points_mm"]
                for a, b in zip(pts, pts[1:]):
                    dv = cq.Vector(*b) - cq.Vector(*a)
                    tube = cq.Solid.makeCylinder(other_route["od_mm"]/2, dv.Length, cq.Vector(*a), dv.normalized())
                    assert segment.intersect(tube).Volume() < .01, (label, i, other)
        cable_clearance_checks.append({"route": label, "segment": i, "nominal_component_collision": bool(segment_conflicts), "unresolved_conflicts": segment_conflicts})
        assembly.add(segment, name=f"{label.replace(' ', '_')}_survey_segment_{i}",
                     color=cq.Color(.95, .55, .18))
# Network: plug and cable lengths for the direct Berserk-Kenshin link.
for box in outboard_connectors:
    for other in parts + connectors:
        assert not overlap(box, other), (box.name, other.name)
_kplug = outboard_connectors[0]
_dac = cable_routes["QSFP28 DAC"]
_dac_plugs = 2 * spec.dim(nic.DAC, "plug_length_outside")
_dac_needed = _dac["polyline_length_mm"] + _dac_plugs
_dac_reach = max(p[0] for p in _dac["points_mm"]) + _dac["od_mm"]/2
_sff = cable_routes["Berserk SFF-8643 cable"]
_sff_needed = _sff["polyline_length_mm"] + 2*spec.dim(nic.SFF, "plug_length")
assert _dac_needed * 1.1 <= spec.dim(nic.DAC, "length"), ("DAC length", _dac_needed)
network_report = {
    "link": "Berserk ConnectX-4 Lx (LRFC6911N riser, H12D SFF-8643 x4) to Kenshin ConnectX-4 Lx (chipset slot behind the 5090) over one QSFP28 passive DAC",
    "Berserk_NIC_holder": nic.report(),
    "QSFP28_DAC": {"route_polyline_mm": _dac["polyline_length_mm"], "plugs_outside_cages_mm": _dac_plugs,
        "minimum_length_mm": round(_dac_needed), "planned_length_mm": spec.dim(nic.DAC, "length"),
        "Kenshin_plug_past_deck_edge_mm": round(_kplug.x1 - SHELF_W, 2),
        "Kenshin_plug_past_rack_opening_mm": round(_kplug.x1 - (SHELF_W + SIDE_OVERHANG_LIMIT), 2),
        "Kenshin_cable_loop_past_rack_opening_mm": round(_dac_reach - (SHELF_W + SIDE_OVERHANG_LIMIT), 2),
        "service": "unplug the DAC at Kenshin before sliding the shelf; with the shelf in, the plug and loop sit beside the rack rail",
        "status": "cable not chosen; plug and bend sizes are allowances"},
    "SFF_8643_cable": {"route_polyline_mm": _sff["polyline_length_mm"], "minimum_length_mm": round(_sff_needed),
        "selected_length_mm": spec.dim(nic.SFF, "length"),
        "selected_length_sufficient": _sff_needed <= spec.dim(nic.SFF, "length"),
        "H12D_port_xy_mm": [round(H12D_SFF_PORT_X, 2), round(BERSERK_BOARD_Y, 2)],
        "H12D_port_basis": "photo-estimated from the H12D-8D manual's layout figure: middle of three SFF-8643 ports on the front PCB edge",
        "riser_plug": "lies along the riser's socket edge with its cable leaving toward the SATA end (owner, 2026-11-27); the cable turns up and forward over the plug, so nothing projects toward Kenshin's board"},
}
k_aio_foot_keepout_conflicts = []
for foot in k_aio_foot_boxes:
    for box in parts + connectors:
        if (box.name == "Kenshin GA II Lite radiator" or box.name.startswith("Kenshin AIO exhaust fan")):
            continue  # each foot intentionally meets its fan frame
        if overlap(foot, box):
            k_aio_foot_keepout_conflicts.append(box.name)
k_aio_mount_checks = []
# Built in radiator-local coordinates, checked and placed after the mirror.
for x0, frame_local in ([(x0, kenshin_aio_frame_on_shelf(k_aio_frame,x0)) for x0 in K_AIO_FRAME_X]
                        + [(151, k_aio_spacer_local)]):
    frame = k_aio_shape(frame_local)
    for component in parts + connectors:
        assert frame.val().intersect(component.shape().val()).Volume() < .01, ("Kenshin AIO frame",component.name)
    for post in post_locations:
        envelope = cq.Workplane("XY").center(post["x_mm"],post["y_mm"]).circle(3).extrude(post["top_z_survey_mm"])
        assert frame.val().intersect(envelope.val()).Volume() < .01, ("Kenshin AIO frame",post)
    for x in (x0+7.5,x0+112.5):
        for z in (K_AIO_Z+7.5,K_AIO_Z+112.5):
            witness = cq.Workplane("XZ").center(x,z).circle(2).extrude(-6).translate((0,K_AIO_FRAME_REAR_Y - 6,0))
            assert frame_local.val().intersect(witness.val()).Volume() < .01, (x,z,"AIO screw axis")
            # Continuous visible clearance shaft through fan and6mm frame/spacer.
            shaft = k_aio_shape(cq.Workplane("XZ").center(x,z).circle(1.5).extrude(-34).translate((0,K_AIO_Y+27,0)))
            fan = next(b for b in k_aio_local_boxes.values() if b.name.startswith("Kenshin AIO exhaust fan") and abs(b.x+62-(x0+60)) < .01)
            assert shaft.val().intersect(fan_shapes[fan.name].val()).Volume() < .01
            sy = k_aio_xy(x, 0)[1]
            assembly.add(shaft,name=f"Kenshin_AIO_shared_screw_shaft_{sy:g}_{z}_nominal",color=cq.Color(.65,.65,.68))
            washer = k_aio_shape(cq.Workplane("XZ").center(x,z).circle(5).circle(2.25).extrude(-1).translate((0,K_AIO_FAN_Y + 28,0)))
            head = k_aio_shape(cq.Workplane("XZ").center(x,z).circle(4).extrude(-3).translate((0,K_AIO_FAN_Y + 29,0)))
            driver = k_aio_shape(cq.Workplane("XZ").center(x,z).circle(3).extrude(-35).translate((0,K_AIO_FAN_Y + 32,0)))
            for name,other in placed_prints:
                assert other.val().intersect(washer.union(head).val()).Volume() < .01, (name,x,z,"AIO screw head")
                assert other.val().intersect(driver.val()).Volume() < .01, (name,x,z,"AIO driver")
            assembly.add(washer.union(head),name=f"Kenshin_AIO_screw_head_{sy:g}_{z}_survey",color=cq.Color(.65,.65,.68))
            k_aio_mount_checks.append({"axis_yz_mm":[sy,z],"axis_direction":"X","washer_OD_thickness_mm":[10,1],
                "head_diameter_height_mm":[8,3],"outer_driver_clear_length_mm":35,
                "fan_plus_frame_or_spacer_stack_mm":34,"minimum_side_hole_edge_material_mm":4.75 if x0 == 151 else 5.25,
                "length_rule":"original safe fan screw length +6mm insert +any added washer thickness; measure first",
                "factory_thread_and_engagement_verified":False})
# Eight shared front screws clamp fan + original bracket into the radiator.
# Head seats and factory thread/engagement remain measured-hardware checks.
h115i_mount_checks = []
for x in H115I_SCREW_X:
    for z in (RAD_Z+7.75,RAD_Z+132.25):
        shaft = cq.Workplane("XZ").center(x,z).circle(1.5).extrude(-30).translate((0,RAD_FAN_Y,0))
        washer = cq.Workplane("XZ").center(x,z).circle(5).circle(2.25).extrude(1).translate((0,RAD_FAN_Y,0))
        head = cq.Workplane("XZ").center(x,z).circle(4).extrude(3).translate((0,RAD_FAN_Y-1,0))
        driver = cq.Workplane("XZ").center(x,z).circle(3).extrude(35).translate((0,RAD_FAN_Y-4,0))
        assert shaft.val().intersect(fan_shapes["H115i intake fans"].val()).Volume() < .01
        for name,other in placed_prints:
            assert other.val().intersect(shaft.val()).Volume() < .01,(name,x,z,"H115i screw shaft")
            assert other.val().intersect(washer.union(head).val()).Volume() < .01,(name,x,z,"H115i screw head")
            assert other.val().intersect(driver.val()).Volume() < .01,(name,x,z,"H115i driver")
        assembly.add(shaft.union(washer).union(head),name=f"H115i_shared_front_screw_{x}_{z}_survey",color=cq.Color(.65,.65,.68))
        h115i_mount_checks.append({"axis_xz_mm":[x,z],"fan_plus_frame_mm":30,
            "front_head_y_mm":RAD_FAN_Y-4,"front_driver_clear_length_mm":35,
            "factory_thread_and_engagement_verified":False,
            "length_rule":"preserve original safe fan-screw engagement; account for added5mm bracket and actual washer/head seats"})

# Brace uses existing rear threads; the motherboard carries none of its load.
for component in parts + connectors:
    assert aio_brace_installed.val().intersect(component.shape().val()).Volume() < .01, (aio_brace.PART, component.name)
aio_brace_fasteners = []
for z in aio_brace.RADIATOR_Z:
    x = aio_brace.X0 + aio_brace.SCREW_X
    rear_y = RAD_Y + RAD_D
    shaft = cq.Workplane("XZ").center(x,z).circle(1.75).extrude(-aio_brace.FACE_T).translate((0,rear_y,0))
    washer = cq.Workplane("XZ").center(x,z).circle(5).extrude(-1).translate((0,rear_y+aio_brace.FACE_T,0))
    head = cq.Workplane("XZ").center(x,z).circle(4).extrude(-4).translate((0,rear_y+aio_brace.FACE_T+1,0))
    driver = cq.Workplane("XZ").center(x,z).circle(3).extrude(-35).translate((0,rear_y+aio_brace.FACE_T+5,0))
    for offset in (-2,0,2):
        for name,other in placed_prints:
            for envelope in (shaft,washer,head,driver):
                assert other.val().intersect(envelope.translate((0,0,offset)).val()).Volume() < .01, (aio_brace.PART,name,z,offset)
        for component in parts+connectors:
            for envelope in (washer,head,driver):
                assert component.shape().val().intersect(envelope.translate((0,0,offset)).val()).Volume() < .01, (aio_brace.PART,component.name,z,offset)
    assembly.add(shaft.union(washer).union(head),name=f"H115i_brace_rear_screw_{z}_survey",color=cq.Color(.8,.5,.2))
    aio_brace_fasteners.append({"axis_xz_mm":[x,z],"rear_face_y_mm":rear_y,
        "frame_thickness_mm":aio_brace.FACE_T,"washer_od_thickness_mm":[10,1],
        "head_diameter_height_mm":[8,4],"driver_diameter_length_mm":[6,35],
        "checked_Z_adjustment_mm":[-2,2],"factory_thread_and_engagement_verified":False})

# Derive the drill plan from bracket geometry. Transfer through dry-fitted
# mounts only after checking the real deck and factory slide attachments.
for x0 in H115I_FRAME_X:
    for x, depth in RAD_ANCHORS:
        add_shelf_hole("h115i_screw_frame_drill_plan", x0 + x,
                       RAD_FRAME_FRONT_Y + depth)
for x,y in aio_brace.ANCHORS:
    add_shelf_hole(aio_brace.PART,aio_brace.X0+x,RAD_Y+RAD_D+y,aio_brace.SHELF_SLOT_L)
for system in PSU_FRAMES:
    for x,depth in PSU_SHELF_ANCHORS:
        add_shelf_hole(f"psu_screw_frame_{system.lower()}_drill_plan",*psu_anchor_xy(system,x,depth),
                       axis="Y" if system == "Berserk" else "X")
for fan_x in K_AIO_FRAME_X:
    for x, depth in K_AIO_ANCHORS:
        add_shelf_hole("kenshin_aio_screw_frame_drill_plan", *k_aio_xy(fan_x + x,
                       K_AIO_FRAME_REAR_Y - depth))
for local_x in (10, 40):
    add_shelf_hole("gpu_5090_rest_drill_plan", GPU_REST_X + local_x, GPU_REST_Y + GPU_REST_ANCHOR_Y)
for x,y in t_cool.ANCHORS:add_shelf_hole("v100_gpu_shroud",x,y,t_cool.SLOT_LENGTH)
for x,y in nic.ANCHORS:add_shelf_hole(nic.PART,x,y,nic.SLOT_L)


# Check the actual assembled printed solids, not only a list of intended
# coordinates. Every round steel pilot must land inside exactly one printed
# front-to-rear slot, with clearance over a small adjustment range.
mounted_brackets = {
    "v100_gpu_shroud":[v100_plenum],
    aio_brace.PART: [aio_brace_installed],
    **{label: [shape] for label, shape in installed_adapter_shapes.items()},
    "h115i_screw_frame_drill_plan": [radiator_frame_on_shelf(rad_frame, x)
                                      for x in H115I_FRAME_X],
    "psu_screw_frame_berserk_drill_plan": [psu_frame_on_shelf(psu_frame_berserk, "Berserk")],
    "psu_screw_frame_kenshin_drill_plan": [psu_frame_on_shelf(psu_frame_kenshin, "Kenshin")],
    "kenshin_aio_screw_frame_drill_plan": [k_aio_frame_installed(x) for x in K_AIO_FRAME_X],
    "gpu_5090_rest_drill_plan": [k_shape(gpu_rest.translate((GPU_REST_X, GPU_REST_Y, 0)))],
    nic.PART: [nic_holder],
}
fastener_access = []
for site in shelf_attachment_holes:
    x, y = site["center_xy_mm"]
    candidates = [shape for shape in mounted_brackets[site["part"]]
                  if (shape.val().BoundingBox().xmin <= x <= shape.val().BoundingBox().xmax
                      and shape.val().BoundingBox().ymin <= y <= shape.val().BoundingBox().ymax)]
    assert len(candidates) == 1, site
    # Keep each OD12 backing washer on steel across full slot adjustment.
    offsets = (-2.5, 0, 2.5)
    if site["part"] == aio_brace.PART:
        offsets = (-aio_brace.SHELF_TRAVEL, 0, aio_brace.SHELF_TRAVEL)
    if "_mobo_adapter_" in site["part"]:
        offsets = (-2.0,0,2.0)
    if site["part"] == "v100_gpu_shroud":
        offsets = (-1.25,0,1.25)
    for y_offset in offsets:
        wdx, wdy = slot_offset(site, y_offset)
        witness = (cq.Workplane("XY").center(x + wdx, y + wdy)
                   .circle(.5).extrude(6)
                   .translate((0, 0, 0)))
        assert candidates[0].val().intersect(witness.val()).Volume() < .01, (site, y_offset)

    # Check a real washer/head envelope, not just the center of the shaft.
    # Install the bare mounts before hardware that intentionally covers them.
    rest = site["part"] == "gpu_5090_rest_drill_plan"
    riser = False  # both add-in NICs and receivers deferred
    small_mobo = site["fastener"].startswith("M3")
    seat, washer_radius = (18.0, 4.5) if rest else (6.0, 6.0)
    if site["part"] == aio_brace.PART:
        seat = aio_brace.FOOT_T
    if riser or "_mobo_adapter_" in site["part"]: washer_radius=4.5
    if small_mobo: washer_radius=3.5
    washer_t,head_h=(.5,3) if riser or small_mobo else (1,4)
    head_r=3 if small_mobo else 4
    covered_by = set()
    if "_mobo_adapter_" in site["part"]:
        # Explicit end-ear hardware makes its above/below-PCB access inspectable.
        back_r,back_t,nut_d,nut_h,shaft_r=(3.5,.5,6.35,2.4,1.5) if small_mobo else (6,1,8.08,3.2,2)
        hardware=(cq.Workplane("XY").center(x,y).circle(washer_radius).extrude(washer_t).translate((0,0,6))
            .union(cq.Workplane("XY").center(x,y).circle(head_r).extrude(head_h).translate((0,0,6+washer_t)))
            .union(cq.Workplane("XY").center(x,y).circle(shaft_r).extrude(16).translate((0,0,6+washer_t-16)))
            .union(cq.Workplane("XY").center(x,y).circle(back_r).extrude(back_t).translate((0,0,-SHELF_T-back_t)))
            .union(cq.Workplane("XY").center(x,y).polygon(6,nut_d).extrude(nut_h).translate((0,0,-SHELF_T-back_t-nut_h))))
        assembly.add(hardware,name=f"{site['part']}_shelf_bolt_{x}_{y}",color=cq.Color(.65,.67,.7))
        for travel in (-2,0,2):
            bdx, bdy = slot_offset(site, travel)
            backing=cq.Workplane("XY").center(x+bdx,y+bdy).circle(back_r).extrude(back_t).translate((0,0,-SHELF_T-back_t))
            if site["install_before_PCB"]:
                # The small backing washers must bear fully on the solid deck.
                steel_foot=(cq.Workplane("XY").center(x+bdx,y+bdy).circle(back_r)
                            .extrude(.1).translate((0,0,-.1)))
                assert steel_foot.val().cut(base_shelf_deck.val()).Volume()<.01,(site,travel,"under-PCB washer on sound steel")
            for box in gpu_backer_boxes:
                assert backing.val().intersect(box.shape().val()).Volume()<.01,(site,box.name,"backing washer")

    for offset in offsets:
        odx, ody = slot_offset(site, offset)
        # Every top washer stays on the deck footprint across slot travel.
        assert .5 <= x + odx - washer_radius and x + odx + washer_radius <= SHELF_W - .5, (site, offset)
        assert .5 <= y + ody - washer_radius and y + ody + washer_radius <= SHELF_D - .5, (site, offset)
        washer = (cq.Workplane("XY").center(x + odx, y + ody).circle(washer_radius)
                   .extrude(washer_t).translate((0, 0, seat)))
        head = (cq.Workplane("XY").center(x + odx, y + ody).circle(head_r)
                .extrude(head_h).translate((0, 0, seat + washer_t)))
        hardware = washer.union(head).val()
        tool = (cq.Workplane("XY").center(x + odx, y + ody).circle(4 if riser else 3)
                .extrude(35).translate((0, 0, seat + washer_t + head_h))).val()
        for name, shape in placed_prints:
            assert shape.val().intersect(hardware).Volume() < .01, (site, offset, "washer/head", name)
            if "_mobo_adapter_" in site["part"] and name == "V100 GPU shroud":
                if shape.val().intersect(tool).Volume() > .01:
                    covered_by.add(name + " (fit after motherboard shelf bolts)")
            elif site["part"] == "h115i_screw_frame_drill_plan" and name == "H115i hose brace":
                if shape.val().intersect(tool).Volume() > .01:
                    covered_by.add("H115i hose brace (fit after original frame shelf bolts)")
            else:
                assert shape.val().intersect(tool).Volume() < .01, (site, offset, "driver", name)
        for box in parts + connectors:
            assert box.shape().val().intersect(hardware).Volume() < .01, (site, offset, "installed head", box.name)
            if box.shape().val().intersect(tool).Volume() > .01:
                covered_by.add(box.name)
    if "_mobo_adapter_" in site["part"]:
        if site["install_before_PCB"]:
            # These explicit under-PCB anchors are fitted to the bare adapter.
            # Installed head collision checks above still apply at every offset.
            assert seat+washer_t+head_h < BOARD_Z
        else:
            assert not any("ATX board" in n for n in covered_by), (site,covered_by)
    fastener_access.append({"part": site["part"], "fastener":site["fastener"], "center_xy_mm": [x, y],
                            "washer_seat_z_mm": seat, "washer_max_od_mm": washer_radius * 2,
                            "head_envelope_diameter_height_mm": [head_r*2, head_h], "washer_thickness_mm":washer_t,
                            "driver_diameter_mm": 8 if riser else 6, "driver_clear_height_mm": 35,
                            "slot_axis": site["printed_bracket_slot_axis"],
                            "checked_adjustment_mm": [min(offsets), max(offsets)],
                            "nominal_rear_washer_margin_mm": round(SHELF_D - y - washer_radius, 3),
                            "minimum_washer_margin_to_deck_edge_at_checked_travel_mm": round(min(
                                min(x + slot_offset(site, o)[0] - washer_radius, SHELF_W - x - slot_offset(site, o)[0] - washer_radius,
                                    y + slot_offset(site, o)[1] - washer_radius, SHELF_D - y - slot_offset(site, o)[1] - washer_radius)
                                for o in offsets), 3),
                            "bare_bracket_tool_access": True,
                            "install_before": sorted(covered_by)})
optional_mobo_access = []
for site in optional_mobo_shelf_anchors:
    x,y=site["center_xy_mm"]
    for travel in (-2,0,2):
        dx, dy = (travel, 0) if site["part"].startswith("kenshin_") else (0, travel)
        head=(cq.Workplane("XY").center(x+dx,y+dy).circle(3.5).extrude(.5).translate((0,0,6))
            .union(cq.Workplane("XY").center(x+dx,y+dy).circle(3).extrude(3).translate((0,0,6.5))))
        shaft=cq.Workplane("XY").center(x+dx,y+dy).circle(1.5).extrude(6)
        for name,shape in placed_prints:
            assert shape.val().intersect(head.val()).Volume()<.01,(site,name,"optional head")
        assert installed_adapter_shapes[site["part"]].val().intersect(shaft.val()).Volume()<.01,(site,"optional slot")
        for component in parts+connectors+gpu_post_base_keepouts:
            assert component.shape().val().intersect(head.val()).Volume()<.01,(site,component.name,"optional head")
    optional_mobo_access.append({**site,"checked_slot_adjustment_mm":[-2,2],
                                "slot_axis":"shelf X" if site["part"].startswith("kenshin_") else "shelf Y","install_before":["motherboard PCB"],
                                "head_to_PCB_clearance_mm":RAIL_T+STANDOFF_H-9.5})
metal_fastener_access = []
for site in metal_shelf_holes:
    x, y = site["center_xy_mm"]
    tail = "tail-support" in site["part"]
    offsets = (0,) if tail else (-2.5, 0, 2.5)
    for offset in offsets:
        seat = -SHELF_T - 1 if tail else 2
        washer = cq.Workplane("XY").center(x, y + offset).circle(6).extrude(1).translate((0, 0, seat))
        head_z = seat - 4 if tail else seat + 1
        head = cq.Workplane("XY").center(x, y + offset).circle(4).extrude(4).translate((0, 0, head_z))
        tool_z = head_z - 35 if tail else head_z + 4
        tool = cq.Workplane("XY").center(x, y + offset).circle(3).extrude(35).translate((0, 0, tool_z))
        for box in parts + connectors:
            assert box.shape().val().intersect(washer.union(head).val()).Volume() < .01, (site, "metal head", box.name)
            assert box.shape().val().intersect(tool.val()).Volume() < .01, (site, "metal driver", box.name)
        for name, shape in placed_prints:
            assert shape.val().intersect(washer.union(head).val()).Volume() < .01, (site, "metal head", name)
            assert shape.val().intersect(tool.val()).Volume() < .01, (site, "metal driver", name)
    metal_fastener_access.append({"part": site["part"], "fastener":site["fastener"], "center_xy_mm": [x, y],
        "driver_side": "below shelf" if tail else "above shelf", "washer_max_od_mm": 12,
        "checked_Y_offsets_mm": list(offsets), "nominal_tool_clearance": True,
        "physical_underside_access_verified": False})
exhaust_report, exhaust_shapes = gpu_exhaust.integrate(assembly, parts, connectors, OUT)

(OUT / "assembly-access-audit.json").write_text(json.dumps({
    "status": "nominal CAD clearance check; hardware dimensions and physical fit unverified",
    "M4_mount_count": sum(not x["fastener"].startswith("M3") for x in fastener_access),
    "M3_motherboard_mount_count":sum(x["fastener"].startswith("M3") for x in fastener_access), "M3_direct_metal_post_count": len(gpu_post_holes),
    "M3_shared_post_adapter_count":0,"through_post_mounts":through_post_access,
    "head_and_washer_collisions": 0, "bare_bracket_driver_collisions": 0,
    "limits": "Checks 35 mm of straight 6 mm driver above the head; no driver handle or hand model. Fit shelf fasteners before covering components. No material-strength or creep simulation.",
    "mounts": fastener_access,
    "additional_metal_M4_mount_count": len(metal_shelf_holes),
    "metal_mounts": metal_fastener_access,
    "cable_segment_checks": cable_clearance_checks,
    "V100_fan_fasteners": cooling_fasteners,
    "GPU_exhaust": exhaust_report,
    "V100_plenum_join_fasteners": plenum_joint_checks,
    "Kenshin_AIO_radiator_fasteners": k_aio_mount_checks,
    "H115i_shared_fan_radiator_fasteners": h115i_mount_checks,
    "H115i_hose_brace_rear_fasteners": aio_brace_fasteners,
    "network": network_report,
    "planned_upgrade_clearance_passed": not (planned_upgrade_conflicts or planned_upgrade_cable_conflicts),
    "planned_upgrade_component_conflicts": planned_upgrade_conflicts,
    "planned_upgrade_cable_conflicts": planned_upgrade_cable_conflicts,
    "V100_plenum_joint": {"type":"none; integral fan panel",
        "support":"three internalM4 slots on6mm shelf base;mount bare hood through fan opening before fan/duct;seal common inlet with flexible nonconductive skirt;independently support duct",
        "physical_fit_verified":False},
}, indent=2) + "\n")

def vent_overlap_estimate(x: float, y: float):
    return any(abs(x - col) <= VENT_LENGTH / 2 + 2.5 and
               abs(y - (VENT_FIRST_Y + row * VENT_PITCH_Y)) <= (VENT_WIDTH + 5) / 2
               for col in VENT_X for row in range(VENT_ROWS))


all_shelf_holes = shelf_attachment_holes + metal_shelf_holes + gpu_post_holes
for site in all_shelf_holes:
    x, y = site["center_xy_mm"]
    site["intersects_approximate_vent"] = vent_overlap_estimate(x, y)
    if "_mobo_adapter_" in site["part"] and site["fastener"].startswith("M3"):
        site["fabrication"] = "survey: drill diameter3.5mm in sound steel; confirm full bearing and usable adjustment on actual shelf"
    else:
        site["fabrication"] = ("survey: relocate hole" if site["intersects_approximate_vent"]
                               else "candidate new drill through sound steel; survey first")
assert len({tuple(site["center_xy_mm"]) for site in all_shelf_holes}) == len(all_shelf_holes)
shelf_deck = base_shelf_deck
for diameter in (3.5,5.0):
    hole_cutters=(cq.Workplane("XY").pushPoints([tuple(site["center_xy_mm"]) for site in shelf_attachment_holes+metal_shelf_holes if site["diameter_mm"]==diameter])
                  .circle(diameter/2).extrude(SHELF_T+1).translate((0,0,-SHELF_T-.5)))
    shelf_deck=shelf_deck.cut(hole_cutters)
post_cutters = (cq.Workplane("XY")
                .pushPoints([tuple(site["center_xy_mm"]) for site in gpu_post_holes])
                .circle(1.75).extrude(SHELF_T+1).translate((0,0,-SHELF_T-.5)))
shelf_deck = shelf_deck.cut(post_cutters)
assert len(shelf_deck.solids().vals()) == 1 and shelf_deck.val().isValid()
for site in gpu_post_holes:
    x, y = site["center_xy_mm"]
    bearing = (cq.Workplane("XY").polygon(6, post_hw.BASE_AF / (3 ** .5) * 2)
               .circle(1.75).extrude(.1).rotate((0,0,0),(0,0,1),hex_rotation(site["part"])).translate((x,y,-.1)))
    assert bearing.val().cut(shelf_deck.val()).Volume()<.01,(site,"full metal foot must seat on steel")
    # The snug regular hex is fixed at the actual modeled post axis. There
    # is no longer an elongated travel range to sample over the deck.
    frame=next(p for p in adapter_support_patterns if p["part"]==site["clearance_through_adapter"])
    sx,sy=min(frame["common_post_slot_centers_mm"],key=lambda pt:(pt[0]-x)**2+(pt[1]-y)**2)
    assert abs(sx-x)<.001 and abs(sy-y)<.001,(site,"hex opening must match post axis")
    site["fixed_hex_center_xy_mm"] = [sx,sy]
    site["fit_note"] = "Regular hex with 0.25 mm face clearance (snug fit on the real SW5.5 base confirmed by test print 2026-11-14) and no elongated adjustment. Point one corner toward PCB. Verify post axis against seated cards and full foot on real steel before drilling."
cq.exporters.export(shelf_deck, str(OUT / "rsus1931bk1-drill-plan-deck.step"))
assembly.add(shelf_deck, name="RSUS1931BK1_drill_plan_deck_not_manufacturer_CAD",
             color=cq.Color(.38, .42, .47))
# Side AIO: frame feet bear directly on the deck (no steel extension).
side_aio_holes=[h for h in shelf_attachment_holes if h["part"]=="kenshin_aio_screw_frame_drill_plan"]
assert len(side_aio_holes)==4
deck_top=cq.Workplane("XY").box(SHELF_W,SHELF_D,.1,centered=(False,False,False)).translate((0,0,.1)).val()
side_supports=[(k_aio_frame_installed(x),2.5) for x in K_AIO_FRAME_X]
for frame,travel in side_supports:
    for dx in (-travel,0,travel):
        moved=frame.translate((dx,0,0)).val()
        bearing=moved.intersect(cq.Workplane("XY").box(SHELF_W+200,SHELF_D+200,.1,centered=(False,False,False)).translate((-100,-100,.1)).val())
        assert bearing.Volume()/.1>=500,(dx,"side AIO mount needs at least 500 mm2 bearing on the deck")
        # Footprint must stay on the deck through the slot travel.
        assert bearing.cut(deck_top).Volume()<.01,(dx,"side AIO mount footprint must stay on steel through slot travel")
for h in side_aio_holes:
    x,y=h["center_xy_mm"]
    seat=6
    screw=(cq.Workplane("XY").center(x,y).circle(2).extrude(20).translate((0,0,seat+1-20))
           .union(cq.Workplane("XY").center(x,y).circle(6).circle(2.25).extrude(1).translate((0,0,seat)))
           .union(cq.Workplane("XY").center(x,y).circle(4).extrude(4).translate((0,0,seat+1)))
           .union(cq.Workplane("XY").center(x,y).circle(6).circle(2.25).extrude(1).translate((0,0,-SHELF_T-1)))
           .union(cq.Workplane("XY").center(x,y).polygon(6,8.08).circle(2).extrude(3.2).translate((0,0,-SHELF_T-4.2))))
    for name,solid in placed_prints:
        assert screw.val().intersect(solid.val()).Volume()<.01,(name,"side AIO shelf screw")
    assert screw.val().intersect(shelf_deck.val()).Volume()<.01
    assembly.add(screw,name=f"Side_AIO_M4_shelf_screw_{x}_{y}",color=cq.Color(.6,.63,.65))
# The fabricated rear extension is retired with the side-AIO layout.
for stale in ("rear-aio-steel-extension-drill-plan.step","rear-aio-steel-extension-report.json"):
    (OUT/stale).unlink(missing_ok=True)
rail_assembly_report = rail_assembly.add_to_assembly(
    assembly, SHELF_W, SHELF_D, SHELF_T, OUT)
assembly.save(str(OUT / "dual-pc-hammond-assembly.step"))
# Every instance must belong to a part folder; exports each component model into its folder.
assembly_bom = classify_assembly(assembly)
assert not assembly_bom["errors"], "\n".join(assembly_bom["errors"])

fig, (ax, side) = plt.subplots(2, 1, figsize=(12, 11),
                               gridspec_kw={"height_ratios": [1.45, 1]})
ax.add_patch(Rectangle((0, 0), SHELF_W, SHELF_D, facecolor="#edf0f3", edgecolor="black"))
ax.add_patch(Rectangle((-SIDE_OVERHANG_LIMIT, -45), RACK_OPENING_W, SHELF_D+140, fill=False,
                       edgecolor="#a83232", linestyle=":", lw=1.1, label="450 mm rack opening (EIA-310)"))
ax.add_patch(Rectangle((aio_brace.X0,RAD_Y+RAD_D),aio_brace.WIDTH,aio_brace.DEPTH,
                       facecolor="#399fa5",alpha=.5,label="H115i hose-end brace"))
palette = {"V100": "#3456a9", "ConnectX": "#c3488d", "LRFC6911N": "#c3488d", "5090": "#56a843", "H115i": "#b9574e",
           "PSU": "#d49a2e", "fan": "#8d77ad", "Berserk": "#2878b8",
           "Kenshin": "#33a4ac"}
for box in parts:
    key = next((k for k in palette if k.lower() in box.name.lower()), "fan")
    ax.add_patch(Rectangle((box.x, box.y), box.w, box.d, fill=False,
                           edgecolor=palette[key], lw=2))
    if "keepout" not in box.name and "RDIMM" not in box.name:
        if box.name == "Berserk ATX board":
            tx, ty, angle = box.x+185, box.y+215, 0
        elif box.name == "Kenshin ATX board":
            tx, ty, angle = box.x+35, box.y+210, 0
        else:
            tx, ty, angle = box.x + 3, box.y + box.d / 2, 90 if box.d > box.w else 0
        label = box.name.replace("Berserk V100 16GB ", "V100 ").replace("V100 pressure fan", "1 × 140mm Sanyo")
        label = label.replace(" ATX board", " board").replace("Berserk SP3 CPU and pump survey", "SP3 CPU /\npump survey").replace("Berserk BMC module survey", "BMC survey")
        if box.name == "Kenshin GA II Lite pump":
            label = "GA II Lite\npump"
        elif box.name.startswith("Kenshin AIO exhaust fan"):
            label = f"Exhaust {box.name.rsplit(' ', 1)[-1]}"
        ax.text(tx, ty, label, fontsize=7, color=palette[key], rotation=angle,
                va="center")
for label,tx in (("4 DIMMs",300+BERSERK_DX),("4 DIMMs",427+BERSERK_DX)):
    ax.text(tx,180,label,rotation=90,ha="center",fontsize=6,color="#2878b8")
hood_bounds = v100_plenum.val().BoundingBox()
ax.add_patch(Rectangle((hood_bounds.xmin, hood_bounds.ymin), hood_bounds.xlen, hood_bounds.ylen,
                       fill=False, edgecolor="#777777", lw=1.5))
ax.text(hood_bounds.xmin + 10, hood_bounds.ymin + 16, "printed exhaust plenum", fontsize=6)
for site in metal_shelf_holes:
    x, y = site["center_xy_mm"]
    ax.add_patch(Circle((x, y), 2.5, facecolor="#777777"))
for mount in mounts:
    ax.add_patch(Circle((mount["center_x_mm"], mount["center_y_mm"]), 2.8,
                        facecolor="#555f67", edgecolor="none"))
for shape in installed_adapter_shapes.values():
    for edge in shape.faces(">Z").edges().vals():
        pts=edge.sample(16)[0]
        ax.plot([p.x for p in pts],[p.y for p in pts],color="#2199a5",lw=.65)
for i, foot in enumerate(gpu_backer_boxes):
    ax.add_patch(Rectangle((foot.x, foot.y), foot.w, foot.d,
                           facecolor="#46bfb5", edgecolor="#158c84", alpha=.45,
                           lw=1.3, label="stock washers below PCIe posts" if i == 0 else None))
for i, post in enumerate(post_locations):
    ax.add_patch(Circle((post["x_mm"], post["y_mm"]), 3,
                        facecolor="#696b70", edgecolor="white", lw=.8,
                        label="metal PCIe support post" if i == 0 else None))
for i, x in enumerate(H115I_FRAME_X):
    ax.add_patch(Rectangle((x + 12, RAD_FRAME_FRONT_Y), 116, RAD_FOOT_REACH, fill=False,
                           edgecolor="#30343a", linestyle="--", lw=1.4,
                           label="H115i frame shelf foot" if i == 0 else None))
for i,(system,frame) in enumerate(PSU_FRAMES.items()):
    bb=psu_frame_on_shelf(frame,system).val().BoundingBox()
    ax.add_patch(Rectangle((bb.xmin,bb.ymin),bb.xlen,bb.ylen,fill=False,
                          edgecolor="#76588e",linestyle="--",lw=1.2,
                          label="PSU frame and shelf foot" if i==0 else None))
for z in (RAD_Z + 7.75, RAD_Z + 132.25):
    side.add_patch(Circle((RAD_Y, z), 2.5, fill=False, edgecolor="#b9574e", lw=1))
for i, foot in enumerate(k_aio_foot_boxes):
    ax.add_patch(Rectangle((foot.x, foot.y), foot.w, foot.d,
                           facecolor="#de784b", edgecolor="#9c3f25", alpha=.7,
                           lw=1.1, label="AIO-frame shelf foot" if i == 0 else None))
for i, site in enumerate(shelf_attachment_holes):
    x, y = site["center_xy_mm"]
    slot_length,slot_width=site["printed_bracket_slot_mm"]
    sw, sl = (slot_length, slot_width) if site["printed_bracket_slot_axis"].startswith("shelf X") else (slot_width, slot_length)
    ax.add_patch(FancyBboxPatch((x - sw / 2,
                                 y - sl / 2),
                                sw, sl,
                                boxstyle=f"round,pad=0,rounding_size={slot_width / 2}",
                                fill=False, edgecolor="#087ea4", lw=.8,
                                label="printed adjustment slot" if i == 0 else None))
    ax.add_patch(Circle((x, y), site["diameter_mm"] / 2, facecolor="#141a22", edgecolor="none",
                        label="M4/M3 printed-mount shelf hole" if i == 0 else None))
for site in optional_mobo_shelf_anchors:
    x,y=site["center_xy_mm"];ax.plot(x,y,"o",mfc="none",mec="#219447",ms=3)
for i, site in enumerate(gpu_post_holes):
    x, y = site["center_xy_mm"]
    ax.add_patch(Circle((x, y), 1.75, facecolor="#141a22", edgecolor="white", lw=.35,
                        label="M3 GPU base hole" if i == 0 else None))
for box in connectors:
    ax.add_patch(Rectangle((box.x, box.y), box.w, box.d, fill=False,
                           linestyle="--", edgecolor="#f39525", lw=1.2))
for label, route in cable_routes.items():
    points = route["points_mm"]
    ax.plot([p[0] for p in points], [p[1] for p in points],
            color="#e8881c", lw=1.5, linestyle="--", label=label)
for index, conflict in enumerate(planned_upgrade_conflicts):
    a, b = (next(box for box in parts + connectors if box.name == name)
            for name in conflict["components"])
    ax.add_patch(Rectangle((max(a.x,b.x),max(a.y,b.y)),
                           min(a.x1,b.x1)-max(a.x,b.x),min(a.y1,b.y1)-max(a.y,b.y),
                           facecolor="#de3333",edgecolor="#a82020",hatch="///",
                           label="BMC / GPU underside: measure clearance" if index == 0 else None))
ax.set(xlim=(-40, SHELF_W+60), ylim=(SHELF_D+95, -45), aspect="equal", xlabel="rack width X (mm)",
       ylabel="front → rear Y (mm)", title="Hammond RSUS1931BK1 — two PCs on 422.7 × 787.4 mm deck")
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8, frameon=False)
for box in parts:
    if box.name == "V100 pressure fan":
        yz=[t_cool.point(0,v,t)[1:] for v,t in ((-70,10),(70,10),(70,48),(-70,48))]
        side.add_patch(Polygon(yz,fill=False,edgecolor="#3456a9",lw=1.7))
        continue
    side.add_patch(Rectangle((box.y, box.z), box.d, box.h, fill=False,
                             edgecolor=palette[next((k for k in palette if k.lower() in box.name.lower()), "fan")], lw=1.7))
side.add_patch(Rectangle((RAD_FRAME_FRONT_Y + 4.5, 14), 26.5, 6,
                         facecolor="#b9574e", edgecolor="#80352f", alpha=.65,
                         label="H115i bottom bearing ledges (two)"))
side.add_patch(Polygon([(RAD_Y+RAD_D,0),(RAD_Y+RAD_D+aio_brace.DEPTH,0),
                       (RAD_Y+RAD_D,aio_brace.HEIGHT)],facecolor="#399fa5",alpha=.25,
                       label="H115i hose-end brace"))
for route in cable_routes.values():
    points = route["points_mm"]
    side.plot([p[1] for p in points], [p[2] for p in points],
              color="#e8881c", lw=1.25, linestyle="--")
side.axhline(COMPONENT_Z_LIMIT, color="red", linestyle="--", label="222.25 mm component planning band")
side.axhline(LOWER_Z_REFERENCE, color="#e18b24", linestyle=":", label="177.8 mm comparison height")
for name in (gpu_exhaust.TRANSITION, gpu_exhaust.ROOF):
    vertices,_=exhaust_shapes[name].val().tessellate(.8)
    yz=sorted(set((v.y,v.z) for v in vertices))
    def turn(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    halves=[]
    for points in (yz,yz[::-1]):
        hull=[]
        for point in points:
            while len(hull)>=2 and turn(hull[-2],hull[-1],point)<=0: hull.pop()
            hull.append(point)
        halves.extend(hull[:-1])
    side.add_patch(Polygon(halves,fill=False,edgecolor="#268a99",lw=1.4))
hose_y,hose_z=gpu_exhaust.hose_path_points()
side.plot(hose_y,hose_z,color="#268a99",ls="--",label="adjustable flex duct to provisional roof")
side.add_patch(Rectangle((0,-rail_assembly.SIDE_HEIGHT),SHELF_D,rail_assembly.SIDE_HEIGHT,
                         facecolor="#c4cbd0",edgecolor="#65727c",alpha=.5,label="downward shelf folds (envelope)"))
side.axhline(400,color="#555",ls=":",label="provisional inner ceiling")
side.set(xlim=(-45, SHELF_D+95), ylim=(-70, 425), xlabel="front → rear Y (mm)",
         ylabel="height above shelf deck Z (mm)", title="Side clearance; duct requires upper rack space")
side.legend(loc="upper left", fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "dual-pc-hammond-layout.png", dpi=190)
plt.close(fig)

# Separate cooling views show the broad hood, internal shelf anchors and GPU overlap.
fig = plt.figure(figsize=(15, 6))
for index, (title, solids, view) in enumerate([
    ("One-piece shroud: integral fan panel",
     [(v100_plenum, [.22, .59, .64])],
     (24, -60)),
    ("Rear-array hood; three shelf anchors",
     [(v100_plenum, [.30, .64, .43]),*( (p.shape(), [.65,.68,.72]) for p in parts if "V100 16GB" in p.name)],
     (24, 120)),
], 1):
    axis = fig.add_subplot(1, 2, index, projection="3d")
    for shape, color in solids:
        vertices, triangles = shape.val().tessellate(.2)
        points = np.array([[v.x, v.y, v.z] for v in vertices])
        faces = points[np.array(triangles)]
        normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
        lengths = np.maximum(np.linalg.norm(normals, axis=1), 1e-9)
        light = np.abs((normals / lengths[:, None]) @ np.array([.3, -.4, .866]))
        colors = np.array(color)[None, :] * (.55 + .4 * light[:, None])
        axis.add_collection3d(Poly3DCollection(faces, facecolors=colors, edgecolors=colors, linewidths=.1))
    view_bounds = [shape.val().BoundingBox() for shape, _ in solids]
    xmin, xmax = min(b.xmin for b in view_bounds)-8, max(b.xmax for b in view_bounds)+8
    ymin, ymax = min(b.ymin for b in view_bounds)-8, max(b.ymax for b in view_bounds)+8
    zmin, zmax = min(b.zmin for b in view_bounds)-8, max(b.zmax for b in view_bounds)+8
    axis.set(xlim=(xmin, xmax), ylim=(ymin, ymax), zlim=(zmin, zmax))
    axis.set_box_aspect((xmax - xmin, ymax - ymin, zmax - zmin))
    axis.set_proj_type("ortho")
    axis.view_init(elev=view[0], azim=view[1])
    axis.set_axis_off()
    axis.set_title(title, fontsize=11)
fig.suptitle("Upgrade fit prototypes — dimensions and interfaces require a dry fit", fontsize=13)
fig.subplots_adjust(top=.85, bottom=.1, left=.02, right=.98)
fig.savefig(OUT / "v100-cooling.png", dpi=160)
plt.close(fig)

# Assembly-oriented detail views expose the revised feet and bolt recesses.
# Orange solids are the checked washer/head envelopes, not threaded models.
fig = plt.figure(figsize=(15, 6.5))
details = [
    ("Radiator frame: exposed side ears", radiator_frame_on_shelf(rad_frame, 0),
     [(x, RAD_FRAME_FRONT_Y + y, 6, 6) for x, y in RAD_ANCHORS], 50,
     "Two shelf bolts beside the ledge; fit the radiator afterward."),
    ("Kenshin AIO: paired bearing frames", kenshin_aio_frame_on_shelf(k_aio_frame, 0),
     [(x, K_AIO_FRAME_REAR_Y - y, 6, 6) for x, y in K_AIO_ANCHORS], -60,
     "Rear face down to print; ledge supports the radiator."),
    ("5090 rest: recessed bolt heads", gpu_rest,
     [(x, GPU_REST_ANCHOR_Y, 18, 4.5) for x in (10, 40)], 50,
     "Heads sit 1 mm below the 24 mm support surface."),
]
for index, (title, shape, bolts, azimuth, caption) in enumerate(details, 1):
    ax3 = fig.add_subplot(1, 3, index, projection="3d")
    solids = [(shape, np.array([.22, .59, .64]))]
    for x, y, z, radius in bolts:
        fastener = (cq.Workplane("XY").center(x, y).circle(radius).extrude(1).translate((0, 0, z)))
        fastener = fastener.union(cq.Workplane("XY").center(x, y).circle(4).extrude(4).translate((0, 0, z + 1)))
        solids.append((fastener, np.array([.94, .48, .12])))
    drawn_faces, drawn_colors = [], []
    for solid, color in solids:
        vertices, triangles = solid.val().tessellate(.15)
        pts = np.array([[v.x, v.y, v.z] for v in vertices])
        faces = pts[np.array(triangles)]
        normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
        norms = np.maximum(np.linalg.norm(normals, axis=1), 1e-9)
        light = np.abs((normals / norms[:, None]) @ np.array([.3, -.4, .866]))
        face_colors = color[None, :] * (.55 + .4 * light[:, None])
        drawn_faces.extend(faces)
        drawn_colors.extend(face_colors)
    ax3.add_collection3d(Poly3DCollection(drawn_faces, facecolors=drawn_colors,
                                         edgecolors=drawn_colors, linewidths=.1))
    bounds = shape.val().BoundingBox()
    ax3.set(xlim=(bounds.xmin - 3, bounds.xmax + 3),
            ylim=(bounds.ymin - 3, bounds.ymax + 3),
            zlim=(bounds.zmin - 3, bounds.zmax + 3))
    ax3.set_box_aspect((bounds.xlen, bounds.ylen, bounds.zlen))
    ax3.set_proj_type("ortho")
    ax3.view_init(elev=25, azim=azimuth)
    ax3.set_axis_off()
    ax3.set_title(title, fontsize=12, pad=12)
    ax3.text2D(.5, -.08, caption, transform=ax3.transAxes, ha="center", fontsize=9, wrap=True)
fig.suptitle("Mounting details — teal printed parts, orange fastener clearance", fontsize=15)
fig.subplots_adjust(top=.85, bottom=.18, left=.02, right=.98, wspace=.05)
fig.savefig(OUT / "assembly-details.png", dpi=160)
plt.close(fig)

installed = {b.name:b for b in parts+connectors}
kb,kg,kp = (installed[n] for n in ("Kenshin ATX board","Kenshin RTX 5090","Kenshin owned HX1200i PSU"))
k_aio_installed_boxes = [b for b in parts if b.name in K_AIO_PARTS]
k_psu_frame_bounds = psu_frame_on_shelf(psu_frame_kenshin, "Kenshin").val().BoundingBox()
k_aio_frame_bounds = [k_aio_frame_installed(x).val().BoundingBox() for x in K_AIO_FRAME_X]
clearances = {
    "H115i_brace_to_board_front_mm": round(BERSERK_BOARD_Y-(RAD_Y+RAD_D+aio_brace.DEPTH),3),
    "component_height_planning_band_mm": round(COMPONENT_Z_LIMIT, 3),
    "lower_height_reference_mm": round(LOWER_Z_REFERENCE, 3),
    "planning_band_to_PSU_top_mm": round(COMPONENT_Z_LIMIT - 150, 3),
    "planning_band_to_radiator_mm": round(COMPONENT_Z_LIMIT - RAD_TOP, 3),
    "H115i_bottom_to_shelf_deck_mm": RAD_Z,
    "planning_band_to_V100_power_route_mm": round(COMPONENT_Z_LIMIT - 215, 3),
    "planning_band_to_5090_cable_keepout_mm": round(COMPONENT_Z_LIMIT - 196.8, 3),
    "lower_reference_V100_power_route_deficit_mm": round(215 - LOWER_Z_REFERENCE, 3),
    "radiator_to_Berserk_board_depth_gap_mm": round(BERSERK_BOARD_Y - (RAD_Y+RAD_D), 3),
    "radiator_to_planned_V100_power_plug_gap_mm": round(V100_FRONT_Y - bp.EPS_PROJECTION - (RAD_Y+RAD_D),3),
    "Berserk_GPU_tail_to_Kenshin_board_gap_mm": round(kb.y-V100_TAIL_Y,3),
    "Berserk_GPU_tail_to_Kenshin_GPU_y_gap_mm": round(kg.y-V100_TAIL_Y,3),
    "Berserk_GPU_to_GPU_x_gap_mm": round(40.64 - V100_W, 3),
    "Berserk_PSU_to_nearest_V100_x_gap_mm": round(min(V100_SLOTS.values()) - (PSU_BERSERK_X+86), 3),
    "Berserk_PSU_left_overhang_mm": round(-PSU_BERSERK_X, 3),
    "V100_fan_bbox_to_Kenshin_board_signed_y_gap_mm": round(kb.y-max(box.y1 for box in parts if box.name.startswith("V100 pressure fan")),3),
    "Kenshin_board_rear_to_PSU_y_gap_mm": round(kp.y-kb.y1,3),
    "Kenshin_GPU_to_PSU_y_gap_mm": round(kp.y-kg.y1,3),
    "Kenshin_PSU_rear_overhang_mm": round(kp.y1-SHELF_D,3),
    "GPU_to_shelf_rear_mm": round(SHELF_D-kg.y1,3),
    "Kenshin_post_backer_to_shelf_right_mm": round(SHELF_W - max(b.x1 for b in gpu_backer_boxes if b.name.startswith("Kenshin")), 3),
    "Berserk_post_cylinder_to_board_rear_mm": round(6 - PCIE_POST_SURVEY_D / 2, 3),
    "Kenshin_post_cylinder_to_board_IO_edge_mm": round(min(p["x_mm"] for p in post_locations if p["system"]=="Kenshin")-PCIE_POST_SURVEY_D/2-kb.x1,3),
    "Berserk_board_to_shelf_right_mm": round(SHELF_W - (BERSERK_X + bp.WIDTH), 3),
    "Kenshin_board_IO_edge_to_shelf_right_mm": round(SHELF_W-kb.x1,3),
    "Kenshin_IO_service_reserve_past_rack_opening_mm": round(kb.x1 + atx_mount.IO_SERVICE_DEPTH - (SHELF_W + SIDE_OVERHANG_LIMIT),3),
    "radiator_to_shelf_right_mm": round(SHELF_W-installed["Berserk H115i radiator"].x1,3),
    "Kenshin_AIO_left_overhang_with_heads_mm": round(REAR_ASSEMBLY_LIMIT_Y - K_AIO_DX,3),
    "Kenshin_AIO_heads_inside_rack_opening_mm": round(SIDE_OVERHANG_LIMIT-(REAR_ASSEMBLY_LIMIT_Y - K_AIO_DX),3),
    "Kenshin_AIO_rear_overhang_mm": round(max(b.y1 for b in k_aio_installed_boxes)-SHELF_D,3),
    "Kenshin_AIO_foot_to_shelf_left_mm": round(min(foot.x for foot in k_aio_foot_boxes), 3),
    "Kenshin_AIO_foot_to_shelf_rear_mm": round(SHELF_D-max(foot.y1 for foot in k_aio_foot_boxes), 3),
    "Kenshin_AIO_radiator_to_GPU_tail_x_gap_mm": round(kg.x-installed["Kenshin GA II Lite radiator"].x1,3),
    "Kenshin_AIO_frames_to_PSU_bracket_x_gap_mm": round(k_psu_frame_bounds.xmin-max(b.xmax for b in k_aio_frame_bounds),3),
    "Kenshin_AIO_radiator_to_Berserk_AC_plug_y_gap_mm": round(installed["Kenshin GA II Lite radiator"].y-installed["Berserk AC plug + tail"].y1,3),
    "planning_band_to_Kenshin_AIO_top_mm": round(COMPONENT_Z_LIMIT - (K_AIO_FRAME_H+k_aio.SUPPORT_T),3),
    "planning_band_to_Kenshin_AIO_frame_top_mm": round(COMPONENT_Z_LIMIT-K_AIO_FRAME_H-k_aio.SUPPORT_T,3),
    "Berserk_Ethernet_right_cabinet_lane_reach_mm": 12,
}
assert clearances["Berserk_GPU_tail_to_Kenshin_board_gap_mm"] >= 20
assert clearances["Berserk_GPU_to_GPU_x_gap_mm"] >= .6
assert clearances["Berserk_post_cylinder_to_board_rear_mm"] >= 3
assert clearances["Berserk_board_to_shelf_right_mm"] >= 4.0
assert clearances["Kenshin_board_IO_edge_to_shelf_right_mm"] >= KENSHIN_RAIL_DEPTH - .001
assert clearances["Kenshin_post_backer_to_shelf_right_mm"] >= 7
assert clearances["Kenshin_board_rear_to_PSU_y_gap_mm"] > 0
assert 0 <= clearances["Kenshin_PSU_rear_overhang_mm"] <= REAR_OVERHANG_LIMIT
assert clearances["Kenshin_AIO_rear_overhang_mm"] <= REAR_OVERHANG_LIMIT
assert clearances["Kenshin_AIO_heads_inside_rack_opening_mm"] >= SIDE_MARGIN - .001
assert clearances["Kenshin_AIO_foot_to_shelf_left_mm"] >= 6.0
assert clearances["Kenshin_AIO_radiator_to_GPU_tail_x_gap_mm"] >= 5
assert clearances["Kenshin_AIO_frames_to_PSU_bracket_x_gap_mm"] >= 3
assert clearances["planning_band_to_Kenshin_AIO_top_mm"] >= 4
fan_box = next(b for b in parts if b.name == "V100 pressure fan")
for b in parts+connectors:
    if b.name == "V100 pressure fan":continue
    assert fan_box.shape().val().intersect(b.shape().val()).Volume()<.01,("tilted fan",b.name)
clearances["V100_fan_top_above_shelf_mm"]=round(fan_box.z1,3)
clearances["V100_fan_above_component_band_mm"]=round(fan_box.z1-COMPONENT_Z_LIMIT,3)
assert clearances["H115i_bottom_to_shelf_deck_mm"] >= 10
rad_ref_x = H115I_SCREW_X
rad_frame_x = tuple(x+dx for x in H115I_FRAME_X for dx in (7.75,132.25))
rad_x_offset = max(abs(a - b) for a, b in zip(rad_ref_x, rad_frame_x))
assert rad_x_offset <= 2.0
hole_alignment = {
    "motherboard_to_adapter_max_nominal_offset_mm": 0.0,
    "Kenshin_AIO_radiator_to_frame_max_nominal_offset_mm": 0.0,
    "radiator_to_frame_max_nominal_x_offset_mm": rad_x_offset,
    "H115i_front_frame_holes": 8,
    "H115i_front_fan_holes": 8,
    "H115i_shared_fan_frame_radiator_screw_axes": len(h115i_mount_checks),
    "H115i_hose_brace_rear_screw_axes": len(aio_brace_fasteners),
    "Kenshin_AIO_frame_holes": 8,
    "motherboard_holes": len(mounts),
    "GPU_flange_survey_holes": len(gpu_flange_holes),
    "PSU_rear_thread_marks": len([h for h in mount_holes if h["interface"] == "PSU rear factory thread-to-frame"]),
    "PSU_to_frame_max_nominal_offset_mm": 0.0,
    "drilled_shelf_hole_alignment_nominal": True,
    "printed_shelf_slot_size_mm": [SHELF_SLOT_LENGTH, SHELF_SLOT_WIDTH],
    "motherboard_shelf_slot_exception_mm": {"adapter_M3":[8,4],"GPU_base_clearance":[atx_mount.POST_SLOT_LENGTH,atx_mount.POST_SLOT_WIDTH]},
    "V100_hood_shelf_slot_exception_mm": [t_cool.SLOT_LENGTH,t_cool.SLOT_WIDTH],
    "H115i_brace_shelf_slot_exception_mm": [aio_brace.SHELF_SLOT_L,aio_brace.SHELF_SLOT_W],
    "printed_shelf_slot_axis": "Y (front-to-rear) for Berserk and H115i mounts; X for Kenshin's turned adapters, 5090 rest, HX1200i bracket and the side-AIO frames and brace",
    "printed_shelf_slot_clearance_checked_in_CAD": True,
    "physical_shelf_verified": False,
}
assert len(mounts) == 18 and len(gpu_flange_holes) == 10
assert not any("NIC" in h["component"] for h in mount_holes)
pressure_holes = [h["center_mm"] for h in mount_holes if h["interface"] == "pressure fan factory clearance"]
assert len(pressure_holes) == len(fan_holes) == 4
assert all(min(sum((a - b) ** 2 for a, b in zip(center, factory)) for factory in pressure_holes) < 1e-8 for center in fan_holes)
# 28 before 2026-11-19, minus the two Kenshin AIO brace bolts, plus the NIC holder bolts.
assert len(nic.ANCHORS) == 4
assert len(shelf_attachment_holes) == 26 + len(nic.ANCHORS) + len(t_cool.ANCHORS) and len(gpu_post_holes) == 10
assert sum(h["part"] == "v100_gpu_shroud" for h in shelf_attachment_holes) == 3
assert len(metal_shelf_holes) == 4
assert all(sum(site["part"].startswith(f"{system}_mobo_adapter_")
               for site in shelf_attachment_holes) == 5
           for system in ("berserk", "kenshin"))
assert {part: sum(site["part"] == part for site in shelf_attachment_holes)
        for part in ("h115i_screw_frame_drill_plan",
                     "psu_screw_frame_berserk_drill_plan",
                     "psu_screw_frame_kenshin_drill_plan",
                     "kenshin_aio_screw_frame_drill_plan",
                     "gpu_5090_rest_drill_plan", nic.PART)} == {
    "h115i_screw_frame_drill_plan": 4,
    "psu_screw_frame_berserk_drill_plan": 2,
    "psu_screw_frame_kenshin_drill_plan": 2,
    "kenshin_aio_screw_frame_drill_plan": 4,
    "gpu_5090_rest_drill_plan": 2,
    nic.PART: 4,
}
assert len([h for h in mount_holes if h["interface"] == "H115i sandwich factory thread"]) == 8
assert len([h for h in mount_holes if h["interface"] == "H115i unused rear factory thread"]) == 6
assert len([h for h in mount_holes if h["interface"] == "H115i hose brace rear factory thread"]) == 2
assert len([h for h in mount_holes if h["interface"] == "Kenshin AIO rear factory thread"]) == 12
assert len([h for h in mount_holes if h["interface"] == "Kenshin AIO unused inward factory thread"]) == 12
assert len([h for h in mount_holes if h["interface"] == "Kenshin AIO fan factory clearance"]) == 12
assert len([h for h in mount_holes if h["interface"] == "fan-to-radiator"]) == 8
assert hole_alignment["PSU_rear_thread_marks"] == 4
(OUT / "mount-hole-manifest.json").write_text(json.dumps({
    "coordinate_system": "shelf X left-to-right viewed from rack front, Y front-to-rear, Z above deck; millimetres",
    "status": "provisional drill plan; survey actual shelf before drilling; do not drill component bodies",
    "CAD_files": ["dual-pc-hammond-assembly.step",
                  "rsus1931bk1-solid-deck.step",
                  "rsus1931bk1-drill-plan-deck.step",
                  "individual printed bracket STEP files"],
    "component_holes": mount_holes + gpu_flange_holes,
    "GPU_exhaust_interfaces": exhaust_report,
    "shelf_attachment_holes": all_shelf_holes,
    "optional_motherboard_shelf_holes":optional_mobo_shelf_anchors,
    "selectable_GPU_post_slots_per_board":8,
    "selectable_GPU_post_slot_centers_mm":{p["part"]:p["common_post_slot_centers_mm"] for p in adapter_support_patterns if p["common_post_slot_centers_mm"]},
    "GPU_post_slot_note":"Eight options per board; only the selected card posts appear in the required steel pattern. Locate real seated-card posts; high-X positions need port clearance checks.",
    "optional_motherboard_shelf_hole_note":f"{len(optional_mobo_shelf_anchors)} optional sites excluded from required drill/count plan; use only as needed, before PCB installation",
    "hole_count": len(all_shelf_holes),
    "M4_printed_mount_hole_count": sum(not h["fastener"].startswith("M3") for h in shelf_attachment_holes),
    "M3_motherboard_mount_hole_count":sum(h["fastener"].startswith("M3") for h in shelf_attachment_holes),
    "M3_direct_metal_post_hole_count": len(gpu_post_holes),
    "M3_shared_post_adapter_hole_count":0,
    "M4_metal_cooling_and_tail_support_hole_count": len(metal_shelf_holes),
    "estimated_vent_intersection_count": sum(s["intersects_approximate_vent"]
                                         for s in all_shelf_holes),
    "PSU_rear_face_pattern_local_xz_mm": PSU_REAR_HOLES_LOCAL_XZ,
    "radiator_bottom_bearing_ledge_per_frame_mm": [64, 26.5, 6],
    "alignment_checks": hole_alignment,
    "pending_physical_measurement": [
        "actual shelf folds, flat bearing area, sound steel and underside slide clearance",
        "actual populated motherboard holes and standoff hardware",
        "H115i revision, radiator face-hole pitch, screw thread and safe screw engagement",
        "GPU flange shape and post-hole coordinates; CAD tabs are survey markers",
        "both PSU rear screw patterns, orientation, AC-inlet locations and safe screw engagement; CAD marks refer only to existing factory threads",
        "GA II Lite Performance radiator hole pitch/thread/engagement, P28 connector projections, pump-port orientation, hose path and rear shelf lip",
    ],
}, indent=2) + "\n")
(OUT / "fit-report.json").write_text(json.dumps({
    "status": "Hammond sliding-shelf fit prototype; factory dimensions sourced, physical interfaces unmeasured. BMC/GPU underside clearance unresolved; planned angled-EPS routes clear nominal geometry",
    "AIO_fan_outline_revision": {
        "date":"2026-10-18",
        "Berserk":{"fan_face_mm":[140,140],"factory_hole_pitch_mm":[124.5,124.5],
                   "frame_width_height_mm":[140,160],"top_side_projection_mm":0,
                   "top_slot_edge_material_mm":4.25,"side_slot_edge_material_mm":5.5},
        "Kenshin":{"nominal_fan_face_mm":[120,120],"owned_fan_body_mm":[124,120,28],
                   "factory_hole_pitch_mm":[105,105],"frame_width_height_mm":[120,140],
                   "top_side_projection_beyond_nominal_fan_mm":0,
                   "top_slot_edge_material_mm":4.0,"side_slot_edge_material_mm":5.25},
        "both_frame_slots_length_width_mm":[7,4.5],
        "lower_support_height_mm":20,"Kenshin_feet_bear_on":"deck (rear steel extension retired 2026-11-16)","H115i_hose_brace_top_projection_mm":2,
        "retained_local_interfaces":"factory fan pitch, sandwich thickness, ledges and center spacer; Kenshin feet shortened to the radiator footprint and Kenshin brace dropped (2026-11-19)",
        "standard_pitch_sources":["https://cdn.noctua.at/media/noctua_nf_a14_pwm_infosheet_en_web-1.pdf",
                                  "https://noctua.at/en/products/fan/nf-a12x25-pwm/service"],
        "physical_fit_verified":False},
    "GPU_exhaust": exhaust_report,
    "H115i_hose_brace": aio_brace.report(RAD_Y+RAD_D,BERSERK_BOARD_Y),
    "Kenshin_AIO_frame_feet": {**k_aio.report(),
        "shelf_anchor_xy_mm":[h["center_xy_mm"] for h in shelf_attachment_holes if h["part"]=="kenshin_aio_screw_frame_drill_plan"],
        "brace":"none; the inward hose brace was dropped as unnecessary (owner 2026-11-19)"},
    "planned_upgrade_clearance": {"passed":not (planned_upgrade_conflicts or planned_upgrade_cable_conflicts),
        "component_conflicts":planned_upgrade_conflicts,"cable_conflicts":planned_upgrade_cable_conflicts,
        "action":"measure BMC components/headers and GPU underside; verify angled EPS projection, SP3 cooler and cables before installation; do not use intersecting parts"},
    "historical_observation_2026_10_10": {"Berserk_GPU_count": 2, "GPU_model": "NVIDIA GeForce GTX 1080 Ti",
                               "MSI_subsystem_id": "1462:360a", "per_GPU_power_limit_W": 280},
    "Berserk_platform": bp.report(),
    "Kenshin_clearance_revision":{"date":"2026-11-16","rotation_z_deg":-90,
        "basis":"owner mock-up photo: Kenshin I/O and PCIe brackets face the right shelf edge so the ConnectX card can be plugged in; GA II radiator on the left edge behind the Hercules; HX1200i at the rear",
        "Berserk_GPU_tail_to_Kenshin_board_gap_mm":clearances["Berserk_GPU_tail_to_Kenshin_board_gap_mm"],"physical_fit_verified":False},
    "selected_upgrade": {"Berserk_GPU_count": 4, "GPU_model": "NVIDIA Tesla V100 PCIe 16GB",
                         "installed": False, "aggregate_separate_VRAM_GB": 64,
                         "GPU_board_power_max_W": 1000,
                         "commissioning_start_power_limit_W_each": 180,
                         "slot_lane_widths": {k:16 for k in V100_SLOTS},
                         "slot_positions_basis": "H12D-8D manufacturer photograph plus nominal 40.64 mm dual-slot pitch; physical survey required",
                         "V100_body_dimension_source": "NVIDIA PB-08744-001_v03 figure 3: 266.70 x 111.15 mm; thickness is a 40 mm survey envelope",
                         "NICs": "Kenshin's ConnectX-4 Lx in the chipset slot behind the RTX 5090 (bracket on the right shelf edge); Berserk's on the LRFC6911N riser in the printed holder beside Kenshin's side AIO",
                         "link": "QSFP28 passive DAC between the two cards; see the network section",
                         "software": "Qwen3.8-27B Volta decoder and hybrid KV/state handoff require validation before purchase"},
    "Hammond_layout_revision": {
        "date":"2026-11-05", "deck_change_width_depth_mm":[round(SHELF_W-446,3),round(SHELF_D-700,3)],
        "Berserk_translation_from_previous_mm":[BERSERK_DX,BERSERK_DY],
        "Kenshin_orientation":"-90 degrees about Z (2026-11-16): rear I/O and PCIe brackets toward the right shelf edge, PCIe end toward the rear, CPU end toward Berserk; HX1200i on its side along the rear edge; GA II radiator along the left edge",
        "front_fan_projection_mm":max(0,-RAD_FAN_Y),
        "side_AIO_left_projection_with_heads_mm":clearances["Kenshin_AIO_left_overhang_with_heads_mm"],
        "side_AIO_rear_projection_mm":clearances["Kenshin_AIO_rear_overhang_mm"],
        "Kenshin_PSU_rear_projection_mm":clearances["Kenshin_PSU_rear_overhang_mm"],
        "Hercules_left_projection_mm":clearances["Berserk_PSU_left_overhang_mm"],
        "rack_opening_basis":"EIA-310 450 mm minimum opening between rails; side overhang kept 1 mm inside it",
        "Hercules_supported_depth_mm":245,
        "service":"Power down and disconnect fixed-rack power/data and roof duct before extending. No live-service cable carrier is designed; 711.2mm travel requires measured cabinet/door clearance.",
        "rack_space":"Shelf alone: 2U mounting, 3U required clearance per Hammond. Component band222.25mm is not total rack height. Fixed exhaust roof is provisionally Z400; overall allocation needs rack measurements.",
        "physical_fit_verified":False},
    "shelf": "Hammond RSUS1931BK1 solid 422.656 x 787.4 mm deck with supplied slides; downward folds are dimensioned envelopes, slide cross-sections and bracket positions illustrative",
    "NIC_lane":"Kenshin's ConnectX-4 Lx sits behind the RTX 5090 with its QSFP28 cage on the right shelf edge; Berserk's sits on its riser in the strip between Kenshin's side radiator and motherboard mount, cage facing the rack front.",
    "network": network_report,
    "direct_shelf_mount": {"body_width_mm": SHELF_W, "depth_mm": SHELF_D,
                           "steel_thickness_mm": SHELF_T,
                           "shelf_drilling_allowed": True,
                           "folds_and_underside_access_verified": False,
                           "solid_deck_step": "rsus1931bk1-solid-deck.step",
                           "drill_plan_deck_step": "rsus1931bk1-drill-plan-deck.step",
                           "estimated_slot_count": VENT_ROWS * len(VENT_X),
                           "proposed_attachment_count": len(all_shelf_holes),
                           "candidate_vent_intersections": sum(s["intersects_approximate_vent"] for s in all_shelf_holes),
                           "local_backing_plate_locations_survey": True},
    "lateral_support_review": {
        "design_basis": "stationary rack, ordinary handling only; verify holes, backing and loaded fit before powering",
        "Berserk_and_Kenshin_motherboards": "two interlocking flat sections per board, each with at least four non-collinear motherboard screws; five independent shelf anchors (two front ears, three under-PCB); eight choices per common rail; eight Berserk and nine Kenshin metal standoffs (Kenshin B optional)",
        "Berserk_and_Kenshin_PSUs": "each PSU rests on steel and uses two upper factory screws for lateral restraint; each open rear frame has a continuous lower rail and a symmetric two-slot shelf foot; PSU patterns and plug clearances remain unmeasured",
        "Berserk_H115i": "trimmed fan-flush replacements preserve the owner-fitted sandwich's ledges,40mm feet and factory axes; ledges bear radiator, 40mm feet fully supported on shelf; revised slots and loaded fit require checking",
        "five_GPUs": "Ten OBT posts use14mm M3 through-thread SW5.5 bases passing freely through plastic and seating directly on sound steel. M3x8 lower screws through two OD12x1 and two OD7x0.5 washers leave1.52mm nominal gap to owner-reported9mm OBT studs. Five separate shelf bolts retain each adapter pair. Fixed OBT nut height must be checked with fully seated cards. Each V100 also has a purchased M4 female/female 20 mm tail spacer with a 4 mm silicone bearing pad; avoid bare PCB components",
    "V100_cooling": "single Sanyo140mm fan on integral45-degree panel; broad3.2mm HT-PLA-GF rear-array hood with6mm base and three internalM4 shelf slots;no fitted collar or individual post cuts;flexible nonconductive inlet seal required;M4 T-nut pockets;physical and thermal qualification pending",
        "Kenshin_AIO": f"three coplanar owned fans pull outward past the left deck edge through the 360 radiator at{K_AIO_Z:g}mm bottom height; two120mm frames with{k_aio.REACH:g}mm feet inside the AIO footprint bear the radiator weight directly on the deck, plus one plain6mm middle spacer; twelve shared fan/radiator screws clamp the stack; no inward brace; loaded PETG fit unverified",
        "overall": "balanced drilled-hole concept is plausible, but physical holes, PETG stiffness, cooling and GPU post load paths are unverified"
    },
    "GPU_post_thread_stack": post_thread_stack,
    "motherboard_adapter_revision": {"interlocking_pair_count": 2,
                                      "printed_frame_count": len(adapter_parts),
                                      "standoff_count": 17,
                                      "optional_Kenshin_B_standoff_count": 1,
                                      "hole_datum_source": "Intel ATX specification 2.01, figure 3",
                                      "row_spacing_correction_mm": 7.62,
                                      "support_patterns": adapter_support_patterns,
                                      "standoff_slot_mm": [6.0, 3.7],
                                      "head_recess_mm": [10.8, 8.5, 3.0],
                                      "shared_post_joint_count":0,"through_post_joint_count":len(through_post_access),"standalone_front_anchor_count":4,"under_PCB_anchor_count":6,
                                      "identical_pair_for_both_boards":False,"common_front_section":True,"rear_rail_exception":"H12D GPU slot positions require shifted rear post rail","selectable_post_slots_per_board":8,
                                      "unused_post_positions_add_steel_holes":False,
                                      "adapter_thickness_mm": RAIL_T,
                                      "joint_count": len(adapter_seams),
                                      "joint_type": "three full-depth drop-in dovetails per board, including one perpendicular key; 0.3mm side clearance; shelf and standoffs retain Z",
                                      "shelf_slots_mm": {"M3_adapter_anchors":[8,4],"GPU_base_clearance":[atx_mount.POST_SLOT_LENGTH,atx_mount.POST_SLOT_WIDTH]},
                                      "GPU_base_opening":post_hw.opening_spec(),
                                      "M3_anchor_note":"Ten adapter anchors: M3x16,OD7x0.5 top/back washers and nuts; six under-PCB anchors go in first. Ten GPU bases: Wurth970140324 14mm M3 SW5.5 on steel, M3x8 below with two OD12x1 and two OD7x0.5 washers. All steel holes3.5mm; confirm fixed OBT nut height and solid steel before drilling",
                                      "bar_width_mm":25.,"ear_width_mm":14.,
                                      "shelf_anchor_access": "front anchors outside PCB; three mandatory anchors per rear section under PCB, fit before motherboard; high-X post/port clearance remains provisional",
                                      "printer_bed_mm": [270, 200],
                                      "optional_shelf_anchor_count_per_board":5,
                                      "rear_io_service_keepouts":rear_io_service_keepouts,
                                      "shelf_anchor_positions_verified": False,
                                      "recessed_standoff_screw_head_fit_verified": False},
    "Kenshin_AIO_module": {"model":"Lian Li GA II Lite Performance 360 Black (GA2L36PB)",
                        "specification_source":"https://lian-li.com/product/ga-ii-lite/",
                        "radiator_dimensions_mm":[397,120,27],"pump_dimensions_mm":[74,74,67],
                        "tube_length_mm":400,"fan_count":3,"fan_dimensions_mm":[124,120,28],
                        "radiator_installed_xy_range_mm":[[installed["Kenshin GA II Lite radiator"].x,installed["Kenshin GA II Lite radiator"].x1],[installed["Kenshin GA II Lite radiator"].y,installed["Kenshin GA II Lite radiator"].y1]],"radiator_bottom_z_mm":K_AIO_Z,
                        "bearing_ledge_per_frame_mm":[k_aio.LEDGE_W,k_aio.LEDGE_D,6],
                        "frame_print_orientation":f"rear face down;{k_aio.REACH:g}mm feet, webs and ledge rise from that face; installed feet fully bear on the deck inside the AIO footprint",
                        "radiator_screw_rule":"twelve matching factory-thread fan screws: preserve original safe engagement and add 6mm for frame/spacer plus any added washer thickness to original under-head length; thread and length unverified; never drill radiator",
                        "airflow":"radiator inward, all fans outward pulling toward the left cabinet side",
                        "center_spacer_mm":[119,119,6],"center_spacer_side_clearance_mm":0.5,"center_spacer_count":1,
                        "fan_bank_coplanar":True,"shared_fan_radiator_screw_count":12,
                        "frame_count": 2,
                        "foot_inner_x_mm": max(foot.x1 for foot in k_aio_foot_boxes),
                        "foot_count": len(k_aio_foot_boxes),
                        "shelf_anchors_per_frame": 2,
                        "shelf_anchor_X_adjustment_mm": [-2.5, 2.5],
                        "minimum_rear_washer_edge_margin_mm": round(SHELF_D - max(h["center_xy_mm"][1] for h in shelf_attachment_holes if h["part"]=="kenshin_aio_screw_frame_drill_plan") - 6, 3),
                        "radiator_screws_per_frame": 4,
                        "projection_beyond_left_edge_with_heads_mm": clearances["Kenshin_AIO_left_overhang_with_heads_mm"],
                        "projection_beyond_rear_edge_mm": clearances["Kenshin_AIO_rear_overhang_mm"],
                        "nominal_keepout_conflicts": sorted(set(k_aio_foot_keepout_conflicts)),
                        "physical_shelf_verified": False},
    "PSU_screw_frame_module": {"frame_count": 2,
                               "factory_rear_threads_per_frame": 2,
                               "continuous_lower_rail": True,
                               "frame_width_mm": {"Berserk": 92.5, "Kenshin": 92.5},
                               "height_mm":150,"foot_width_depth_mm":[50,30],
                               "shelf_anchors_local_x_depth_mm":PSU_SHELF_ANCHORS,
                               "material":"Polymaker HT-PLA-GF;0.4mm hardened steel nozzle;230C nozzle/50C bed;anneal and recheck fit",
                               "Berserk_open_top":False,
                               "Hercules_left_overhang_mm": -PSU_BERSERK_X,
                               "HX1200i_rear_overhang_mm": clearances["Kenshin_PSU_rear_overhang_mm"],
                               "HX1200i_orientation": "on its side along the rear edge; rear (AC) face toward -X, bracket turned +90 degrees; fan toward the rack rear",
                               "Berserk_photo_fit_revision": {
                                   "date": "2026-10-18",
                                   "source": "owner photos of the fitted PSU",
                                   "basis": "Owner photos establish LED location; owner later reports >10mm top-to-power-connector gap. Other connector dimensions remain estimates.",
                                   "top_crossbar_height_mm": 8,
                                   "owner_reported_top_to_connector_gap_mm": ">10",
                                   "modeled_minimum_top_to_connector_gap_mm": 10,
                                   "top_bar_to_connector_gap_mm": 2,
                                   "clearance_basis": "2026-10-18 owner report supersedes photo-estimated upper connector position; plug-body seating still requires fit check",
                                   "previous_top_crossbar_height_mm": 18,
                                   "LED_relief_width_height_mm": BERSERK_LED_RELIEF_WH,
                                   "LED_center_x_from_PSU_left_and_down_from_top_mm": BERSERK_LED_CENTER,
                                   "LED_relief_outer_web_mm": BERSERK_LED_OUTER_WEB,
                                   "local_LED_extension_beyond_PSU_mm": 6.5,
                                   "revised_fit_verified": False},
                               "outer_screw_slot_edge_material_mm": 4,
                               "minimum_top_screw_slot_edge_material_mm":3.5,
                               "factory_screw_slots_length_width_mm":[5,4],
                               "inner_screw_slot_edge_material_mm": 4,
                               "side_rail_thickness_at_screws_mm": 9,
                               "minimum_shelf_slot_end_material_mm": 6,
                               "shelf_anchors_per_frame": 2,
                               "basis": "Intel ATX12V guide figure 12-1 rotated onto PSU side; installed revisions unmeasured",
                               "PSU_weight_path": f"steel shelf supports the full 245mm Hercules depth over {86+PSU_BERSERK_X:g} of its 86mm width; the HX1200i overhangs the rear by {clearances['Kenshin_PSU_rear_overhang_mm']:g}mm; mass, edge folds and fascia clearance require dry fit",
                               "loaded_fit_verified": False},
    "H115i_support_module": {"frame_count": 2,
                               "owner_reported_fitted": False,
                               "previous_sandwich_geometry_owner_fitted": True,
                               "evidence": "owner installation photo and approximate 13mm face overhang",
                               "stack_front_to_rear": ["fans","fan-flush replacement frames","radiator"],
                               "bracket_front_y_mm_approx": RAD_FRAME_FRONT_Y,
                               "fan_y_extent_mm": [RAD_FAN_Y,RAD_FRAME_FRONT_Y],
                               "radiator_y_extent_mm": [RAD_Y,RAD_Y+RAD_D],
                               "shelf_anchor_y_mm": RAD_FRAME_FRONT_Y+28,
                               "minimum_front_washer_margin_at_full_slot_travel_mm": RAD_FRAME_FRONT_Y+28-2.5-6,
                               "shared_fan_frame_radiator_screw_count": len(h115i_mount_checks),
                               "reprint_required_for_trimmed_outline": True,
                               "identical_frames": True,
                               "top_rim_extension_above_radiator_mm": 0,
                               "factory_slot_length_width_mm": [RAD_FRAME_SLOT_L,RAD_FRAME_SLOT_W],
                               "upper_slot_top_edge_material_mm": 4.25,
                               "slot_side_edge_material_mm": 5.5,
                               "bottom_bearing_ledge_per_frame_mm": [64, 26.5, 6],
                               "shelf_foot_mm": [116, RAD_FOOT_REACH, 6],
                               "side_ears_clear_of_bearing_ledge": True,
                               "assembly_order": "secure bare shelf brackets before installing radiator and fans; radiator covers vertical shelf-bolt driver paths",
                               "shelf_anchors_per_frame": 2,
                               "radiator_weight_path": f"radiator bears on two ledges and {RAD_FOOT_REACH:g}mm feet fully on steel, two anchors per foot at Y{RAD_FRAME_FRONT_Y+28:g}",
                               "single_piece_print": True,
                               "front_unsupported_foot_depth_mm": max(0,-RAD_FRAME_FRONT_Y),
                               "loaded_fit_verified": False},
    "GPU_rest_module": {"position_mm": [*k_xy(GPU_REST_X+50,GPU_REST_Y),0],
                         "head_recess_length_width_depth_mm": [17, 12, 6],
                         "washer_max_od_thickness_mm": [9, 1],
                         "head_max_diameter_height_mm": [8, 4],
                         "nominal_head_clearance_to_card_mm": 1,
                         "minimum_recess_side_web_mm": 4,
                         "physical_contact_point_verified": False},
    "minimum_nominal_board_side_margin_mm": min(clearances["Berserk_board_to_shelf_right_mm"], clearances["Kenshin_board_IO_edge_to_shelf_right_mm"]),
    "planning_clearance_targets_mm": {
        "board_to_shelf_side": 10, "GPU_to_GPU_lateral": .64,
        "Berserk_card_tail_to_Kenshin_board": 20,
        "rear_post_backer_to_shelf_edge": 7,
    },
    "usable_shelf_width_verified": False,
    "unverified_assumptions": [
        "the 422.656mm published deck width does not establish bend radii or exact flat bearing area; measure the real shelf and cabinet before drilling",
        "candidate holes are nominal: survey real folds, slide attachment points and underside access; keep drill chips out of the factory slides",
        "do not drill PSU, radiator, motherboard or GPU bodies; their modeled holes are alignment references for existing factory interfaces",
        "use wide steel washers or backing strips beneath concentrated brackets, especially GPU post joints; deburr and protect drilled steel edges",
        "Berserk board has only4.656mm nominal clearance to the right shelf edge; Kenshin's I/O edge sits 25mm inside it with its rear rail flush to the edge; actual board and shelf fit must be checked",
        f"Kenshin's rear I/O, 5090 and ConnectX brackets face the right shelf edge: plugged cables (I/O approach reaches {clearances['Kenshin_IO_service_reserve_past_rack_opening_mm']:g}mm past the 450mm rack opening) must be unplugged or use right-angle plugs before the shelf slides",
        "V100 factory length/height are documented, but thickness, four PCIe slot centers, flange holes, tail bearing points and EPS connector sweeps must be surveyed on the selected PCIe cards",
        "remove shipping/retention extenders; the model uses the 266.7 mm bare-card length, not 312 or 339 mm with extenders",
        "four adjacent dual-slot cards have only 0.64 mm nominal lateral margin at a 40 mm survey thickness; verify screws, shrouds and motherboard components",
        "Hood high-X sidewall must be dry-fitted against actual Berserk rear ports and any I/O shield; unmeasured connector bodies are not established clear by the simplified assembly",
        "HT-PLA-GF V100 plenum must seal all four heatsinks and rear-post clearance; free-air ratings do not establish operating airflow; inspect actual loaded temperatures and stiffness",
        "keep Qwen decoder and RDMA readiness separate from mechanical fit; current standard vLLM excludes Volta and direct GPU memory transfer is topology-dependent",
        "PSU rear hole patterns, inlet and modular cable bends require physical measurement; keep each PSU's original modular cables",
        "H115i original brackets are owner-fitted in a fan/frame/radiator sandwich; approximate13mm overhang from owner, ledges touch at Z20; angled EPS plugs are modeled with an unverified 18mm projection target; actual product dimensions, electrical pinout and cable bends must be checked",
        f"Side AIO screw heads reach X{-clearances['Kenshin_AIO_left_overhang_with_heads_mm']:g} (1mm inside the 450mm opening) and the radiator reaches Y{SHELF_D+clearances['Kenshin_AIO_rear_overhang_mm']:g}; front fans start Y{RAD_FAN_Y:g}. Measure rack rails, doors and cabinet side intake space. Disconnect fixed-rack cables and exhaust duct before sliding",
        "ten selected GPU posts need ten14mm Wurth970140324 M3 female bases and M3x8 lower screws (3.48mm nominal engagement,1.52mm nominal gap to owner-reported9mm stud); plastic does not carry their clamp load. Eight selectable slots per board do not require populating all16. Verify fixed OBT nut height with seated card; PCIE1 high-X positions are unverified envelope-derived points near I/O, not manufacturer holes. Ten replacement14mm bases are required; ten rods total (six previously ordered, four additional). Both add-in NICs and risers are deferred",
        "ground each motherboard with a metal lead from a standoff to the steel shelf; printed adapters are insulating",
        "Kenshin's AC plug survey volume assumes a side/upward exit inside the bracket window at the HX1200i's -X face; verify the actual inlet and bend",
        "Berserk AC rises over the side-AIO hose end and runs rearward at Z205 beside the radiator; Kenshin AC leaves straight out the rear; Ethernet routes outside the right edge (about 12 mm); verify cabinet lanes and smooth cable bends",
        "PETG parts, drilled nominal1.52mm shelf joints, cooling and power have not had a sustained loaded test; generated G-code remains a fit prototype",
    ],
    "clearances_mm": clearances,
    "components_mm": [asdict(part) for part in parts],
    "large_connector_keepouts_mm": [asdict(part) for part in connectors],
    "printed_parts": print_manifest,
    "factory_shelf_assembly": rail_assembly_report,
    "installed_part_models": INSTALLED_MODELS,
    "motherboard_adapter_rail_envelopes_mm": [asdict(box) for box in bridge_boxes],
    "motherboard_adapter_web_envelopes_mm": [asdict(box) for box in adapter_web_boxes],
    "motherboard_adapter_seams": adapter_seams,
    "optional_motherboard_shelf_anchor_access":optional_mobo_access,
    "gpu_pcie_support_posts_survey": post_locations,
    "gpu_post_steel_backers_mm": [asdict(box) for box in gpu_backer_boxes],
    "assembly_access_audit": "assembly-access-audit.json",
    "motherboard_mounts_mm": mounts,
    "mount_hole_alignment": hole_alignment,
    "mount_hole_manifest": "mount-hole-manifest.json",
    "cable_routes": cable_routes,
    "Berserk_orientation": {"rear_IO":"rack rear", "PSU":"right viewed from rack rear (low X)", "AIO":"rack front", "board_front_y_mm":BERSERK_BOARD_Y, "board_rear_y_mm":V100_TAIL_Y, "printed_board_frames":"new interlocking sections authored in installed shelf coordinates; rear I/O orientation preserved"},
    "stock_tail_spacer_mounts": metal_shelf_holes,
    "V100_cooling_module": t_cool.report(),
}, indent=2) + "\n")
render_psu_preview(OUT)
render_motherboard_mounts_preview(OUT)
render_pcie_post_preview(OUT)
aio_brace.preview(OUT / "fan140-aio-hose-brace.png", RAD_Y + RAD_D)
k_aio.preview(OUT / "fan120-aio-frames.png", K_AIO_Y, K_AIO_FRAME_REAR_Y)  # radiator-local view
(OUT / "fan120-aio-frames-and-brace.png").unlink(missing_ok=True)
gpu_exhaust.preview(OUT / "gpu-exhaust-preview.png", exhaust_shapes, parts)
print(f"Generated {OUT}")

# Retired outputs belong to the replaced shelf conversion, not this build.
for pattern in ("rail_shelf_shim_*", "rail-shelf-*", "shelf-side-mounting-pattern.png",
                "shelf-vent-estimate.json", "adjshelfhdv-*.step", "kenshin-berserk-6u-shelf-*"):
    for retired in OUT.glob(pattern):
        retired.unlink()
# Printed STEP/STL now live in their part folders (parts/printed/<name>/).
for part in spec.load_all().values():
    if part.category == "printed":
        for suffix in (".step", ".stl"):
            (OUT / f"{part.id}{suffix}").unlink(missing_ok=True)
