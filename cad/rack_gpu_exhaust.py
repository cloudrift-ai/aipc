"""Removable flex duct to the Sysracks inner ceiling, not its outer lid.

The owner permits a reasonable provisional roof height and an adjustable flex
route. No cabinet CAD or physical hose geometry is implied. Dimensions mm.
"""
import json
import math
import cadquery as cq
import tilted_gpu_cooling as cooling

TRANSITION='gpu_exhaust_fan_flange'
ROOF='gpu_exhaust_roof_flange'
CX=cooling.CX
_,FAN_Y,FAN_Z=cooling.point(0,0,cooling.PANEL+cooling.FAN_DEPTH)
FAN_PLATE,FAN_NECK,FAN_W,FAN_PITCH=10.,28.,160.,124.5
SPIGOT_OD,BORE=151.5,145.5
HOSE_ID,HOSE_OD=152.4,154.4
CEILING_Z,CEILING_T,GASKET_T=400.,1.2,2.
ROOF_W,ROOF_T,ROOF_NECK,ROOF_ANCHOR=176.,6.,40.,78.
BEND_R,STRAIGHT=150.,40.
HOSE_START_Y=FAN_Y+(FAN_PLATE+1)*cooling.S
HOSE_START_Z=FAN_Z+(FAN_PLATE+1)*cooling.S
BEND_START_Y=HOSE_START_Y+STRAIGHT*cooling.S
BEND_START_Z=HOSE_START_Z+STRAIGHT*cooling.S
ROOF_Y=BEND_START_Y+BEND_R*(1-cooling.S)
BEND_END_Z=BEND_START_Z+BEND_R*cooling.S
HOSE_TOP_Z=CEILING_Z-GASKET_T-ROOF_T-4
CLAMP_WIDTH,CLAMP_T=22.225,.889
CLAMP_LINK='https://www.mcmaster.com/53185K52/'
CLAMP_PRICE=21.92


def normalize(s):
    b=s.val().BoundingBox()
    return s.translate((-b.xmin,-b.ymin,-b.zmin))


def flange_local(roof=False):
    width,plate,neck=(ROOF_W,ROOF_T,ROOF_NECK) if roof else (FAN_W,FAN_PLATE,FAN_NECK)
    opening=cq.Workplane('XY').circle(BORE/2).extrude(plate)
    if not roof:
        # Keep the opening inside the 140 mm fan face, matching its recommended
        # 138 mm panel boundary. A full round bore leaks at the four side edges.
        opening=opening.intersect(cq.Workplane('XY').rect(138,138).extrude(plate))
    shape=cq.Workplane('XY').rect(width,width).extrude(plate).cut(opening)
    shape=shape.union(cq.Workplane('XY',origin=(0,0,plate)).circle(SPIGOT_OD/2).circle(BORE/2).extrude(neck))
    pitch=2*ROOF_ANCHOR if roof else FAN_PITCH
    for x in (-pitch/2,pitch/2):
        for y in (-pitch/2,pitch/2):
            cutter=cq.Workplane('XY').center(x,y)
            cutter=cutter.slot2D(8,5.5,90) if roof else cutter.circle(2.25)
            shape=shape.cut(cutter.extrude(plate))
            if not roof:shape=shape.cut(cooling.pocket_cut(x,y,plate-cooling.NUT_POCKET[2]))
    assert shape.val().isValid() and len(shape.solids().vals())==1
    return shape


def print_parts():
    return {TRANSITION:normalize(flange_local()),ROOF:normalize(flange_local(True))}


def fan_place(s):
    return cooling.place(s.translate((0,0,cooling.PANEL+cooling.FAN_DEPTH)))


def hose_path_points(count=30):
    import numpy as np
    theta=np.linspace(-math.pi/4,0,count)
    cy=BEND_START_Y-BEND_R*cooling.S
    cz=BEND_START_Z+BEND_R*cooling.S
    return ([HOSE_START_Y]+list(cy+BEND_R*np.cos(theta))+[ROOF_Y],
            [HOSE_START_Z]+list(cz+BEND_R*np.sin(theta))+[HOSE_TOP_Z])


def hose_shape():
    cy=BEND_START_Y-BEND_R*cooling.S;cz=BEND_START_Z+BEND_R*cooling.S
    path=(cq.Workplane('YZ',origin=(CX,0,0)).moveTo(HOSE_START_Y,HOSE_START_Z)
          .lineTo(BEND_START_Y,BEND_START_Z)
          .threePointArc((cy+BEND_R*math.cos(math.pi/8),cz-BEND_R*math.sin(math.pi/8)),
                         (ROOF_Y,BEND_END_Z))
          .lineTo(ROOF_Y,HOSE_TOP_Z).wire())
    plane=cq.Plane(origin=(CX,HOSE_START_Y,HOSE_START_Z),xDir=(1,0,0),normal=(0,cooling.S,cooling.S))
    return cq.Workplane(plane).circle(HOSE_OD/2).circle(HOSE_ID/2).sweep(path,isFrenet=True)


def clamp_local(neck_start,neck_length):
    center=neck_start+neck_length/2
    ring=(cq.Workplane('XY',origin=(0,0,center-CLAMP_WIDTH/2)).circle(HOSE_OD/2+CLAMP_T)
          .circle(HOSE_OD/2).extrude(CLAMP_WIDTH))
    lever=cq.Workplane('XY').box(36,15,12).translate((0,-HOSE_OD/2-6,center))
    return ring.union(lever)


def bolt_local(plate,flange_thickness=4.,washer_od=9.):
    # Head outside the printed plate, nut/second washer behind mating flange.
    top=plate+1
    shaft=cq.Workplane('XY',origin=(0,0,top-20)).circle(2).extrude(20)
    head=cq.Workplane('XY',origin=(0,0,top)).circle(4).extrude(3)
    washer=cq.Workplane('XY',origin=(0,0,plate)).circle(washer_od/2).circle(2.25).extrude(1)
    washer2=cq.Workplane('XY',origin=(0,0,-flange_thickness-1)).circle(washer_od/2).circle(2.25).extrude(1)
    nut=cq.Workplane('XY',origin=(0,0,-flange_thickness-4.2)).polygon(6,7/(3**.5/2)).circle(2).extrude(3.2)
    return shaft.union(head).union(washer).union(washer2).union(nut)


def installed():
    roof=lambda s:s.rotate((0,0,0),(1,0,0),180).translate((CX,ROOF_Y,CEILING_Z-GASKET_T))
    shapes={TRANSITION:fan_place(flange_local()),ROOF:roof(flange_local(True)),
            'flex_duct_6in_ADJUSTABLE_ROUTE':hose_shape(),
            '53185K52_fan_clamp_envelope':fan_place(clamp_local(FAN_PLATE,FAN_NECK)),
            '53185K52_roof_clamp_envelope':roof(clamp_local(ROOF_T,ROOF_NECK))}
    for name,z,w,h in [('inner_ceiling_patch_PROVISIONAL',CEILING_Z,226,CEILING_T),
                       ('roof_silicone_gasket',CEILING_Z-GASKET_T,176,GASKET_T)]:
        s=cq.Workplane('XY',origin=(CX,ROOF_Y,z)).rect(w,w).circle(77).extrude(h)
        for x in (-ROOF_ANCHOR,ROOF_ANCHOR):
            for y in (-ROOF_ANCHOR,ROOF_ANCHOR):
                s=s.cut(cq.Workplane('XY',origin=(CX+x,ROOF_Y+y,z)).circle(2.75).extrude(h))
        shapes[name]=s
    for x in (-FAN_PITCH/2,FAN_PITCH/2):
        for y in (-FAN_PITCH/2,FAN_PITCH/2):
            # Insert from open fan corner into the externally loaded T-nut.
            shaft=cq.Workplane('XY',origin=(x,y,-5)).circle(2).extrude(16)
            head=cq.Workplane('XY',origin=(x,y,-9)).circle(4).extrude(4)
            washer=cq.Workplane('XY',origin=(x,y,-5)).circle(4.5).circle(2.25).extrude(1)
            nut=cooling.nut(x,y,FAN_PLATE-cooling.NUT_POCKET[2])
            shapes[f'fan_outlet_M4_{x}_{y}']=fan_place(shaft.union(head).union(washer).union(nut))
    for x in (-ROOF_ANCHOR,ROOF_ANCHOR):
        for y in (-ROOF_ANCHOR,ROOF_ANCHOR):
            shapes[f'roof_M4_{x}_{y}']=roof(bolt_local(ROOF_T,CEILING_T+GASKET_T,12).translate((x,y,0)))
    return shapes


def integrate(assembly,parts,connectors,out):
    shapes=installed();collisions=[];keepout=[]
    for name in (TRANSITION,ROOF):
        for p in parts+connectors:
            v=shapes[name].val().intersect(p.shape().val()).Volume()
            if v>.1:
                record={'part':name,'component':p.name,'volume_mm3':round(v,2)}
                (keepout if p in connectors else collisions).append(record)
    assert not collisions,collisions
    for name,s in shapes.items():
        color=(.36,.75,.76) if name in (TRANSITION,ROOF) else (.60,.64,.68,.18) if 'duct' in name else (.45,.48,.52,.3) if 'ceiling' in name else (.65,.66,.68)
        assembly.add(s,name=name,color=cq.Color(*color))
    report={
      'status':'45-degree adjustable duct-route study; rigid flange interfaces require dry fit',
      'material':'Polymaker HT-PLA-GF, hardened0.4mm nozzle,230C/50C; recheck after annealing',
      'ceiling_height_above_shelf_mm':CEILING_Z,'roof_center_xy_mm':[CX,ROOF_Y],
      'route':'existing V100 extraction fan -> short straight flange -> adjustable6in flex bend -> inner-ceiling chamber',
      'layout':'GPU inlet fixed; fan and outlet tilt upward45 degrees; PC positions retained',
      'rack_space':'tilted fan topZ233.44 and duct require reserved volume toZ400 above shelf; not a self-contained6U unit',
      'flex_route':'owner authorizes schematic component overlaps; reshape hose around actual components, do not force rigid parts or obstruct fan inlets. Centerline is a planning curve, not an installation jig.',
      'bend_radius_mm_schematic':BEND_R,'hose_nominal_id_mm':HOSE_ID,'hose_OD_mm_provisional':HOSE_OD,
      'modeled_centerline_length_mm':round(STRAIGHT+math.pi*BEND_R/4+HOSE_TOP_Z-BEND_END_Z,1),
      'purchase_length':'one1m length of6in wire-supported ventilation hose; trim after test fit; seller/pack pending',
      'fan_flange':{'face_mm':FAN_PLATE,'neck_mm':FAN_NECK,'plate_opening':'intersection of centered 138 mm square and diameter 145.5 mm circle; stays inside the 140 mm fan face; seal mating seam','hole_pitch_mm':FAN_PITCH,'clearance_holes_mm':4.5,'pockets_mm':cooling.NUT_POCKET,'nut_dimensions_provisional':True,'back_to_neck_end_y_mm':FAN_Y+(FAN_PLATE+FAN_NECK)*cooling.S,'print':'flat face on bed, neck up, no supports','hardware':'4 M4x16,4 M4 hammer T-nuts,4 OD9x1washers; bench mount before hose; test job13 coupon first'},
      'roof_flange':{'face_mm':ROOF_T,'neck_mm':ROOF_NECK,'square_mm':ROOF_W,'hole_centers_xy_mm':[[CX+x,ROOF_Y+y]for x in(-78,78)for y in(-78,78)],'slots_mm':[8,5.5],'roof_hole_mm':154,'gasket_mm':2,'sheet_thickness_mm_provisional':1.2,'hardware':'4M4x20,4nuts,8OD12x1washers; resize for actual ceiling stack'},
      'spigot_od_bore_mm':[SPIGOT_OD,BORE],
      'clamps':{'part':'McMaster53185K52','quantity':2,'unit_price_usd':CLAMP_PRICE,'price_date':'2026-10-17','url':CLAMP_LINK,'range_mm':[152,159],'band_width_mm':CLAMP_WIDTH,'geometry':'published band width/thickness; estimated latch; not manufacturerCAD','fit':'measure installed hoseOD; center band on28mm fan neck with2.89mm margin each end; do not crush3mm HT-PLA-GF wall'},
      'release':'support hose, open both lever clamps, ease cuffs off necks and flex the loop free. Preserve service slack; no rigid axial-slide clearance claim.',
      'support':'owned strap to rack near roof carries hose weight; keep tension off fan and PCB',
      'roof_work':'inner ceiling only, not outer lid; survey factory fans, wiring, ribs, baffles and roof-channel outlet area before drilling/cutting',
      'known_component_intersections':collisions,'provisional_cable_reserve_intersections':keepout,
      'cable_fit_condition':'tilted rigid fan/flange clear the modeled24-pin reserve; confirm actual header, latch and cable routing during dry fit',
      'airflow':'not calculated from free-air rating; qualify actual GPU and printed-part temperatures, roof restriction/backflow and seal leakage under load. Roof fanidentity/curve unconfirmed.',
    }
    (out/'gpu-exhaust-report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report,shapes


def preview(path,shapes,parts):
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.patches import Rectangle,Polygon
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb
    plenum,_,_=cooling.parts()
    hardware,_=cooling.hardware()
    shown={**shapes,**{k:v for k,v in hardware.items() if 'driver' not in k},'fan':cooling.fan(),'shroud':plenum}
    detail=cq.Assembly(name='V100_45_degree_exhaust_fit_prototype')
    for name,shape in shown.items():
        color=(.23,.73,.75) if name in(TRANSITION,ROOF,'shroud') else (.25,.28,.31,.2) if 'duct' in name else (.35,.37,.4)
        detail.add(shape,name=name,color=cq.Color(*color))
    detail.save(str(path.with_name('v100-tilted-exhaust.step')))
    fig=plt.figure(figsize=(14,8));ax=fig.add_subplot(121,projection='3d')
    def mesh(s):
        vs,ts=s.val().tessellate(.8);v=np.array([[q.x,q.y,q.z]for q in vs]);return v[np.array(ts)]
    for name,s in shown.items():
        if '_M4_' in name:continue
        c='#52aeb8' if name in(TRANSITION,ROOF,'shroud') else '#e29c40' if 'clamp' in name else '#67727e'
        faces=mesh(s)
        normals=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
        normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
        light=np.array([.3,-.5,.8]);light/=np.linalg.norm(light)
        shades=.48+.52*np.abs(normals@light)
        colors=np.array(to_rgb(c))[None,:]*shades[:,None]
        ax.add_collection3d(Poly3DCollection(faces,facecolors=colors,edgecolors='none',alpha=.16 if 'duct' in name or 'ceiling' in name else 1))
    ax.set(xlim=(110,360),ylim=(250,570),zlim=(0,425));ax.set_box_aspect((250,320,425));ax.view_init(elev=20,azim=-55)
    ax.set(xlabel='X',ylabel='Rearward Y',zlabel='Height Z');ax.set_title('Fan tilted upward; removable flexible hose')
    ax=fig.add_subplot(122)
    for y,z,w,h,label in [(47.5,24,266.7,111.15,'V100 cards'),(380.5,15.525,244,1.6,'Kenshin board'),(380.5,14,74,58,'24-pin reserve')]:
        ax.add_patch(Rectangle((y,z),w,h,fc='#bac5cf',ec='#87939e',alpha=.35))
        ax.text(max(y+5,210),z+h+5,label,fontsize=8)
    for name in ('shroud','fan',TRANSITION,ROOF):
        faces=mesh(shown[name])[:,:,[1,2]]
        u=faces[:,1]-faces[:,0];v=faces[:,2]-faces[:,0]
        area=np.abs(u[:,0]*v[:,1]-u[:,1]*v[:,0])
        ax.add_collection(PolyCollection(faces[area>1e-6],facecolors='#55aeb9' if name!='fan' else '#4d565e',edgecolors='none'))
    ys,zs=hose_path_points()
    ax.plot(ys,zs,color='#268a99',lw=22,alpha=.15);ax.plot(ys,zs,color='#268a99',ls='--')
    ax.axhline(CEILING_Z,color='#333',lw=2);ax.text(420,408,'Inner ceiling Z400 (provisional)',ha='center',fontsize=9)
    ax.axhline(222.25,color='#b36b12',ls='--');ax.text(545,226,'6U shelf envelope',ha='center',fontsize=8)
    ax.annotate('45° outlet',xy=(380,190),xytext=(475,165),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.annotate('Shelf-mounted\nhood',xy=(341,6),xytext=(255,55),ha='center',arrowprops={'arrowstyle':'->'},fontsize=9)
    ax.set(xlim=(200,640),ylim=(0,430),xlabel='Front → rear Y (mm)',ylabel='Above steel shelf Z (mm)');ax.set_aspect('equal')
    ax.set_title('Side projection; hose centerline adjustable')
    fig.suptitle('45° GPU exhaust — HT-PLA-GF / hardened 0.4 mm nozzle',fontsize=15)
    fig.text(.5,.025,'Fan top Z233.44 uses reserved upper duct volume. Roof, nut pockets and physical hardware need a dry fit.',ha='center',fontsize=10)
    fig.subplots_adjust(top=.9,bottom=.11,wspace=.22);fig.savefig(path,dpi=150);plt.close(fig)
