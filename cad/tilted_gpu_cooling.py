"""45-degree V100 extraction module. Dimensions are a fit prototype, in mm.

One broad hood covers the rear GPU array and bolts directly to the steel shelf. T-nut pockets use a
conservative 2020 hammer-nut envelope, not measured Sutemribor dimensions.
"""
import math
from functools import lru_cache
import cadquery as cq
import berserk_platform as bp

CX, WIDTH = bp.GPU_CENTER, 173.32
X0 = CX - WIDTH/2
CY, CZ, ANGLE = 325.0, 150.0, 45.0
HEIGHT, PANEL, WALL = 148.0, 10.0, 3.2
# Four nominal40mm GPU bodies follow H12D SLOT_PLANES minus36mm and Z24..135.15.
# Plain sidewalls cover the rear120.2mm; no fitted collar or individual rod cuts.
GPU_END_Y, FIT_GAP = 314.2, 1.5
INLET_Y, INLET_BOTTOM, INLET_TOP = 194.0, 0.0, 145.0
BASE_Y, BASE_END_Y, BASE_T = 333.0, 363.0, 6.0
BASE_TOE_Y = BASE_Y + BASE_T  # One straight inlet edge;45deg underside bevel.
RIB_T = 4.0
RIB_X = tuple(CX + x for x in (-65.0,-25.0,25.0,65.0))
FAN_SIZE, FAN_DEPTH, FAN_FLANGE, PITCH = 140.0,38.0,4.0,124.5
ANCHORS=((CX-55.0,347.0),(CX+55.0,347.0),(CX,352.5))
SLOT_LENGTH, SLOT_WIDTH = 8.0,5.5
NUT_BODY=(11.5,5.7,4.2)
NUT_POCKET=(12.2,6.4,4.8)
NUT_SOURCE='https://www.amazon.ae/Sutemribor-Hammer-Fastener-Aluminum-Profile/dp/B07FPLZXTF'
NUT_REFERENCE='https://www.motedis.com/shop/products_files/Motedis_S6BHASNM4-Drawing.pdf'
JOINT_X=()  # Integral fan panel: no plenum-to-base joint.
S=math.sqrt(.5)


def place(shape):
    # Local XY is the fan face, Z is airflow; upper local Y points front/up.
    return shape.rotate((0,0,0),(1,0,0),-45).translate((CX,CY,CZ))


def point(x,v,t=0):return [CX+x,CY-S*v+S*t,CZ+S*v+S*t]


def normalize(shape):
    b=shape.val().BoundingBox();return shape.translate((-b.xmin,-b.ymin,-b.zmin))


def face_down(shape):
    # Fan-facing surface down, turned90deg to center the long side on bed X.
    # Four integral chamber ribs carry the shelf-base transition during printing.
    s=shape.translate((-CX,-CY,-CZ)).rotate((0,0,0),(1,0,0),45)
    return normalize(s.rotate((0,0,0),(1,0,0),180).rotate((0,0,0),(0,0,1),90))


def fan_envelope():
    return place(cq.Workplane('XY').rect(140,140).extrude(FAN_DEPTH).translate((0,0,PANEL)))


def fan():
    opening=cq.Workplane('XY').rect(138,138).extrude(4).intersect(cq.Workplane('XY').circle(73.5).extrude(4))
    f=cq.Workplane('XY').rect(140,140).extrude(4).cut(opening)
    for x in (-PITCH/2,PITCH/2):
        for y in (-PITCH/2,PITCH/2):f=f.cut(cq.Workplane('XY').center(x,y).circle(2.25).extrude(4))
    barrel=cq.Workplane('XY').circle(70).circle(67).extrude(FAN_DEPTH)
    return place(f.union(f.translate((0,0,FAN_DEPTH-4))).union(barrel).translate((0,0,PANEL)))


def pocket_cut(x,y,from_t=0):
    return cq.Workplane('XY',origin=(x,y,from_t)).rect(*NUT_POCKET[:2]).extrude(NUT_POCKET[2])


def nut(x,y,t=0.6):
    return (cq.Workplane('XY',origin=(x,y,t)).rect(*NUT_BODY[:2]).extrude(NUT_BODY[2])
            .cut(cq.Workplane('XY',origin=(x,y,t)).circle(2).extrude(NUT_BODY[2])))


def prism(points,x,width):
    return cq.Workplane('YZ',origin=(x,0,0)).polyline(points).close().extrude(width)


@lru_cache(None)
def parts():
    # A single five-sided outline governs all exterior walls. The fan panel
    # reaches this outline, removing the former roof lips and panel-end steps.
    _,yb,zb=point(0,-HEIGHT/2,PANEL)
    _,yt,zt=point(0,HEIGHT/2,PANEL)
    outer=[(INLET_Y,INLET_TOP),(BASE_TOE_Y,0),
           (BASE_END_Y,0),(yb,zb),(yt,zt)]
    envelope=prism(outer,X0,WIDTH)
    shell=prism(outer,X0,WALL).union(prism(outer,X0+WIDTH-WALL,WALL))
    roof_drop=WALL*math.sqrt(1+((zt-INLET_TOP)/(yt-INLET_Y))**2)
    roof=[(INLET_Y,INLET_TOP),(yt,zt),(yt,zt-roof_drop),
          (INLET_Y,INLET_TOP-roof_drop)]
    floor_shift=WALL*math.sqrt(1+((yb-BASE_END_Y)/zb)**2)
    floor=[(BASE_END_Y,0),(yb,zb),(yb-floor_shift,zb),
           (BASE_END_Y-floor_shift,0)]
    shell=shell.union(prism(roof,X0,WIDTH)).union(prism(floor,X0,WIDTH))
    # The front bevel is continuous with the mouth; no short vertical toe/notch.
    base=prism([(BASE_Y,BASE_T),(BASE_TOE_Y,0),
                (BASE_END_Y,0),(BASE_END_Y,BASE_T)],X0,WIDTH)
    shell=shell.union(base)
    # Four permanent broad triangular ribs grow from the rear wall toward the
    # shelf flange. They avoid the bolt/washer/driver lanes and stay in chamber.
    rib=[(344,6),(365,6),(375,60)]
    for x in RIB_X:
        shell=shell.union(prism(rib,x-RIB_T/2,RIB_T))
    panel=cq.Workplane('XY').rect(WIDTH,HEIGHT).extrude(PANEL)
    shell=shell.union(place(panel)).intersect(envelope)
    opening=(cq.Workplane('XY').rect(138,138).extrude(PANEL+2*WALL)
             .intersect(cq.Workplane('XY').circle(73.5).extrude(PANEL+2*WALL))
             .translate((0,0,-2*WALL)))
    shell=shell.cut(place(opening))
    for x in (-PITCH/2,PITCH/2):
        for y in (-PITCH/2,PITCH/2):
            shell=shell.cut(place(cq.Workplane('XY').center(x,y).circle(2.25).extrude(PANEL)))
            shell=shell.cut(place(pocket_cut(x,y)))
    for x,y in ANCHORS:
        shell=shell.cut(cq.Workplane('XY').center(x,y).slot2D(SLOT_LENGTH,SLOT_WIDTH,90).extrude(BASE_T))
    shell=shell.clean()
    post_slots=[]  # All eight rods remain inside the broad open mouth.
    coupon=cq.Workplane('XY').box(24,22,10,centered=(False,False,False))
    coupon=coupon.cut(pocket_cut(12,11,5.2)).cut(cq.Workplane('XY').center(12,11).circle(2.25).extrude(10))
    for name,shape in [('shroud',shell),('coupon',coupon)]:
        assert shape.val().isValid() and len(shape.solids().vals())==1,(name,len(shape.solids().vals()))
    return shell,coupon,post_slots


def hardware():
    out={};records=[]
    for x in (-PITCH/2,PITCH/2):
        for v in (-PITCH/2,PITCH/2):
            # M4x14 from the open fan corner toward a back-loaded rectangular nut.
            seat=PANEL+FAN_FLANGE+1
            shaft=cq.Workplane('XY',origin=(x,v,seat-14)).circle(2).extrude(14)
            head=cq.Workplane('XY',origin=(x,v,seat)).circle(4).extrude(4)
            washer=cq.Workplane('XY',origin=(x,v,seat-1)).circle(4.5).circle(2.25).extrude(1)
            out[f'inlet_M4_{x}_{v}']=place(shaft.union(head).union(washer).union(nut(x,v)))
            # A long 3 mm hex bit passes through the corresponding outlet hole.
            out[f'inlet_driver_{x}_{v}']=place(cq.Workplane('XY',origin=(x,v,seat+4)).circle(1.5).extrude(40))
            records.append({'center_mm':point(x,v,PANEL),'axis':[0,S,S], 'fastener':'M4x14 socket-cap screw, OD9x1 washer, M4 2020 hammer T-nut','pocket_mm':list(NUT_POCKET),'pocket_backing_mm':PANEL-NUT_POCKET[2],'nut_dimensions_provisional':True})
    return out,records


def print_parts():
    shell,coupon,_=parts()
    return {'v100_gpu_shroud':face_down(shell),'v100_screw_fit_sample':coupon}


def report():
    b=fan_envelope().val().BoundingBox()
    return {'status':'one broad rear-array hood with three internal shelf anchors; fit prototype',
      'fan_selected':'Sanyo Denki 9GV1412P1S001','fan_body_mm':[140,140,38],
      'fan_hole_pitch_mm':PITCH,'fan_hole_diameter_mm':4.5,
      'fan_dimension_source':'https://publish.sanyodenki.com/San_Ace_E/book/data/San_Ace_E.pdf pp185-188',
      'angle_up_from_horizontal_deg':45,'panel_center_xyz_mm':[CX,CY,CZ],
      'fan_top_z_mm':round(b.zmax,2),'rack_space':'fan reaches above nominal6U shelf envelope; keep existing duct space to inner ceilingZ400 clear',
      'GPU_inlet_y_mm':INLET_Y,'outer_width_mm':WIDTH,
      'rear_GPU_coverage_mm':GPU_END_Y-INLET_Y,'side_body_clearance_mm':2.5,
      'base_y_range_mm':[BASE_Y,BASE_END_Y],'base_thickness_mm':BASE_T,
      'base_ground_y_range_mm':[BASE_TOE_Y,BASE_END_Y],'base_front_bevel_deg':45,
      'permanent_ribs':{'count':4,'thickness_mm':RIB_T,'centers_x_mm':RIB_X,
                        'purpose':'support the shelf-flange transition in print; retain inside chamber'},
      'adapter_rail_gap_mm':BASE_Y-330.7,'individual_rod_cutouts':0,
      'support':'continuous sidewalls into6mm base; three M4 shelf bolts carry fan and hood; flex duct separately supported',
      'inlet_edge_yz_mm':[[INLET_Y,INLET_TOP],[BASE_TOE_Y,0]],
      'shelf_slot_size_mm':[SLOT_LENGTH,SLOT_WIDTH],'shelf_slot_checked_travel_mm':[-1.25,1.25],
      'shelf_hardware':'3 M4x16 bolts,3 nuts,6 OD12x1 steel washers; verify actual stack',
      'rear_IO_fit':'high-X sidewall requires dry fit against Berserk rear ports and any fitted shield; exact bodies unmeasured',
      'fan_panel_mm':PANEL,'plenum_wall_mm':WALL,'shelf_anchors_xy_mm':ANCHORS,
      'material':'Polymaker HT-PLA-GF; 0.4mm hardened steel nozzle;230C nozzle/50C bed',
      'nut':'M4 2020 hammer T-nut; rectangular back-loaded pocket; no extra cap',
      'nut_body_reference_mm':NUT_BODY,'nut_pocket_mm':NUT_POCKET,
      'nut_reference_drawing':NUT_REFERENCE,'selected_nut_link':NUT_SOURCE,
      'nut_fit':'selected Sutemribor dimensions unverified; print job13 nut coupon first; 12.2x6.4x4.8 pocket is provisional',
      'inlet_hardware':'4 M4x14 socket-cap screws,4 M4 T-nuts,4 OD9x1 washers; clamp only inlet flange',
      'joint_hardware':'none; fan panel is integral with shroud',
      'assembly_order':'fit-test nut coupon; load four fan nuts; tighten Kenshin front motherboard anchors first; lower bare hood over rear array; fix three internal M4 shelf bolts through open fan aperture using long driver, before fan/duct; seal common inlet/underside with secured nonconductive flexible gasket; install fan then separately supported duct',
      'print_orientation':'integral fan face down, rotated90deg in XY; four permanent tapered chamber ribs; no removable supports in job11',
      'seal':'broad secured flexible nonconductive foam/tape skirt across common lower opening and front/side perimeter; keep GPU vents open and exclude PCB contacts; seal all bypasses before thermal testing',
      'airflow':'four V100 heatsinks to common plenum, pull fan, flexible duct and inner-ceiling chamber; actual pressure/flow and temperatures require load testing',
      'fan_rated_current_A':3.1,'fan_rated_power_W':37.2,'fan_free_air_CFM':272,'fan_shutoff_pressure_Pa':480,'fan_full_speed_noise_dBA':67,
      'ratings_limit':'free-air and shutoff endpoints are not operating airflow; no thermal qualification yet',
      'thermal_verified':False,'physical_fit_verified':False,
      'anneal':'see saved manufacturer TDS; check dimensions after annealing; unloaded heat stability is not a loaded bracket rating'}
