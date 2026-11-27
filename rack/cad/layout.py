"""Cabinet cooling: two 2 x 2 banks of 200 mm fans, the ESP32 controller and its 12 V supply.

Run with ``hwkit cad`` (``make cad BUILD=rack``). Builds the assembly, exports the
library models this build owns and writes models/cooling-report.json with the
fan-bank cutout pattern, the electrical totals and the heat-removal estimate.

The cabinet is not identified, so the banks sit on provisional planes: the intake
bank low on the front plane (Y = 0) blowing toward the rear, the exhaust bank on a
roof plane blowing up. Move them with INTAKE_* and ROOF_* once the cabinet is
measured. Every fan dimension comes from the part spec.

Coordinates (mm): X across the cabinet from its centre line, Y from the front plane
toward the rear, Z up from the cabinet floor.
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
ESP = spec.get("espressif-esp32-devkitc-32e")
PSU = spec.get("meanwell-gst60a12-p1j")
BOARD = spec.get("rack-fan-controller-board")
PROBE = spec.get("ds18b20-waterproof-probe")

# Layout allowances (provisional until the cabinet is measured).
FAN_GAP = 5.0  # between adjacent frames in a bank, room for the anti-vibration pads
BANK = 2  # fans per row and per column
INTAKE_Z0 = 100.0  # bottom of the intake bank above the cabinet floor: PROVISIONAL
ROOF_Z = 1200.0  # roof plane under the exhaust bank: PROVISIONAL
ROOF_Y0 = 300.0  # front edge of the exhaust bank behind the front plane: PROVISIONAL
PROBE_OFFSET = 60.0  # probe tip distance from its bank, in the airstream
FAN_MOUNT_HOLE = 4.5  # illustrative; the frame hole diameter is not published
ROTOR_CUT = SIZE - 10.0  # illustrative rotor area; the bore diameter is not published
HUB = 80.0  # illustrative hub

FANS_PER_CHANNEL = BANK * BANK
assert FAN.quantity == 2 * FANS_PER_CHANNEL, ("fan quantity must fill both banks", FAN.quantity)
assert PITCH < SIZE, "hole pitch must lie inside the frame"
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
    """Fan centres in the bank plane, relative to the bank centre, row by row."""
    step = SIZE + FAN_GAP
    offs = [(i - (BANK - 1) / 2) * step for i in range(BANK)]
    return [(u, v) for v in reversed(offs) for u in offs]


FAN_SHAPE = fan_model()
bank_span = BANK * SIZE + (BANK - 1) * FAN_GAP
solids: dict[str, cq.Workplane] = {}
colors: dict[str, cq.Color] = {}

# Intake bank: vertical on the front plane, blowing +Y. The fan's local Z (airflow) maps to +Y.
intake_centre_z = INTAKE_Z0 + bank_span / 2
for n, (u, v) in enumerate(bank_centres(), start=1):
    shape = FAN_SHAPE.rotate((0, 0, 0), (1, 0, 0), -90).translate((u, 0, intake_centre_z + v))
    solids[f"intake_fan_{n}"] = shape
    colors[f"intake_fan_{n}"] = cq.Color(0.35, 0.55, 0.85)

# Exhaust bank: horizontal under the roof plane, blowing +Z.
roof_centre_y = ROOF_Y0 + bank_span / 2
for n, (u, v) in enumerate(bank_centres(), start=1):
    shape = FAN_SHAPE.translate((u, roof_centre_y + v, ROOF_Z - DEPTH))
    solids[f"exhaust_fan_{n}"] = shape
    colors[f"exhaust_fan_{n}"] = cq.Color(0.85, 0.45, 0.25)

# Probes: tubes along the airflow, one in each bank's stream.
tube_d, tube_l = PROBE.dim("tube_diameter"), PROBE.dim("tube_length")
solids["intake_probe"] = (
    cq.Workplane("XZ").circle(tube_d / 2).extrude(-tube_l).translate((0, DEPTH + PROBE_OFFSET, intake_centre_z))
)
solids["exhaust_probe"] = (
    cq.Workplane("XY").circle(tube_d / 2).extrude(tube_l).translate((0, roof_centre_y, ROOF_Z - DEPTH - PROBE_OFFSET - tube_l))
)
for name in ("intake_probe", "exhaust_probe"):
    colors[name] = cq.Color(0.8, 0.8, 0.82)

# Controller board, DevKitC and supply beside the exhaust bank, under the roof (PROVISIONAL).
bx, by, bh = BOARD.dim("board_width"), BOARD.dim("board_depth"), BOARD.dim("height")
board_x0 = bank_span / 2 + 40.0
board_y0 = ROOF_Y0
board_z0 = ROOF_Z - 60.0 - bh
solids["controller_board"] = cq.Workplane("XY").box(bx, by, 1.6, centered=False).translate((board_x0, board_y0, board_z0))
colors["controller_board"] = cq.Color(0.2, 0.55, 0.3)
ew = ESP.dim("board_width")
el = ESP.dim("board_length") + ESP.dim("antenna_overhang")
solids["esp32_devkitc"] = (
    cq.Workplane("XY").box(el, ew, 12.0, centered=False).translate((board_x0 + 10.0, board_y0 + 10.0, board_z0 + 1.6 + 8.0))
)
colors["esp32_devkitc"] = cq.Color(0.15, 0.15, 0.18)
pl, pw, ph = PSU.dim("length"), PSU.dim("width"), PSU.dim("height")
solids["fan_psu_12v"] = cq.Workplane("XY").box(pl, pw, ph, centered=False).translate((board_x0, board_y0 + by + 30.0, board_z0))
colors["fan_psu_12v"] = cq.Color(0.25, 0.25, 0.28)

# --- Checks ---------------------------------------------------------------------------------------
for name, shape in solids.items():
    assert shape.val().isValid(), name
for (a, sa), (b, sb) in itertools.combinations(solids.items(), 2):
    common = sa.intersect(sb)
    vol = sum(s.Volume() for s in common.solids().vals())
    assert vol < 1e-6, ("collision", a, b, round(vol, 3))
assert INTAKE_Z0 + bank_span < ROOF_Z - DEPTH - PROBE_OFFSET - tube_l, "intake bank must sit below the exhaust bank and its probe"

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
    "status": "design; nothing bought. Fan bank positions are provisional until the cabinet is identified.",
    "fan": {"part": FAN.id, "size_mm": SIZE, "depth_mm": DEPTH, "hole_pitch_mm": PITCH, "free_air_cfm": airflow},
    "bank": {
        "fans": FANS_PER_CHANNEL,
        "span_mm": round(bank_span, 2),
        "gap_mm": FAN_GAP,
        "cutout_pattern": "relative to the bank centre; u across, v up (intake) or toward the rear (exhaust)",
        "fans_and_holes": holes,
        "intake_plane": {"y_mm": 0.0, "bottom_z_mm": INTAKE_Z0, "evidence": "allowance"},
        "exhaust_plane": {"z_mm": ROOF_Z, "front_y_mm": ROOF_Y0, "evidence": "allowance"},
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
      report["airflow"]["heat_removal_w"])
