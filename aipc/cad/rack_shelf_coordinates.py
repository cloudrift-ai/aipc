"""Assembly datums for the Hammond RSUS1931BK1, in millimetres.

Component-local fabrication coordinates remain independent of placement.
Kenshin is built in its original local frame (I/O edge toward local +Y,
PCIe end toward local low X) and turned -90 degrees about Z on the deck: its rear I/O
and card brackets face the right (+X) shelf edge, its PCIe end faces the
rear, and its CPU end faces Berserk. The owner's 2026-11-16 mock-up photo
sets this topology; the exact offsets are CAD placements, not measurements.
"""

from hwkit import spec

_SHELF = spec.get('hammond-rsus1931bk1')
SHELF_W, SHELF_D, SHELF_T = _SHELF.dim('deck_width'), _SHELF.dim('deck_depth'), _SHELF.dim('sheet_thickness')
BERSERK_DX, BERSERK_DY = -24.0, 28.0
# Kenshin local (x, y) -> deck (y + K_TX, K_TY - x). K_TX puts the 25 mm rear
# motherboard rail flush with the right deck edge, so the rear I/O and the
# PCIe brackets (RTX 5090 and the ConnectX NIC) face the shelf's right side.
# K_TY is pinned by a front-to-rear chain with almost no slack: the V100 hood
# (Y405.7 at 24-pin height) -> Kenshin's 24-pin reserve, which overhangs the
# CPU-end PCB edge by 15 mm -> 305 mm PCB -> HX1200i (86 mm on its side) ->
# its bracket's rear M4 washer, which must stay 0.5 mm inside the deck rear.
KENSHIN_IO_LOCAL_Y, KENSHIN_RAIL_DEPTH = 624.5, 25.0
K_TX = SHELF_W - KENSHIN_RAIL_DEPTH - KENSHIN_IO_LOCAL_Y
K_TY = 731.78

BUILD_FORWARD_SHIFT = 52.5


def shelf_y(previous_station):
    return previous_station - BUILD_FORWARD_SHIFT


def k_xy(x, y):
    return y + K_TX, K_TY - x


def k_shape(shape):
    return shape.rotate((0, 0, 0), (0, 0, 1), -90).translate((K_TX, K_TY, 0))
