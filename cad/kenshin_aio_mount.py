"""Rear 360 mm AIO: front-style bearing frames and a matching inward brace.

Only the radiator/fan pitch and frame envelope adapt to the smaller fan size.
Fastener diameters and structural thicknesses are retained, not scaled down.
Factory interfaces and the right-end hose envelope remain provisional.
"""
import cadquery as cq
import berserk_aio_brace as front_brace

FRAME_X = (43.0, 283.0)
FRAME_W, FRAME_H, FRAME_T = 120.0, 140.0, 6.0
FOOT_X, FOOT_W, REACH = 12.0, 96.0, 40.0
ANCHORS = ((22.0, 28.0), (98.0, 28.0))
LEDGE_W, LEDGE_D = 64.0, 27.5
RADIATOR_Z = (27.5, 132.5)
BRACE_PART = "fan120_aio_hose_brace"
BRACE_HEIGHT, BRACE_X0 = 142.0, 377.75


def frame():
    """120 mm fan-flush face above the 20 mm bearing; print broad face down."""
    result = cq.Workplane("XY").box(FRAME_W, FRAME_H, FRAME_T,
                                     centered=(False, False, False))
    result = result.cut(cq.Workplane("XY").center(60, 80).circle(55).extrude(FRAME_T))
    for x in (7.5, 112.5):
        for z in RADIATOR_Z:
            result = result.cut(cq.Workplane("XY").center(x,z).slot2D(7,4.5,90).extrude(FRAME_T))
    foot = cq.Workplane("XY").box(FOOT_W,6,REACH,centered=(False,False,False)).translate((FOOT_X,0,0))
    ledge = cq.Workplane("XY").box(LEDGE_W,6,LEDGE_D,centered=(False,False,False)).translate((28,14,5.5))
    for x in (28,88):
        ledge = ledge.union(cq.Workplane("YZ").polyline(((0,0),(20,0),(20,33),(0,REACH)))
                            .close().extrude(4).translate((x,0,0)))
    result = result.union(foot).union(ledge)
    for x,depth in ANCHORS:
        result = result.cut(cq.Workplane("XZ").center(x,depth).slot2D(10,5.5,90).extrude(-6))
    assert result.val().isValid() and len(result.solids().vals())==1
    assert 7.5-4.5/2 >=4
    assert FRAME_H-RADIATOR_Z[-1]-7/2 >=4
    return result


def brace_local():
    return front_brace.local_shape(height=BRACE_HEIGHT, radiator_z=RADIATOR_Z)


def brace_installed(radiator_front_y):
    # Low-X web stays inward from the right hose end; the foot points forward.
    return brace_local().mirror("XZ").translate((BRACE_X0,radiator_front_y,0))


def brace_printable():
    # Print the same handed solid as the installed brace, with its broad web down.
    return (brace_local().mirror("XZ").rotate((0,0,0),(0,1,0),-90)
            .translate((BRACE_HEIGHT,front_brace.DEPTH,0)))


def brace_anchors(radiator_front_y):
    return [(BRACE_X0+x,radiator_front_y-y) for x,y in front_brace.ANCHORS]


def report(radiator_front_y):
    return {
        "part": BRACE_PART, "quantity":1,
        "basis":"same mirrored front brace, adapted to 105 mm vertical screw pitch; structural thickness and fastener sizes retained",
        "installed_bounds_xyz_mm":[[BRACE_X0,radiator_front_y-front_brace.DEPTH,0],
                                    [BRACE_X0+front_brace.WIDTH,radiator_front_y,BRACE_HEIGHT]],
        "web_x_range_mm":[BRACE_X0,BRACE_X0+front_brace.WEB_T],
        "print_dimensions_mm":[BRACE_HEIGHT,front_brace.DEPTH,front_brace.WIDTH],
        "factory_screw_axes_xz_mm":[[BRACE_X0+front_brace.SCREW_X,z] for z in RADIATOR_Z],
        "shelf_anchor_xy_mm":brace_anchors(radiator_front_y),
        "shelf_slot_length_width_mm":[front_brace.SHELF_SLOT_L,front_brace.SHELF_SLOT_W],
        "shelf_slot_adjustment_mm":[-front_brace.SHELF_TRAVEL,front_brace.SHELF_TRAVEL],
        "web_face_foot_thickness_mm":[front_brace.WEB_T,front_brace.FACE_T,front_brace.FOOT_T],
        "load_path":"two unused inward radiator factory threads -> continuous triangular web -> two shelf bolts with steel backing",
        "assembly_order":"secure bearing-frame shelf bolts before fitting radiator; fit brace loosely to supported radiator, then shelf, without hose preload",
        "fasteners":"two matched radiator screws + OD10 washers; two M4 shelf bolts, two nuts, four OD12 washers; determine lengths from actual engagement/stack",
        "print_orientation":"broad low-X web flat on bed; supports off; same front-brace slot bridges",
        "physical_fit_verified":False,
        "limitations":"right hose end assumed; actual tank ports, hose sweep, factory threads and warm PETG stiffness require dry fit",
    }


def preview(path, radiator_front_y, frame_rear_y):
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(15,6))
    def draw(ax,shape,color,alpha=1):
        vertices,triangles=shape.val().tessellate(.2)
        pts=np.array([[v.x,v.y,v.z] for v in vertices])
        faces=pts[np.array(triangles)]
        normals=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
        normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-9)
        light=np.array([.35,-.45,.82]);light/=np.linalg.norm(light)
        shades=.55+.4*np.maximum(normals@light,0)
        colors=shades[:,None]*np.array(to_rgb(color))
        ax.add_collection3d(Poly3DCollection(faces,facecolor=colors,
                           edgecolor="none",alpha=alpha))
    ax=fig.add_subplot(131,projection="3d")
    for x in FRAME_X:
        draw(ax,frame().rotate((0,0,0),(1,0,0),90).translate((x,frame_rear_y,0)),"#478f99")
    draw(ax,brace_installed(radiator_front_y),"#d99942")
    rad=cq.Workplane("XY").box(397,27,120,centered=(False,False,False)).translate((24.5,radiator_front_y,20))
    draw(ax,rad,"#bac4cd",.15)
    ax.set(xlim=(15,435),ylim=(radiator_front_y-55,frame_rear_y+10),zlim=(0,150))
    ax.set_box_aspect((420,100,150));ax.view_init(elev=28,azim=-70)
    ax.set_title("Installed: brace points toward rack front")
    ax=fig.add_subplot(132,projection="3d")
    draw(ax,frame(),"#478f99")
    ax.set(xlim=(0,120),ylim=(0,FRAME_H),zlim=(0,40))
    ax.set_box_aspect((120,FRAME_H,40));ax.view_init(elev=30,azim=-60)
    ax.set_title("Jobs 08/09: 140 × 120 × 40 mm")
    ax=fig.add_subplot(133,projection="3d")
    draw(ax,brace_printable(),"#d99942")
    ax.set(xlim=(0,142),ylim=(0,44.5),zlim=(0,28))
    ax.set_box_aspect((142,44.5,28));ax.view_init(elev=30,azim=-55)
    ax.set_title("Job 20: 142 × 44.5 × 28 mm")
    for ax in fig.axes:ax.set_axis_off()
    fig.suptitle("Kenshin rear AIO — front-style bearing frames and inward brace",fontsize=16)
    fig.text(.5,.08,"Same broad brace construction; 105 mm factory pitch is provisional. Tighten frame shelf bolts before fitting the radiator.",ha="center",fontsize=11)
    fig.tight_layout(rect=(0,.12,1,.91));fig.savefig(path,dpi=160);plt.close(fig)
