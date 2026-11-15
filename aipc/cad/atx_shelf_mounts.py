"""AIPC placement of the shared two-section ATX mount (hwkit.components.atx_mobo_mount).

Installed shelf coordinates. Berserk and Kenshin each sit on one pair of
sections; Kenshin's pair is turned 180 degrees. The section geometry, joints
and post slots live in hwkit so other builds can place the same parts.
"""
import berserk_platform as bp
from hwkit.components import atx_mobo_mount as mount
from hwkit.components.atx_mobo_mount import (ANCHOR_ENDS, GROUPS, POST_SLOT_LENGTH, POST_SLOT_WIDTH,  # noqa: F401
                                             SITES, THICKNESS)
from rack_shelf_coordinates import k_xy, k_shape

# Selected Kenshin openings align with the existing post axes at45/65.
# Other selectable positions retain their provisional survey coordinates.
POST_SLOT_X = (23.88, 45., 65., 84.52, 105.16, 125.16, 145.80, 165.80)
# Eight selectable positions on one continuous rear rail, common to both boards.
# Current card layout populates all eight on Berserk and two on Kenshin.
# Post coordinates are survey estimates, not a standardized card-flange drawing.
SHARED_POST_X = {'Berserk': tuple(sorted(x+u-bp.X for x in bp.GPU_BODY_X.values() for u in (7,27))),
                 'Kenshin': (45., 65.)}
SHARED_POST_Y = {'Berserk': 6., 'Kenshin': 10.}


def shared_post_centers(system, *, installed=True):
    x, y, _, d = BOARDS[system]
    points = [(x+u, y+d+SHARED_POST_Y[system]) for u in SHARED_POST_X[system]]
    return [k_xy(*p) for p in points] if system == 'Kenshin' and installed else points


def is_shared_post(system, x, y):
    return any(abs(x-u)<.001 and abs(y-v)<.001 for u,v in shared_post_centers(system))
BOARDS = {'Berserk': (bp.X, bp.FRONT_Y, bp.WIDTH, bp.DEPTH), 'Kenshin': (6., 380.5, 305., 244.)}
LABELS = {'Berserk': {'front': 'right', 'rear': 'left'},
          'Kenshin': {'front': 'left', 'rear': 'right'}}
# ATX 2.01 Fig.3/4: aperture X148.488..307.238, shield margin2.54mm.
# Round X outward and use the ATX lower shield datum. Actual shrouds,
# plugs and cables are not dimensioned by that standard and need a dry fit.
IO_LOCAL_X = (145.0, 310.0)
IO_SERVICE_DEPTH = 40.0


def io_keepout(system):
    x, y, w, d = BOARDS[system]
    result = {'system': system, 'x_range_mm': [x + IO_LOCAL_X[0], x + IO_LOCAL_X[1]],
            'y_range_mm': [y + d, y + d + IO_SERVICE_DEPTH], 'z_range_mm': [10.5466, 75],
            'basis': 'ATX2.01 Fig4: aperture bottom0.086+/-0.010in below PCB underside, plus0.100in shield margin; lowest standard shield Z10.5466 at PCB underside15.525. X rounded outward;40mm rear service depth and upperZ75 are provisional; actual plugs may project lower'}
    if system == 'Kenshin':
        corners = [k_xy(a,b) for a,b in zip(result['x_range_mm'], result['y_range_mm'])]
        result['x_range_mm'] = sorted(p[0] for p in corners)
        result['y_range_mm'] = sorted(p[1] for p in corners)
    return result


def build(system):
    x0, y0, w, d = BOARDS[system]
    post_x = SHARED_POST_X['Berserk'] if system == 'Berserk' else POST_SLOT_X
    groups, joints = mount.build(system, x0, y0, w, d, post_x, SHARED_POST_Y[system])
    assert all(any(abs(px-x)<.001 and abs(py-y)<.001 for x,y in groups['front']['post_slots'])
               for px,py in shared_post_centers(system, installed=False)), (system,'post must be centered in hex hole')
    result = {}
    for group, frame in groups.items():
        frame['through_post_centers'] = shared_post_centers(system, installed=False) if group == 'front' else []
        frame['interchangeable_with'] = ('Kenshin' if system == 'Berserk' else 'Berserk') if group == 'rear' else None
        result[f'{system.lower()}_mobo_adapter_{LABELS[system][group]}_drill_plan'] = frame
    if system == 'Kenshin':
        for frame in result.values():
            # Preserve the already-normalized print geometry; only installation turns.
            frame['shape'] = k_shape(frame['shape'])
            bb = frame['shape'].val().BoundingBox()
            frame['origin'] = (bb.xmin, bb.ymin)
            frame['bounds'] = [bb.xmin, bb.ymin, bb.xmax, bb.ymax]
            frame['rotation_about_Z_deg'] = 180
            frame['hole_centers'] = {site: k_xy(*p) for site,p in frame['hole_centers'].items()}
            for field in ('anchors', 'standalone_anchors', 'optional_anchors', 'through_post_centers', 'post_slots'):
                frame[field] = [k_xy(*p) for p in frame[field]]
            frame['anchor_end'] = 'front' if frame['anchor_end'] == 'rear' else 'rear'
            if frame['gpu_tab_relief']:
                frame['gpu_tab_relief']['installed_y_range_mm'] = sorted(k_xy(0,y)[1] for y in frame['gpu_tab_relief']['installed_y_range_mm'])
                frame['gpu_tab_relief']['rear_direction_in_shelf_Y'] = -1
        for joint in joints:
            joint['center_xy_mm'] = k_xy(*joint['center_xy_mm'])
    return result, joints
