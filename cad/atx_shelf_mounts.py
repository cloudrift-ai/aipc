"""Two braced, interlocking ATX sections with port-safe outer shelf anchors.

Installed shelf coordinates. Full-depth drop-in dovetails locate X/Y, not Z.
Five independent shelf bolts retain each pair. GPU bases pass through the rail
and seat directly on steel. Under-PCB anchors go in before the motherboard.
"""
import cadquery as cq
import berserk_platform as bp
import pcie_post_hardware as post_hw

THICKNESS = 6.0
CLEARANCE = .3
SHELF_SLOT_LENGTH = 8.0
SHELF_TRAVEL = 2.0
BAR_WIDTH = 25.0
EAR_WIDTH = 14.0
EAR_OFFSET = 6.5
SHELF_SLOT_WIDTH = 4.0
WASHER_OD = 7.0
POST_SLOT_LENGTH, POST_SLOT_WIDTH = post_hw.OPENING_LENGTH, post_hw.OPENING_WIDTH
# Selected Kenshin openings align with the existing post axes at45/65.
# Other selectable positions retain their provisional survey coordinates.
POST_SLOT_X = (23.88, 45., 65., 84.52, 105.16, 125.16, 145.80, 165.80)
REAR_RAIL_CENTER_Y = 7.5  # keep the outer rail unchanged when locating holes
# ATX2.2 Fig3: mounting datum is10.16mm inside PCB rear edge.
# PCIe CEM2.0 Figs5-1/5-2/6-14: connector key is46.94mm inside that datum.
# Fig6-2: bracket outside flat face is59.05mm behind key -> PCB rear+1.95.
# Fig6-4:0.86mm sheet and5deg outward bend over5.07mm -> tip about+1.53..2.39.
# Use a1..3mm rear-edge groove for nominal fit; tolerance stack needs a dry fit.
ATX_REAR_MOUNT_DATUM = .4*25.4
PCIE_KEY_FROM_MOUNT_DATUM = 46.94
PCIE_BRACKET_FACE_FROM_KEY = 59.05
PCIE_BRACKET_OUTSIDE_Y = PCIE_BRACKET_FACE_FROM_KEY-PCIE_KEY_FROM_MOUNT_DATUM-ATX_REAR_MOUNT_DATUM
GPU_TAB_RELIEF_DEPTH = 2.0
GPU_TAB_GROOVE_WIDTH = 2.0
GPU_TAB_GROOVE_Y = 2.0  # nominal-fit allowance referenced to PCB edge, not posts
STANDOFF_EDGE_WEB = 4.0
# Eight selectable positions on one continuous rear rail, common to both boards.
# Current card layout populates all eight on Berserk and two on Kenshin.
# Post coordinates are survey estimates, not a standardized card-flange drawing.
SHARED_POST_X = {'Berserk': tuple(sorted(x+u-bp.X for x in bp.GPU_BODY_X.values() for u in (7,27))),
                 'Kenshin': (45., 65.)}
SHARED_POST_Y = {'Berserk': 6., 'Kenshin': 10.}


def shared_post_centers(system):
    x, y, _, d = BOARDS[system]
    return [(x+u, y+d+SHARED_POST_Y[system]) for u in SHARED_POST_X[system]]


def is_shared_post(system, x, y):
    return any(abs(x-u)<.001 and abs(y-v)<.001 for u,v in shared_post_centers(system))
SITES = {'A': (.65, .4), 'B': (3.75, .4), 'C': (5.55, .4), 'F': (11.75, 1.3),
         'G': (.65, 6.5), 'H': (5.55, 6.5), 'J': (11.75, 6.5),
         'K': (.65, 9.35), 'L': (5.55, 9.35), 'M': (11.75, 9.35)}
BOARDS = {'Berserk': (bp.X, bp.FRONT_Y, bp.WIDTH, bp.DEPTH), 'Kenshin': (6., 380.5, 305., 244.)}
# Group names preserve earlier job identities; anchor ends are now reversed.
GROUPS = {'front': ('A', 'B', 'C', 'G', 'K'), 'rear': ('F', 'H', 'J', 'L', 'M')}
LABELS = {'Berserk': {'front': 'right', 'rear': 'left'},
          'Kenshin': {'front': 'left', 'rear': 'right'}}
ANCHOR_ENDS = {'front': 'rear', 'rear': 'front'}
# ATX 2.01 Fig.3/4: aperture X148.488..307.238, shield margin2.54mm.
# Round X outward and use the ATX lower shield datum. Actual shrouds,
# plugs and cables are not dimensioned by that standard and need a dry fit.
IO_LOCAL_X = (145.0, 310.0)
IO_SERVICE_DEPTH = 40.0


def io_keepout(system):
    x, y, w, d = BOARDS[system]
    return {'system': system, 'x_range_mm': [x + IO_LOCAL_X[0], x + IO_LOCAL_X[1]],
            'y_range_mm': [y + d, y + d + IO_SERVICE_DEPTH], 'z_range_mm': [10.5466, 75],
            'basis': 'ATX2.01 Fig4: aperture bottom0.086+/-0.010in below PCB underside, plus0.100in shield margin; lowest standard shield Z10.5466 at PCB underside15.525. X rounded outward;40mm rear service depth and upperZ75 are provisional; actual plugs may project lower'}


def box(x0, x1, y0, y1):
    return cq.Workplane('XY').box(x1-x0, y1-y0, THICKNESS, centered=(False, False, False)).translate((x0, y0, 0))


def build(system):
    x0, y0, w, d = BOARDS[system]
    back = y0 + d
    holes = {k: (x0 + u*25.4, back - v*25.4) for k, (u, v) in SITES.items()}
    xa, ya = holes['A']; xc, _ = holes['C']; xf, yf = holes['F']
    _, yg = holes['G']; _, yk = holes['K']; split = x0 + 124
    # Use the same reference depth and anchor pattern for both 305x244-class boards.
    front_y = back-244.0
    post_x = SHARED_POST_X['Berserk'] if system == 'Berserk' else POST_SLOT_X
    post_slots = [(x0+u, back+SHARED_POST_Y[system]) for u in post_x]
    assert all(any(abs(px-x)<.001 and abs(py-y)<.001 for x,y in post_slots)
               for px,py in shared_post_centers(system)), (system,'post must be centered in hex hole')
    anchors = {'front': [(x0+u, back-13) for u in (54.2,110.0)] + [(x0+110.0, yk+3)],
               'rear': [(x0+218, front_y-EAR_OFFSET),(x0+297, front_y-EAR_OFFSET)]}
    # Optional anchors oppose each section's primary ears; matching side slots
    # provide another simple attachment choice without adding more ears.
    optional = {'front': [(x0+54.2, yk+3), (xa+3.5, (ya+yg)/2)],
                'rear': [(x0+218, yf-3), (x0+260, yf-3), (xf-3.5, (yf+yg)/2)]}
    front = box(xa-9, xc+BAR_WIDTH/2, ya+9.5-BAR_WIDTH, ya+9.5)
    front = front.union(box(xa-9, xa-9+BAR_WIDTH, yk-9.5, ya+9.5))
    for low in (yk-9.5, yg-BAR_WIDTH/2):
        front = front.union(box(xa-9, split, low, low+BAR_WIDTH))
    rear = box(split+CLEARANCE, xf+9, yk-9.5, yk-9.5+BAR_WIDTH)
    rear = rear.union(box(split+CLEARANCE, xf+9, yg-BAR_WIDTH/2, yg+BAR_WIDTH/2))
    rear = rear.union(box(xc-BAR_WIDTH/2, xc+BAR_WIDTH/2, yk-9.5, yg+30-CLEARANCE))
    rear = rear.union(box(xf+9-BAR_WIDTH, xf+9, yk-9.5, yf+9.5))
    rear = rear.union(box(x0+218-BAR_WIDTH/2, xf+9, yf+9.5-BAR_WIDTH, yf+9.5))
    front = front.union(box(xc-BAR_WIDTH/2, xc+BAR_WIDTH/2, yg+30, ya+9.5))
    rear = rear.union(box(x0+218-BAR_WIDTH/2, x0+218+BAR_WIDTH/2, yg-BAR_WIDTH/2, yf+9.5))
    shapes = {'front': front, 'rear': rear}
    # One broad 25mm-deep rear rail contains every selectable PCIe post slot.
    # Its last two positions enter the conservative I/O service projection;
    # the 6mm rail sits below the modeled PCB, but actual shield clearance
    # and populated-post locations must be checked on the fitted hardware.
    shapes['front'] = shapes['front'].union(box(min(xa-9,post_slots[0][0]-EAR_WIDTH/2), max(xc+BAR_WIDTH/2,post_slots[-1][0]+EAR_WIDTH/2),
                                               back+REAR_RAIL_CENTER_Y+9-BAR_WIDTH,
                                               back+REAR_RAIL_CENTER_Y+9))
    for x,y in anchors['rear']:
        shapes['rear'] = shapes['rear'].union(box(x-EAR_WIDTH/2,x+EAR_WIDTH/2,
                                                  y-8,yk-9.5+BAR_WIDTH))
    joints = []

    def joint(cx, cy, axis):
        # 10mm neck /16mm head /8mm engagement, full6mm thickness.
        # The third key turns90 degrees and closes the C-to-H rail.
        local = [(-4,-5), (0,-5), (8,-8), (8,8), (0,5), (-4,5)]
        pts = [(cx+u, cy+v) if axis == 'X' else (cx+v, cy-u) for u,v in local]
        wire = cq.Workplane('XY').polyline(pts).close()
        male = wire.extrude(THICKNESS)
        socket = wire.wires().toPending().offset2D(CLEARANCE).extrude(THICKNESS)
        shapes['front'] = shapes['front'].union(male)
        shapes['rear'] = shapes['rear'].cut(socket)
        joints.append({'center_xy_mm': [cx, cy], 'engagement_mm': 8, 'neck_mm': 10, 'head_mm': 16,
                       'clearance_per_side_mm': CLEARANCE, 'locates_axes': ['X','Y'],
                       'key_axis': axis, 'insertion_axis': 'Z'})

    for cy in (yk+3, yg):
        joint(split, cy, 'X')
    joint(xc, yg+30, 'Y')
    result = {}
    for group, s in shapes.items():
        sites = GROUPS[group]
        slot_width = SHELF_SLOT_WIDTH
        washer_od = WASHER_OD
        for site in sites:
            x, y = holes[site]
            for length, width, height in ((6.,3.7,6.), (10.8,8.5,3.)):
                s = s.cut(cq.Workplane('XY').center(x,y).slot2D(length,width,90).extrude(height))
        if group == 'front':
            for x,y in post_slots:
                # A true six-sided hole with0.15mm clearance per face.
                # The user requested a snug fit, removing slot adjustment.
                s = s.cut(cq.Workplane('XY').polyline(post_hw.opening_points()).close()
                          .extrude(THICKNESS).translate((x,y,0)))
        for points,length,width in ((anchors[group],SHELF_SLOT_LENGTH,slot_width),
                                    (optional[group],SHELF_SLOT_LENGTH,SHELF_SLOT_WIDTH)):
            for x,y in points:
                s = s.cut(cq.Workplane('XY').center(x,y).slot2D(length,width,90).extrude(THICKNESS))
        relief = None
        if group == 'front':
            inner_y = back + GPU_TAB_GROOVE_Y - GPU_TAB_GROOVE_WIDTH/2
            outer_y = back + GPU_TAB_GROOVE_Y + GPU_TAB_GROOVE_WIDTH/2
            bb = s.val().BoundingBox()
            # A narrow rectangular groove keeps the original print orientation:
            # its walls start on the bed and the roof bridges only 2 mm at Z2.
            cutter = (cq.Workplane('XY')
                      .box(bb.xlen+2, GPU_TAB_GROOVE_WIDTH, GPU_TAB_RELIEF_DEPTH+1,
                           centered=(False, False, False))
                      .translate((bb.xmin-1, inner_y, THICKNESS-GPU_TAB_RELIEF_DEPTH)))
            # Keep the full thickness around every selectable board screw,
            # including optional B. Do not trade a seated GPU for a weak land.
            lands = []
            for site in sites:
                x, y = holes[site]
                land = (cq.Workplane('XY').center(x, y)
                        .slot2D(6+2*STANDOFF_EDGE_WEB, 3.7+2*STANDOFF_EDGE_WEB, 90)
                        .extrude(THICKNESS))
                lands.append(land)
            # Through-bases carry no load into plastic, so no washer lands
            # interrupt the groove. Point the hex tips toward the PCB:
            # Berserk tips meet the groove without a0.1mm unprintable web;
            # Kenshin's farther-back holes stay separate from the groove.
            original = s.val()
            s = s.cut(cutter)
            assert original.Volume()-s.val().Volume() > 100, (system, 'missing GPU tab relief')
            for land in lands:
                assert original.intersect(land.val()).cut(s.val()).Volume() < .01, (system, 'standoff land')
            assert THICKNESS-GPU_TAB_RELIEF_DEPTH >= 4
            # Each inter-post gap must actually open down to the requested
            # floor, including the region beyond the PCB where tongues land.
            for (lx, _), (rx, _) in zip(post_slots, post_slots[1:]):
                probe = (cq.Workplane('XY').center((lx+rx)/2, back+GPU_TAB_GROOVE_Y)
                         .rect(4, GPU_TAB_GROOVE_WIDTH-.02).extrude(GPU_TAB_RELIEF_DEPTH-.02)
                         .translate((0, 0, THICKNESS-GPU_TAB_RELIEF_DEPTH+.01)))
                assert s.val().intersect(probe.val()).Volume() < .01, (system, 'GPU tab gap')
            relief = {'type': 'narrow rectangular groove',
                      'depth_mm': GPU_TAB_RELIEF_DEPTH, 'width_mm': GPU_TAB_GROOVE_WIDTH,
                      'remaining_base_thickness_mm': THICKNESS-GPU_TAB_RELIEF_DEPTH,
                      'installed_y_range_mm': [inner_y, outer_y],
                      'y_range_relative_to_PCB_rear_mm': [inner_y-back, outer_y-back],
                      'standard_bracket_outside_face_relative_to_PCB_rear_mm': PCIE_BRACKET_OUTSIDE_Y,
                      'standard_datum_chain_mm': {'key_to_bracket_outside_face': PCIE_BRACKET_FACE_FROM_KEY,
                                                  'mount_datum_to_key': PCIE_KEY_FROM_MOUNT_DATUM,
                                                  'PCB_rear_to_mount_datum': ATX_REAR_MOUNT_DATUM},
                      'standoff_slot_edge_web_mm': STANDOFF_EDGE_WEB,
                      'standoff_lands_preserved': True,
                      'intersects_post_clearance_slots': back+SHARED_POST_Y[system]-POST_SLOT_LENGTH/2 < outer_y,
                      'print_orientation': 'original: installed top on bed, screw-head recesses up',
                      'print_bridge_span_mm': GPU_TAB_GROOVE_WIDTH, 'supports_required': False,
                      'basis': 'ATX2.2 Fig3 and PCIe CEM2.0 Figs5-1/5-2/6-2/6-14 give nominal bracket outside face59.05-46.94-10.16=1.95mm behind PCB rear. Fig6-4 specifies0.86mm sheet and5deg+/-2deg outward tongue bend over5.07mm, giving nominal tip about1.53..2.39mm behind PCB. Groove1..3mm is a nominal-fit design allowance, not guaranteed full tolerance coverage; depth2mm requested by owner. Actual hardware fit remains unmeasured',
                      'sources': ['https://analytika.sk/fileadmin/user_upload/developer_specs_atx2_2.PDF#page=12',
                                  'https://tecsmith.github.io/homeassistant-pc-switch/specs/pci-express-card-electromechanical-specification-revision-2.pdf#page=85'],
                      'physical_fit_verified': False,
                      'fit_check': 'Measure seated tab X/Y/Z; check tongues against metal bases and steel deck; print one of each rear rail and dry-fit before use'}
        for x, y in anchors[group]:
            if group == 'rear':
                assert y+SHELF_TRAVEL+washer_od/2 <= y0
            else:
                assert y0 <= y-SHELF_TRAVEL-washer_od/2 and y+SHELF_TRAVEL+washer_od/2 <= back
                # A complete 4mm web surrounds each independent anchor,
                # including the underside around board screw counterbores.
                web=(cq.Workplane('XY').center(x,y).slot2D(16,12,90).extrude(THICKNESS)
                     .cut(cq.Workplane('XY').center(x,y).slot2D(8,4,90).extrude(THICKNESS)))
                assert web.val().cut(s.val()).Volume()<.01,(system,'anchor edge web',x,y)
        assert s.val().isValid() and len(s.solids().vals()) == 1, (system,group)
        bb = s.val().BoundingBox()
        label = f'{system.lower()}_mobo_adapter_{LABELS[system][group]}_drill_plan'
        result[label] = {'shape': s, 'print_shape': s.translate((-bb.xmin,-bb.ymin,0)),
                         'origin': (bb.xmin,bb.ymin), 'sites': sites,
                         'hole_centers': {site: holes[site] for site in sites}, 'anchors': anchors[group],
                         'optional_anchors': optional[group], 'anchor_end': ANCHOR_ENDS[group],
                         'through_post_centers': shared_post_centers(system) if group == 'front' else [],
                         'post_slots': post_slots if group == 'front' else [],
                         'rear_rail_depth_mm': BAR_WIDTH if group == 'front' else None,
                         'gpu_tab_relief': relief,
                         'post_slots_are_selectable': True,
                         'standalone_anchors': anchors[group],
                         'install_anchors_before_PCB': group == 'front',
                         'post_slot_mm': [POST_SLOT_LENGTH,POST_SLOT_WIDTH],
                         'post_opening': post_hw.opening_spec(),
                         'interchangeable_with': ('Kenshin' if system == 'Berserk' else 'Berserk') if group == 'rear' else None,
                         'shelf_slot_mm':[8.,slot_width], 'shelf_fastener':'M3',
                         'top_washer_od_mm':washer_od, 'backing_washer_od_mm':WASHER_OD,
                         'shelf_hole_diameter_mm':3.5,
                         'bar_width_mm':BAR_WIDTH,'ear_width_mm':EAR_WIDTH,
                         'bounds': [bb.xmin,bb.ymin,bb.xmax,bb.ymax]}
    a, b = [v['shape'].val() for v in result.values()]
    assert a.intersect(b).Volume() < .01, (system, 'overlapping sections')
    assert a.distance(b) >= CLEARANCE-.001
    return result, joints
