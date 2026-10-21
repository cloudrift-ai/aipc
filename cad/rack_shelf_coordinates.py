"""Shared placement offset for the open shelf assembly (millimetres).

The steel shelf stays at Y=0..700. Earlier design stations are translated
toward the rack front; printable part-local coordinates are not translated.
"""

BUILD_FORWARD_SHIFT = 52.5


def shelf_y(previous_station):
    return previous_station - BUILD_FORWARD_SHIFT
