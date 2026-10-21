"""One-piece hose-end H115i brace, independent of the motherboard.

Local Y=0 is the radiator's rear face. Dimensions are nominal; verify the
two unused factory threads, hose corridor and shelf fit on the actual AIO.
"""
from pathlib import Path

import cadquery as cq

PART = "fan140_aio_hose_brace"
# Mirror about the installed screw line X410.25, preserving all four axes.
X0, WIDTH, DEPTH, HEIGHT = 392.5, 28.0, 44.5, 162.0
WEB_T, FACE_T, FOOT_T = 8.0, 6.0, 8.0
FOOT_FRONT, FACE_BOTTOM = 11.0, 18.0
SCREW_X = 17.75
FRONT_WEB_CLEARANCE = 13.0
RADIATOR_Z = (27.75, 152.25)
ANCHORS = ((SCREW_X, 20.0), (SCREW_X, 35.5))
SHELF_SLOT_L, SHELF_SLOT_W, SHELF_TRAVEL = 8.0, 5.5, 1.5


def local_shape(*, height=HEIGHT, radiator_z=RADIATOR_Z):
    # Full side gusset is the printing bed face. Flanges grow from that face;
    # no gusset joins, captive nuts, small pads or supports are necessary.
    # Broad relief clears the reused 6 mm foot and its 11 mm-high bolt head.
    # The underside tapers into the rear foot; no little ledges or scallops.
    web = (cq.Workplane("YZ").polyline(((0, FRONT_WEB_CLEARANCE),
           (FOOT_FRONT, FRONT_WEB_CLEARANCE),
           (FOOT_FRONT+FRONT_WEB_CLEARANCE-FOOT_T, FOOT_T),
           (DEPTH*(1-FOOT_T/height), FOOT_T), (0, height)))
           .close().extrude(WEB_T))
    face = (cq.Workplane("XY").box(WIDTH, FACE_T, height-FACE_BOTTOM,
                                  centered=(False, False, False))
            .translate((0, 0, FACE_BOTTOM)))
    foot = (cq.Workplane("XY").box(WIDTH, DEPTH-FOOT_FRONT, FOOT_T,
                                  centered=(False, False, False))
            .translate((0, FOOT_FRONT, 0)))
    shape = web.union(face).union(foot)
    for z in radiator_z:
        shape = shape.cut(cq.Workplane("XZ").center(SCREW_X, z)
                          .slot2D(8.5, 4.5, 90).extrude(-FACE_T))
    for x, y in ANCHORS:
        shape = shape.cut(cq.Workplane("XY").center(x, y)
                          .slot2D(SHELF_SLOT_L, SHELF_SLOT_W, 90).extrude(FOOT_T))
    assert shape.val().isValid() and len(shape.solids().vals()) == 1
    assert radiator_z[0]-8.5/2-FACE_BOTTOM >= 4
    assert height-radiator_z[1]-8.5/2 >= 4
    assert ANCHORS[0][1]-SHELF_SLOT_L/2-FOOT_FRONT >= 4
    assert DEPTH-ANCHORS[-1][1]-SHELF_SLOT_L/2 >= 4
    assert ANCHORS[1][1]-ANCHORS[0][1]-2*SHELF_TRAVEL-12 >= .5
    return shape


def installed(radiator_rear_y):
    return local_shape().translate((X0, radiator_rear_y, 0))


def printable(*, height=HEIGHT, radiator_z=RADIATOR_Z):
    # Shelf Y-Z load plane -> print X-Y; solid outer web lies flat on bed.
    return local_shape(height=height, radiator_z=radiator_z).rotate(
        (0, 0, 0), (0, 1, 0), -90).translate((height, 0, 0))


def report(radiator_rear_y, board_front_y):
    return {
        "part": PART, "quantity": 1, "original_brackets_reused": True,
        "handedness": "mirrored inward from owner-reported hose interference; low-X side web, unchanged mounting axes",
        "side_web_x_range_mm": [X0, X0+WEB_T],
        "front_web_underside_clearance_z_mm": FRONT_WEB_CLEARANCE,
        "nominal_original_foot_bolt_head_clearance_mm": 2.0,
        "installed_bounds_xyz_mm": [[X0, radiator_rear_y, 0],
                                     [X0+WIDTH, radiator_rear_y+DEPTH, HEIGHT]],
        "print_dimensions_mm": [HEIGHT, DEPTH, WIDTH],
        "web_face_foot_thickness_mm": [WEB_T, FACE_T, FOOT_T],
        "rear_factory_screw_axes_xz_mm": [[X0+SCREW_X, z] for z in RADIATOR_Z],
        "radiator_slot_length_width_mm": [8.5, 4.5],
        "shelf_anchor_xy_mm": [[X0+x, radiator_rear_y+y] for x, y in ANCHORS],
        "shelf_slot_length_width_mm": [SHELF_SLOT_L, SHELF_SLOT_W],
        "shelf_checked_adjustment_mm": [-SHELF_TRAVEL, SHELF_TRAVEL],
        "minimum_between_washers_at_opposing_travel_mm": .5,
        "nominal_motherboard_adapter_front_gap_mm": 2.21,
        "nominal_board_front_gap_mm": round(board_front_y-radiator_rear_y-DEPTH, 3),
        "nominal_original_foot_y_gap_mm": 2.0,
        "load_path": "two rear factory radiator screws -> broad face and continuous side gusset -> two shelf anchors and steel backing; no CPU or motherboard attachment",
        "print_orientation": "solid outer side of triangular web on bed; load plane within layers",
        "fasteners": "two matched factory-thread radiator screws through 6 mm face and washers; two M4 shelf through-bolts with OD12 washers and nuts/backing",
        "radiator_screw_length": "6 mm face + actual washer thickness + verified safe factory engagement; do not use long fan screws blindly or drill radiator",
        "assembly_order": "tighten original sandwich-frame shelf bolts first, since mirrored web covers their top access; keep AIO supported; loosely attach brace to rear factory threads, fit shelf bolts/backing, tighten without preloading radiator",
        "limitations": "prototype, no measured load rating; hose force, ports and warm PETG creep unmeasured; relieve hose preload rather than using brace to force tight bends",
    }


def preview(path: Path, radiator_rear_y):
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.patches import Polygon, Rectangle

    fig=plt.figure(figsize=(15, 5.6))
    ax=fig.add_subplot(1, 3, 1, projection="3d")
    shape=local_shape()
    vs, ts=shape.val().tessellate(.15)
    vertices=np.array([[v.x, v.y, v.z] for v in vs]); faces=vertices[np.array(ts)]
    normals=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-9)
    lighting=.55+.4*np.abs(normals @ np.array([.3,-.4,.866]))
    colors=lighting[:,None]*np.array([.20,.62,.67])[None,:]
    ax.add_collection3d(Poly3DCollection(faces,facecolors=colors,edgecolors=colors,linewidths=.1))
    ax.set(xlim=(-5,WIDTH+5),ylim=(-8,DEPTH+8),zlim=(0,HEIGHT+5))
    ax.set_box_aspect((WIDTH+10,DEPTH+16,HEIGHT+5)); ax.view_init(elev=20,azim=-45)
    ax.set_axis_off(); ax.set_title("One piece; two rear radiator screws",fontsize=12)
    ax=fig.add_subplot(1,3,2)
    y=radiator_rear_y
    ax.add_patch(Rectangle((y-26,20),26,140,facecolor="#d5d9dd",edgecolor="#535963"))
    ax.text(y-13,90,"Radiator",ha="center",va="center",rotation=90)
    ax.add_patch(Polygon([(y,FRONT_WEB_CLEARANCE),(y+FOOT_FRONT,FRONT_WEB_CLEARANCE),
                         (y+FOOT_FRONT+FRONT_WEB_CLEARANCE-FOOT_T,FOOT_T),
                         (y+DEPTH*(1-FOOT_T/HEIGHT),FOOT_T),(y,HEIGHT)],
                        facecolor="#5daeb4",alpha=.65))
    ax.add_patch(Rectangle((y,FACE_BOTTOM),FACE_T,HEIGHT-FACE_BOTTOM,facecolor="#287e86"))
    ax.add_patch(Rectangle((y+FOOT_FRONT,0),DEPTH-FOOT_FRONT,FOOT_T,facecolor="#287e86"))
    ax.plot([0,120],[-1,-1],color="#454a50",lw=3)
    for _,dy in ANCHORS:
        ax.plot([y+dy,y+dy],[-5,FOOT_T+5],color="#d78630",lw=3)
    for z in RADIATOR_Z:
        ax.plot([y-2,y+FACE_T+4],[z,z],color="#d78630",lw=3)
    ax.text(y+DEPTH+4,70,"Open space\ntoward CPU",fontsize=10,va="center")
    ax.set(xlim=(-16,120),ylim=(-10,172),xlabel="Shelf front → rear Y (mm)",ylabel="Height Z (mm)")
    ax.set_aspect("equal"); ax.set_title("Hose torque shared with shelf",fontsize=12)
    ax=fig.add_subplot(1,3,3)
    ax.add_patch(Rectangle((X0-8,y-26),54,26,facecolor="#d5d9dd",edgecolor="#535963"))
    ax.text(X0+19,y-13,"Radiator",ha="center",va="center")
    ax.add_patch(Rectangle((X0,y+FOOT_FRONT),WIDTH,DEPTH-FOOT_FRONT,facecolor="#5daeb4"))
    ax.add_patch(Rectangle((X0,y),WIDTH,FACE_T,facecolor="#287e86"))
    ax.add_patch(Rectangle((X0,y),WEB_T,DEPTH*(1-FOOT_T/HEIGHT),facecolor="#287e86"))
    for x,dy in ANCHORS:
        ax.plot(X0+x,y+dy,"o",color="#d78630",ms=7)
    ax.axvline(X0+SCREW_X,color="#d78630",ls="--",lw=1)
    ax.annotate("Web inward",(X0+WEB_T/2,y+25),(X0-13,y+DEPTH+8),
                arrowprops={"arrowstyle":"->"},fontsize=10)
    ax.annotate("Hose side",(X0+WIDTH,y+15),(X0+WIDTH+14,y+30),
                arrowprops={"arrowstyle":"->"},fontsize=10)
    ax.set(xlim=(X0-18,X0+WIDTH+35),ylim=(y-30,y+DEPTH+17),
           xlabel="Shelf X (mm)",ylabel="Shelf front → rear Y (mm)")
    ax.set_aspect("equal"); ax.set_title("Mirrored; screw line stays X410.25",fontsize=12)
    fig.suptitle("Berserk AIO brace — mirrored for hose clearance",fontsize=14)
    fig.text(.5,.015,"Print on the broad web. Tighten the original foot bolts first; verify actual hose clearance.",ha="center",fontsize=10)
    fig.subplots_adjust(top=.88,bottom=.13,wspace=.05)
    fig.savefig(path,dpi=150);plt.close(fig)
