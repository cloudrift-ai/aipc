"""Hammond RSUS1931BK1 dimensional envelope, not manufacturer CAD.

The current family table controls rating/depth range; the older individual
drawing disagrees on those two values. Undimensioned rail internals, bend
radii and screw patterns are deliberately not represented as measured parts.
"""
import json
import cadquery as cq

from aipc import spec

_P = spec.get('hammond-rsus1931bk1')  # parts/purchased/hammond-rsus1931bk1/part.toml
MODEL = 'Hammond RSUS1931BK1'
SOURCE = _P.datasheets[0]['url']
DRAWING = _P.datasheets[1]['url']
SIDE_HEIGHT, OVERALL_HEIGHT = _P.dim('fold_height'), _P.dim('overall_height')
OVERALL_WIDTH, RACK_HOLE_PITCH = _P.dim('overall_width'), _P.dim('rack_hole_pitch')
TRAVEL = _P.dim('slide_travel')
MOUNT_DEPTH_RANGE = (_P.dim('mount_depth_min'), _P.dim('mount_depth_max'))
RATING_KG = _P.dim('load_rating')


def box(w,d,h,x,y,z):
    return cq.Workplane('XY').box(w,d,h,centered=(False,False,False)).translate((x,y,z))


def envelope_parts(width, depth, thickness):
    # Published front view and isometric show folds below the deck. Internal
    # radius and steel thickness are provisional. Simple straight webs retain
    # the published outer envelope without inventing a vent or mounting pattern.
    shapes = {
        'Hammond_left_downward_fold': box(thickness,depth,SIDE_HEIGHT-thickness,0,0,-SIDE_HEIGHT),
        'Hammond_right_downward_fold': box(thickness,depth,SIDE_HEIGHT-thickness,width-thickness,0,-SIDE_HEIGHT),
        'Hammond_front_downward_fold': box(width-2*thickness,thickness,SIDE_HEIGHT-thickness,thickness,0,-SIDE_HEIGHT),
        'Hammond_rear_downward_fold': box(width-2*thickness,thickness,SIDE_HEIGHT-thickness,thickness,depth-thickness,-SIDE_HEIGHT),
    }
    # Outer slide bars are illustrative keepouts outside the deck width.
    # TRAVEL is sourced; closed bar length and cross-section are not.
    # Drawing top view (scale reading): front bracket flange flush with the deck
    # front; at the 28 in rail distance the rear bracket sits ~3 in short of the
    # deck rear. Closed slide length is not dimensioned; drawing scale gives ~28 in.
    rail_length, rail_depth, rail_height = _P.dim('slide_closed_length'), 12.5, 30.0
    rail_y = _P.dim('front_bracket_setback')
    margin = (OVERALL_WIDTH-width)/2
    for side,x in (('left',-rail_depth),('right',width)):
        shapes[f'Hammond_{side}_factory_slide_envelope'] = box(rail_depth,rail_length,rail_height,x,rail_y,-34)
        bx = -margin if side == 'left' else width+rail_depth
        for end,y in (('front',rail_y),('rear',rail_y+MOUNT_DEPTH_RANGE[1])):
            shapes[f'Hammond_{side}_{end}_rack_bracket_envelope'] = box(margin-rail_depth,2,OVERALL_HEIGHT,bx,y,-58)
    return shapes


def add_to_assembly(assembly,width,depth,thickness,out):
    shapes = envelope_parts(width,depth,thickness)
    existing=[(name,shape.moved(loc)) for shape,name,loc,_ in assembly]
    checks=0
    def overlaps(a,b):
        return all(getattr(a,k+'min') < getattr(b,k+'max')-1e-6 and
                   getattr(a,k+'max') > getattr(b,k+'min')+1e-6 for k in 'xyz')
    # Include all explicit underside fasteners, not only the component boxes.
    for name,shape in shapes.items():
        for other_name,other in existing:
            if overlaps(shape.val().BoundingBox(),other.BoundingBox()):
                assert shape.val().intersect(other).Volume()<.01,(name,other_name,'factory shelf envelope')
                checks+=1
    # Conservative continuous sweep against stationary outer rail/bracket
    # envelopes. Roof duct and external cables must be disconnected first.
    motion_checks=0
    for name,shape in shapes.items():
        if 'fold' in name: continue
        for other_name,other in existing:
            if any(term in other_name.lower() for term in ('roof','ceiling','duct','survey_segment')): continue
            b=other.BoundingBox()
            swept=box(b.xlen,b.ylen+TRAVEL,b.zlen,b.xmin,b.ymin-TRAVEL,b.zmin).val()
            if overlaps(shape.val().BoundingBox(),swept.BoundingBox()):
                assert shape.val().intersect(swept).Volume()<.01,(name,other_name,'travel envelope')
                motion_checks+=1
    for name,shape in shapes.items():
        assert shape.val().isValid()
        assembly.add(shape,name=name,color=cq.Color(.24,.27,.30))
    report = {
        'shelf': MODEL, 'source': SOURCE, 'drawing': DRAWING,
        'deck_width_depth_mm': [width,depth],
        'nominal_gauge_thickness_mm': thickness,
        'thickness_basis': '16 gauge from current series page; 1.52 mm nominal allowance, actual sheet and coating unmeasured',
        'fold_height_mm': SIDE_HEIGHT, 'overall_height_mm': OVERALL_HEIGHT,
        'overall_width_mm': OVERALL_WIDTH, 'rack_hole_pitch_mm': RACK_HOLE_PITCH,
        'mount_depth_range_mm': MOUNT_DEPTH_RANGE, 'slide_travel_mm': TRAVEL,
        'equipment_load_limit_kg': RATING_KG,
        'mounting_space_U': 2, 'required_clearance_U': 3,
        'specification_disagreement': 'Individual drawing says 120 lb and 8–28 in; current series table says 85 lb (39 kg) and 18–28 in. Use the current, more restrictive values pending manufacturer confirmation.',
        'status': 'selected by owner; not purchased or physically fitted',
        'factory_slide_internal_geometry_verified': False,
        'physical_fit_verified': False,
        'static_boolean_pairs_checked':checks,
        'continuous_travel_envelope_pairs_checked':motion_checks,
        'travel_check_scope':'Illustrative outer rails and brackets only; actual bearings, stops, rack posts, doors and moving-load capacity unmeasured. Disconnect fixed-rack duct, power and data before extension.',
        'custom_rail_shims': 'none; factory matched slides replace the King Slide adaptation',
        'limitations': 'Deck outer dimensions are sourced. Bend radii, true flat bearing area, slide closed length/cross-section, rack-bracket locations and holes are illustrative. Do not drill using factory slide envelopes. Survey underside hardware clearance, rack spacing, door clearance and total moving load before fabrication.',
    }
    (out/'hammond-shelf-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
