"""Purchased GPU post base; millimetres, with explicit evidence boundaries."""
from math import sqrt

BASE_PART = '970140324'
BASE_HEIGHT = 14.0
BASE_AF = 5.5
BASE_THREAD_LENGTH = 14.0
BASE_DRAWING = 'https://www.we-online.com/components/products/datasheet/970140324.pdf'
BASE_PRODUCT = 'https://www.digikey.com/en/products/detail/w%C3%BCrth-elektronik/970140324/9488563'
# Owner-reported on 2026-10-23; not a dimension from the OBT product page.
OBT_STUD_LENGTH = 9.0
BOTTOM_SCREW_LENGTH = 6.0
BACKER_T = 1.0
SMALL_WASHER_T = .5
BODY_FACE_CLEARANCE = .15
BASE_ROTATION_DEG = 30
BASE_ORIENTATION = 'one hex corner points toward PCB (opposite flats parallel Y); hold with wrench, not plastic'
OPENING_AF = BASE_AF + 2*BODY_FACE_CLEARANCE
OPENING_LENGTH = 2*OPENING_AF/sqrt(3)
OPENING_WIDTH = OPENING_AF


def base_hex_points(clearance=0):
    """Regular hex with vertices along Y; clearance is normal to each face."""
    radius = (BASE_AF + 2*clearance)/sqrt(3)
    half_flat = (BASE_AF + 2*clearance)/2
    return [(half_flat,radius/2), (0,radius), (-half_flat,radius/2),
            (-half_flat,-radius/2), (0,-radius), (half_flat,-radius/2)]


def opening_points():
    """Snug regular hex only; no additional adjustment sweep."""
    return base_hex_points(BODY_FACE_CLEARANCE)


def opening_spec():
    return {'profile': 'regular hexagon', 'sides': 6,
            'across_flats_mm': OPENING_AF, 'across_corners_mm': OPENING_LENGTH,
            'length_Y_mm': OPENING_LENGTH, 'width_X_mm': OPENING_WIDTH,
            'clearance_per_hex_face_mm': BODY_FACE_CLEARANCE,
            'designed_adjustment_mm': {'X': 0, 'Y': 0},
            'fit': 'snug design allowance; actual printed fit unverified',
            'required_base_orientation': BASE_ORIENTATION,
            'arbitrary_base_rotation_allowed': False,
            'physical_fit_verified': False}


def thread_stack(shelf_thickness):
    engagement = BOTTOM_SCREW_LENGTH - shelf_thickness - BACKER_T - SMALL_WASHER_T
    gap = BASE_HEIGHT - OBT_STUD_LENGTH - engagement
    assert engagement >= 3.0, 'M3 lower screw needs at least 3mm nominal engagement'
    assert gap >= 1.0, 'opposed screw tips need at least 1mm nominal clearance'
    assert BASE_THREAD_LENGTH >= OBT_STUD_LENGTH
    return {'base_part': BASE_PART, 'base_height_mm': BASE_HEIGHT,
            'base_across_flats_mm': BASE_AF, 'internal_thread_length_mm': BASE_THREAD_LENGTH,
            'manufacturer_drawing': BASE_DRAWING, 'purchase_link': BASE_PRODUCT,
            'OBT_stud_length_mm': OBT_STUD_LENGTH,
            'OBT_stud_basis': 'owner-reported 2026-10-23; tolerance not measured',
            'bottom_screw': 'M3x6', 'shelf_thickness_nominal_mm': shelf_thickness,
            'nominal_lower_thread_engagement_mm': round(engagement, 3),
            'nominal_tip_clearance_mm': round(gap, 3),
            'physical_fit_verified': False}
