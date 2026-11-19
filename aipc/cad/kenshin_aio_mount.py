"""Side 360 mm AIO: two bearing frames with shallow feet; no brace.

Built in the radiator-local frame (length along +X, hose end at low X, inner
face toward -Y, fans toward +Y). shelf_layout turns the group +90 degrees
about Z onto the deck's left edge: hose end toward the rack front, fans
exhausting past the left deck edge, feet bearing directly on the deck.

The frames follow the older fitted revision (owner, 2026-11-19): the foot
stays inside the radiator footprint (REACH ends at the radiator's inner face)
instead of projecting 75 mm inward, and the inward hose brace is dropped as
unnecessary. The freed strip beside the radiator holds Berserk's NIC riser.

Only the radiator/fan pitch and frame envelope adapt to the smaller fan size.
Fastener diameters and structural thicknesses are retained, not scaled down.
Factory interfaces and the left-end hose envelope remain provisional.
"""
import cadquery as cq

FRAME_X = (31.0, 271.0)
FRAME_W, FRAME_H, FRAME_T = 120.0, 140.0, 6.0
RADIATOR_T = 27.0
# Foot depth from the frame's rear face to the radiator's inner face: the
# 6 mm frame plus the 27 mm radiator. Nothing projects past the AIO footprint.
REACH = FRAME_T + RADIATOR_T
FOOT_X, FOOT_W = 12.0, 96.0
# Anchors outside the ledge and gussets (x 28..92), under the radiator; the
# frame shelf bolts go in before the radiator is fitted.
ANCHORS = ((21.0, 20.0), (99.0, 20.0))
LEDGE_W, LEDGE_D = 64.0, 27.5
RADIATOR_Z = (27.5, 132.5)
SUPPORT_T = 0.0  # feet bear directly on the deck; the rear steel extension is retired


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
        ledge = ledge.union(cq.Workplane("YZ").polyline(((0,0),(20,0),(20,REACH),(0,REACH)))
                            .close().extrude(4).translate((x,0,0)))
    result = result.union(foot).union(ledge)
    for x,depth in ANCHORS:
        result = result.cut(cq.Workplane("XZ").center(x,depth).slot2D(10,5.5,90).extrude(-6))
    assert result.val().isValid() and len(result.solids().vals())==1
    assert 7.5-4.5/2 >=4
    assert FRAME_H-RADIATOR_Z[-1]-7/2 >=4
    assert 5.5+LEDGE_D <= REACH  # ledge stays under the radiator
    for x, depth in ANCHORS:
        # 12 mm washer clears the gussets and the frame plate, slot keeps 4 mm to the foot tip.
        assert x+6 <= 28 or x-6 >= 92, x
        assert depth-5 >= FRAME_T and depth+5 <= REACH-4, depth
    return result


def report():
    return {
        "foot_reach_mm": REACH,
        "foot_x_width_mm": [FOOT_X, FOOT_W],
        "anchor_local_x_depth_mm": ANCHORS,
        "basis": "older fitted revision (owner 2026-11-19): foot ends at the radiator inner face; no inward hose brace",
        "assembly_order": "bolt both bearing frames to the shelf before fitting the radiator; the anchors sit under the radiator",
    }


def preview(path, radiator_front_y, frame_rear_y):
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(12,6))
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
    ax=fig.add_subplot(121,projection="3d")
    for x in FRAME_X:
        draw(ax,frame().rotate((0,0,0),(1,0,0),90).translate((x,frame_rear_y,SUPPORT_T)),"#478f99")
    rad=cq.Workplane("XY").box(397,27,120,centered=(False,False,False)).translate((12.5,radiator_front_y,20+SUPPORT_T))
    draw(ax,rad,"#bac4cd",.15)
    ax.set(xlim=(0,423),ylim=(radiator_front_y-55,frame_rear_y+10),zlim=(0,150))
    ax.set_box_aspect((420,100,150));ax.view_init(elev=28,azim=-70)
    ax.set_title("Radiator-local view: feet end at the radiator inner face")
    ax=fig.add_subplot(122,projection="3d")
    draw(ax,frame(),"#478f99")
    ax.set(xlim=(0,120),ylim=(0,FRAME_H),zlim=(0,REACH))
    ax.set_box_aspect((120,FRAME_H,REACH));ax.view_init(elev=30,azim=-60)
    ax.set_title(f"Job 08: {FRAME_H:g} × {FRAME_W:g} × {REACH:g} mm")
    for ax in fig.axes:ax.set_axis_off()
    fig.suptitle("Kenshin side AIO — bearing frames, feet inside the AIO footprint",fontsize=16)
    fig.text(.5,.08,"105 mm factory pitch is provisional. Bolt the frames to the shelf before fitting the radiator.",ha="center",fontsize=11)
    fig.tight_layout(rect=(0,.12,1,.91));fig.savefig(path,dpi=160);plt.close(fig)
