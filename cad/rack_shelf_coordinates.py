"""Assembly datums for the Hammond RSUS1931BK1, in millimetres.

Component-local fabrication coordinates remain independent of placement.
Kenshin is turned 180 degrees in the deck plane: its I/O faces the center
service corridor and its GPU occupies the high-X side of the deeper tray.
"""

SHELF_W, SHELF_D, SHELF_T = 16.64 * 25.4, 31.0 * 25.4, 1.52
BERSERK_DX, BERSERK_DY = -24.0, 28.0
K_XSUM, K_YSUM = SHELF_W, 1071.0

BUILD_FORWARD_SHIFT = 52.5


def shelf_y(previous_station):
    return previous_station - BUILD_FORWARD_SHIFT


def k_xy(x, y):
    return K_XSUM-x, K_YSUM-y


def k_shape(shape):
    return shape.rotate((0, 0, 0), (0, 0, 1), 180).translate((K_XSUM, K_YSUM, 0))
