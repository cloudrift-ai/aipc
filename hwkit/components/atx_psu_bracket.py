"""Printed rear restraint for an ATX PSU lying on its side (designed for AIPC).

Intel ATX12V guide figure 12-1: retain only the two upper #6-32 rear-face
threads for lateral restraint. PSU weight rests directly on the steel shelf;
the lower frame is a continuous rail instead of two awkward screw pads. The
150 mm face direction is vertical, the 86 mm one across the shelf. A 30 mm foot
behind the face carries two side-by-side M4 shelf slots.

``bracket()`` returns the print shape (PSU face on the bed). ``installed()``
stands it on the shelf behind a PSU rear face. The library model
``psu_bracket`` is exported by AIPC; other builds compare with it.
"""

import cadquery as cq

PSU_REAR_HOLES_LOCAL_XZ = ((80, 144), (6, 120))  # two upper ATX rear-face screws: local X, height
BERSERK_LED_CENTER = (80.0, 60.0)  # local X, distance down from PSU top; photo estimate
BERSERK_LED_RELIEF_WH = (9.0, 40.0)
BERSERK_LED_BYPASS_X = 92.5  # only local LED bypass extends past86mm PSU width
BERSERK_LED_OUTER_WEB = BERSERK_LED_BYPASS_X - BERSERK_LED_CENTER[0] - BERSERK_LED_RELIEF_WH[0] / 2
SHELF_ANCHORS = ((31.0, 19.0), (55.0, 19.0))  # local X, depth behind the PSU face
FOOT_REACH = 30.0
SLOT_LENGTH, SLOT_WIDTH = 10.0, 5.5  # M4, front-to-rear adjustment
FACE_HEIGHT = 150.0


def shelf_slot_xz(x: float, depth: float, y_offset: float = 0):
    """Slot in a vertical print plane that lies along shelf Y after rotation."""
    return cq.Workplane("XZ").center(x, depth).slot2D(SLOT_LENGTH, SLOT_WIDTH, 90).extrude(-6).translate((0, y_offset, 0))


def bracket(*, berserk=False):
    """Compact rear restraint: face on bed, two side-by-side shelf slots.

    PSU weight remains on steel. Berserk uses an8mm top bar within the
    PSU outline; owner reports >10mm from PSU top to power connector.
    """
    frame = cq.Workplane("XY").box(86, 150, 9, centered=(False, False, False))
    window_top = 8 if berserk else 12
    window = (
        cq.Workplane("XY").box(62, 138 - window_top, 9, centered=(False, False, False)).translate((12, window_top, 0)).edges("|Z").fillet(4)
    )
    frame = frame.cut(window)
    if berserk:
        bypass = (
            cq.Workplane("XY")
            .polyline([(74, 30), (86, 30), (BERSERK_LED_BYPASS_X, 40), (BERSERK_LED_BYPASS_X, 80), (86, 90), (74, 90)])
            .close()
            .extrude(9)
        )
        led_relief = cq.Workplane("XY").center(*BERSERK_LED_CENTER).slot2D(40, 9, 90).extrude(9)
        # Open the relief to the main window; no fragile1.5mm inner strip.
        opening = cq.Workplane("XY").box(6, 40, 9, centered=(False, False, False)).translate((74, 40, 0))
        frame = frame.union(bypass).cut(led_relief.union(opening))
        assert BERSERK_LED_OUTER_WEB == 8
    for x, z in PSU_REAR_HOLES_LOCAL_XZ:
        frame = frame.cut(cq.Workplane("XY").center(x, 150 - z).slot2D(5, 4, 90).extrude(9))
    foot = cq.Workplane("XY").box(50, 6, FOOT_REACH, centered=(False, False, False)).translate((18, 144, 0))
    for gx in (18, 64):
        foot = foot.union(cq.Workplane("YZ").polyline(((126, 0), (150, 0), (144, 30))).close().extrude(4).translate((gx, 0, 0)))
    frame = frame.union(foot)
    for x, depth in SHELF_ANCHORS:
        frame = frame.cut(shelf_slot_xz(x, depth, 144))
    assert frame.val().isValid() and len(frame.solids().vals()) == 1
    assert frame.val().BoundingBox().ylen <= 150.0001
    return frame


def installed(print_shape: cq.Workplane, x0: float, face_y: float):
    """Stand the print shape behind a PSU rear face at Y = ``face_y``, PSU toward -Y.

    (print X, Y, Z) -> (shelf x0 + X, face_y + Z, 150 - Y). Turn the result
    180 degrees about Z for a PSU whose rear face points toward -Y.
    """
    return print_shape.rotate((0, 0, 0), (1, 0, 0), -90).translate((x0, face_y, FACE_HEIGHT))


# --- Printing (shared by every build that prints the bracket) -------------------------------------
PRINT_NOTE = "broad rear frame face flat on bed; compact foot and gussets grow upward; HT-PLA-GF with0.4mm hardened nozzle"
PROCESS = "printer:ht-pla-gf-psu.json"
FILAMENT = "printer:polymaker-ht-pla-gf-230c.json"
NOZZLE = "0.4mm hardened steel"
