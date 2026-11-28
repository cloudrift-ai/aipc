"""Cabinet cooling in the SysRacks SP 12.900: two 2 x 2 banks of 200 mm fans, the ESP32 controller and its 12 V supply.

Run with ``hwkit cad`` (``make cad BUILD=rack``). Builds the assembly, exports the
library models this build owns and writes models/cooling-report.json with the
fan-bank cutout pattern, the electrical totals and the heat-removal estimate.

The exhaust bank replaces the two stock fans under the inner top, toward the rear,
and blows into the space under the outer lid, which vents around its edge as
before. The intake bank hangs under the floor toward the front, blowing up through
four floor cutouts, where the stock design already draws air in. The controller and
supply sit on the inner top in front of the exhaust bank, under the lid. Outer
dimensions come from the cabinet spec; wall thickness and the lid are assumptions
until the cabinet is measured.

Coordinates (mm): X across the cabinet from its centre line, Y from the outer front
face toward the rear, Z up from the underside of the cabinet floor (the ground is
at -floor_clearance).
"""

from __future__ import annotations

import itertools
import json

import cadquery as cq

from hwkit import paths, spec
from hwkit.registry import classify_assembly

OUT = paths.MODELS
OUT.mkdir(parents=True, exist_ok=True)

FAN = spec.get("noctua-nf-a20-pwm")
SIZE, DEPTH, PITCH = FAN.dim("size"), FAN.dim("depth"), FAN.dim("hole_pitch")
ESP = spec.get("olimex-esp32-poe")
PSU = spec.get("meanwell-gst60a12-p1j")
BOARD = spec.get("rack-fan-controller-board")
PROBE = spec.get("ds18b20-waterproof-probe")
CAB = spec.get("rack-cabinet")
GASKET_PART = spec.get("silicone-gasket-2mm")
GASKET, GASKET_SHEET = GASKET_PART.dim("thickness"), GASKET_PART.dim("size")
CW, CD, CH = CAB.dim("outer_width"), CAB.dim("outer_depth"), CAB.dim("body_height")
WALL, LID, FLOOR_GAP = CAB.dim("wall_thickness"), CAB.dim("lid_thickness"), CAB.dim("floor_clearance")

# Layout allowances (provisional until the cabinet is measured).
FAN_GAP = 5.0  # between adjacent frames in a bank, room for the anti-vibration pads
BANK = 2  # fans per row and per column
BANK_MARGIN = 20.0  # bank edge from the inside of the front or rear wall
LID_PLATE = 3.0  # outer lid sheet; the rest of the lid thickness is the exhaust plenum
PROBE_OFFSET = 60.0  # probe tip distance from its bank, in the airstream
FAN_MOUNT_HOLE = 4.5  # illustrative; the frame hole diameter is not published
ROTOR_CUT = SIZE - 10.0  # illustrative rotor area and panel cutout; the bore diameter is not published
HUB = 80.0  # illustrative hub
FREE_AIR_MIN = SIZE / 4  # clear air wanted on the open side of a fan

FANS_PER_CHANNEL = BANK * BANK
assert FAN.quantity == 2 * FANS_PER_CHANNEL, ("fan quantity must fill both banks", FAN.quantity)
assert PITCH < SIZE, "hole pitch must lie inside the frame"
assert GASKET_SHEET >= SIZE, ("gasket sheet smaller than the fan frame", GASKET_SHEET, SIZE)
assert GASKET_PART.quantity == FAN.quantity, ("one gasket per fan", GASKET_PART.quantity, FAN.quantity)
assert PROBE.quantity == 2, "one intake and one exhaust probe"
header_count = next(p["count"] for p in BOARD.provides if p["type"] == "fan-header-4pin")
assert header_count == FAN.quantity, ("one controller header per fan, no splitters", header_count, FAN.quantity)


def fan_model() -> cq.Workplane:
    """Fan in its own frame: centred on X/Y, inlet face at Z = 0, outlet at Z = DEPTH."""
    frame = cq.Workplane("XY").rect(SIZE, SIZE).extrude(DEPTH)
    frame = frame.cut(cq.Workplane("XY").circle(ROTOR_CUT / 2).extrude(DEPTH))
    hub = cq.Workplane("XY").circle(HUB / 2).extrude(DEPTH)
    struts = cq.Workplane("XY")
    for angle in (0, 120, 240):
        strut = cq.Workplane("XY").center(SIZE / 4, 0).rect(SIZE / 2, 6.0).extrude(4.0).rotate((0, 0, 0), (0, 0, 1), angle)
        struts = struts.union(strut)
    fan = frame.union(hub).union(struts.translate((0, 0, DEPTH - 4.0)))
    holes = [(sx * PITCH / 2, sy * PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]
    fan = fan.cut(cq.Workplane("XY").pushPoints(holes).circle(FAN_MOUNT_HOLE / 2).extrude(DEPTH))
    assert fan.val().isValid() and len(fan.solids().vals()) == 1, "fan model must be one valid solid"
    return fan


def bank_centres() -> list[tuple[float, float]]:
    """Fan centres in the bank plane, relative to the bank centre: u across (X), v toward the rear (Y), row by row from the rear."""
    step = SIZE + FAN_GAP
    offs = [(i - (BANK - 1) / 2) * step for i in range(BANK)]
    return [(u, v) for v in reversed(offs) for u in offs]


FAN_SHAPE = fan_model()
bank_span = BANK * SIZE + (BANK - 1) * FAN_GAP
inner_w, inner_d = CW - 2 * WALL, CD - 2 * WALL
assert bank_span <= inner_w, ("bank wider than the cabinet interior", bank_span, inner_w)

top_underside = CH - LID - WALL  # underside of the inner top
top_surface = CH - LID  # top of the inner top, floor of the lid plenum
exhaust_y = CD - WALL - BANK_MARGIN - bank_span / 2
intake_y = WALL + BANK_MARGIN + bank_span / 2
assert intake_y < exhaust_y, "intake toward the front, exhaust toward the rear, so air crosses the equipment"
assert bank_span + 2 * BANK_MARGIN <= inner_d, ("bank deeper than the cabinet interior", bank_span, inner_d)

solids: dict[str, cq.Workplane] = {}
colors: dict[str, cq.Color] = {}

# Cabinet: carcass with doors closed, the eight fan cutouts, and the outer lid sheet.
shell = cq.Workplane("XY").box(CW, CD, top_surface, centered=(True, False, False))
shell = shell.cut(cq.Workplane("XY").box(inner_w, inner_d, top_surface - 2 * WALL, centered=(True, False, False)).translate((0, WALL, WALL)))
for u, v in bank_centres():
    shell = shell.cut(cq.Workplane("XY").circle(ROTOR_CUT / 2).extrude(WALL).translate((u, exhaust_y + v, top_underside)))
    shell = shell.cut(cq.Workplane("XY").circle(ROTOR_CUT / 2).extrude(WALL).translate((u, intake_y + v, 0)))
solids["cabinet_shell"] = shell
colors["cabinet_shell"] = cq.Color(0.35, 0.35, 0.38, 0.25)
solids["cabinet_lid"] = cq.Workplane("XY").box(CW, CD, LID_PLATE, centered=(True, False, False)).translate((0, 0, CH - LID_PLATE))
colors["cabinet_lid"] = cq.Color(0.35, 0.35, 0.38, 0.25)

# Gasket: the frame-sized sheet with the rotor opening cut out, between each frame and its panel.
GASKET_SHAPE = cq.Workplane("XY").rect(SIZE, SIZE).extrude(GASKET).cut(cq.Workplane("XY").circle(ROTOR_CUT / 2).extrude(GASKET))

# Exhaust bank: under the inner top, blowing up into the lid plenum.
for n, (u, v) in enumerate(bank_centres(), start=1):
    solids[f"exhaust_gasket_{n}"] = GASKET_SHAPE.translate((u, exhaust_y + v, top_underside - GASKET))
    solids[f"exhaust_fan_{n}"] = FAN_SHAPE.translate((u, exhaust_y + v, top_underside - GASKET - DEPTH))
    colors[f"exhaust_fan_{n}"] = cq.Color(0.85, 0.45, 0.25)

# Intake bank: under the floor, blowing up into the cabinet.
for n, (u, v) in enumerate(bank_centres(), start=1):
    solids[f"intake_gasket_{n}"] = GASKET_SHAPE.translate((u, intake_y + v, -GASKET))
    solids[f"intake_fan_{n}"] = FAN_SHAPE.translate((u, intake_y + v, -GASKET - DEPTH))
    colors[f"intake_fan_{n}"] = cq.Color(0.35, 0.55, 0.85)
for name in [k for k in solids if "_gasket_" in k]:
    colors[name] = cq.Color(0.75, 0.2, 0.2)

# Probes: vertical tubes in each stream, inside the cabinet.
tube_d, tube_l = PROBE.dim("tube_diameter"), PROBE.dim("tube_length")
solids["intake_probe"] = cq.Workplane("XY").circle(tube_d / 2).extrude(tube_l).translate((0, intake_y, WALL + PROBE_OFFSET))
solids["exhaust_probe"] = cq.Workplane("XY").circle(tube_d / 2).extrude(tube_l).translate(
    (0, exhaust_y, top_underside - GASKET - DEPTH - PROBE_OFFSET - tube_l)
)
for name in ("intake_probe", "exhaust_probe"):
    colors[name] = cq.Color(0.8, 0.8, 0.82)

# Controller board, ESP32-POE and supply on the inner top, ahead of the exhaust bank, under the lid.
bx, by, bh = BOARD.dim("board_width"), BOARD.dim("board_depth"), BOARD.dim("height")
pl, pw, ph = PSU.dim("length"), PSU.dim("width"), PSU.dim("height")
board_x0, board_y0 = -bx - 10.0, WALL + 40.0
solids["controller_board"] = cq.Workplane("XY").box(bx, by, 1.6, centered=False).translate((board_x0, board_y0, top_surface + 5.0))
colors["controller_board"] = cq.Color(0.2, 0.55, 0.3)
# The ESP32-POE sits on 8 mm female headers with its RJ45 end (which overhangs its own board)
# toward the cabinet side, so the patch-lead plug has free air instead of the 12 V supply.
ew = ESP.dim("board_width")
el = ESP.dim("board_length") + ESP.dim("rj45_overhang")
eh = 1.6 + ESP.dim("component_height")
esp_x0, esp_y0, esp_z0 = board_x0 + 2.0, board_y0 + 10.0, top_surface + 5.0 + 1.6 + 8.0
solids["esp32_poe"] = cq.Workplane("XY").box(el, ew, eh, centered=False).translate((esp_x0, esp_y0, esp_z0))
colors["esp32_poe"] = cq.Color(0.6, 0.12, 0.12)
assert esp_x0 + el <= board_x0 + bx, "ESP32-POE runs past the controller board"
PLUG_REACH = 45.0  # RJ45 plug, boot and the patch lead's bend radius (allowance)
plug_zone = cq.Workplane("XY").box(PLUG_REACH, ew, eh, centered=False).translate((esp_x0 - PLUG_REACH, esp_y0, esp_z0))
solids["fan_psu_12v"] = cq.Workplane("XY").box(pl, pw, ph, centered=False).translate((10.0, board_y0, top_surface))
colors["fan_psu_12v"] = cq.Color(0.25, 0.25, 0.28)
plenum_top = CH - LID_PLATE
for name in ("esp32_poe", "fan_psu_12v", "controller_board"):
    bb = solids[name].val().BoundingBox()
    assert bb.zmax <= plenum_top, (f"{name} does not fit under the lid", round(bb.zmax, 1), plenum_top)
    assert bb.ymax < exhaust_y - bank_span / 2, f"{name} must sit ahead of the exhaust bank"
    assert abs(bb.xmin) <= CW / 2 and abs(bb.xmax) <= CW / 2, f"{name} outside the cabinet width"

for name, shape in solids.items():
    if name != "esp32_poe":
        blocked = sum(s.Volume() for s in plug_zone.intersect(shape).solids().vals())
        assert blocked < 1e-6, ("Ethernet plug blocked by", name, round(blocked, 3))
assert esp_x0 - PLUG_REACH >= -CW / 2 + WALL, "no room for the Ethernet plug inside the cabinet wall"

# --- Checks ---------------------------------------------------------------------------------------
for name, shape in solids.items():
    assert shape.val().isValid(), name
for (a, sa), (b, sb) in itertools.combinations(solids.items(), 2):
    common = sa.intersect(sb)
    vol = sum(s.Volume() for s in common.solids().vals())
    assert vol < 1e-6, ("collision", a, b, round(vol, 3))
intake_gap = FLOOR_GAP - GASKET - DEPTH  # free air under the intake bank, to the ground (before grill and filter)
plenum_gap = plenum_top - top_surface  # free air above the exhaust bank, under the lid

assembly = cq.Assembly(name="rack_cooling")
for name, shape in solids.items():
    assembly.add(shape, name=name, color=colors[name])
assembly.save(str(paths.ASSEMBLY_STEP))
bom = classify_assembly(assembly)
assert not bom["errors"], bom["errors"]

# --- Report ---------------------------------------------------------------------------------------
airflow = FAN.dim("airflow_max")
heat = next(p for p in FAN.provides if p["type"] == "cabinet-heat-removal")
derate = heat["derate"]
bank_airflow = FANS_PER_CHANNEL * airflow  # intake and exhaust in series: one bank's worth
real_airflow = bank_airflow * derate
fan_w = FAN.quantity * FAN.dim("power_max")
board_w = next(r["load"] for r in BOARD.requires if r["type"] == "dc-12v")
holes = []
for n, (u, v) in enumerate(bank_centres(), start=1):
    holes.append(
        {
            "fan": n,
            "centre_mm": [round(u, 2), round(v, 2)],
            "screw_holes_mm": [[round(u + sx * PITCH / 2, 2), round(v + sy * PITCH / 2, 2)] for sy in (1, -1) for sx in (-1, 1)],
        }
    )
report = {
    "status": "design; nothing bought. Positions follow the SysRacks SP 12.900 drawing; interior not measured.",
    "fan": {"part": FAN.id, "size_mm": SIZE, "depth_mm": DEPTH, "hole_pitch_mm": PITCH, "free_air_cfm": airflow},
    "bank": {
        "fans": FANS_PER_CHANNEL,
        "span_mm": round(bank_span, 2),
        "gap_mm": FAN_GAP,
        "cutout_pattern": "relative to the bank centre; u across (X), v toward the rear (Y); cutout diameter is illustrative",
        "fans_and_holes": holes,
        "intake": {"where": "under the floor, blowing up", "centre_y_mm": round(intake_y, 2),
                   "free_air_below_mm": round(intake_gap, 1), "wanted_mm": FREE_AIR_MIN,
                   "ok": intake_gap >= FREE_AIR_MIN},
        "exhaust": {"where": "under the inner top, blowing into the lid plenum", "centre_y_mm": round(exhaust_y, 2),
                    "free_air_above_mm": round(plenum_gap, 1), "wanted_mm": FREE_AIR_MIN,
                    "ok": plenum_gap >= FREE_AIR_MIN},
        "evidence": "cabinet outer dims from the SysRacks drawing; wall, lid and floor values assumed until measured",
    },
    "airflow": {
        "free_air_per_bank_cfm": round(bank_airflow, 1),
        "derate": derate,
        "estimated_cabinet_cfm": round(real_airflow, 1),
        "evidence": "allowance: free-air rating, series banks count once, derated for grilles and equipment",
        "heat_removal_w": {f"{dt}C_rise": round(real_airflow * dt / 1.76) for dt in (10, 15, 20)},
    },
    "electrical": {
        "fan_load_w": round(fan_w, 2),
        "controller_load_w": board_w,
        "total_12v_w": round(fan_w + board_w, 2),
        "supply_w": PSU.dim("rated_power"),
        "fans_per_pwm_channel": FANS_PER_CHANNEL,
    },
}
(OUT / "cooling-report.json").write_text(json.dumps(report, indent=2) + "\n")
print("cad: rack cooling assembly,", len(solids), "instances; estimated", round(real_airflow), "CFM;",
      report["airflow"]["heat_removal_w"], "| free air: intake", round(intake_gap, 1), "mm, exhaust", round(plenum_gap, 1),
      "mm, wanted", FREE_AIR_MIN)
