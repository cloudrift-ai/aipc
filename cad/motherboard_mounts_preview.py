"""Draw interlocking motherboard frames and outside-PCB shelf anchors."""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
from print_jobs import read_binary_stl, print_orientation


def render_gpu_groove_location(out):
    """Installed top detail with the actual PCB datum, using exported meshes."""
    data = json.loads((out / 'fit-report.json').read_text())
    import atx_shelf_mounts as model
    fig, axes = plt.subplots(2, 1, figsize=(13, 6.5))
    for ax, system in zip(axes, ('Kenshin', 'Berserk')):
        pattern = next(p for p in data['motherboard_adapter_revision']['support_patterns']
                       if p['part'].startswith(system.lower()) and p['gpu_tab_relief'])
        part = data['installed_part_models'][pattern['part']]
        vertices, indices, _ = read_binary_stl(out / f'{part}.stl')
        x, y, _, d = model.BOARDS[system]
        dx, dy = pattern['installed_origin_xy_mm']
        triangles = (np.asarray(vertices)+(dx-x, dy-y-d, 0))[np.asarray(indices)]
        for z, color in ((6, '#82bfc8'), (4, '#de8a38')):
            faces = triangles[np.all(np.abs(triangles[:, :, 2]-z) < .001, axis=1)]
            ax.add_collection(PolyCollection(faces[:, :, :2], facecolors=color,
                                             edgecolors='none', antialiaseds=False))
        ax.axhline(0, color='#bb2639', ls='--', lw=1.5)
        low, high = triangles[:, :, 0].min(), triangles[:, :, 0].max()
        ax.set(xlim=(low-2, high+2), ylim=(-3, 12),
               yticks=[0, 1, 3, 7.5], ylabel='Behind PCB edge (mm)')
        ax.set_title(f'{system}: installed top view, rear rail detail', loc='left', fontsize=12)
        ax.grid(axis='y', alpha=.12)
        ax.set_xlabel('Along motherboard edge (mm); depth enlarged for visibility')
    fig.suptitle('GPU-tab groove: 2 mm deep, spanning 1–3 mm behind the motherboard edge', fontsize=15)
    fig.legend(handles=[Line2D([], [], color='#bb2639', ls='--', label='Motherboard rear edge'),
                        Line2D([], [], color='#de8a38', lw=7, label='Groove floor'),
                        Line2D([], [], color='#82bfc8', lw=7, label='Full-height rail / washer seats')],
               loc='lower center', bbox_to_anchor=(.5, .065), ncol=3, frameon=False)
    fig.text(.5, .025, 'ATX / PCIe nominal bracket outer face: +1.95 mm; bent tip about +1.53…+2.39 mm. Physical fit remains provisional.',
             ha='center', fontsize=10)
    fig.tight_layout(rect=(0, .13, 1, .94))
    fig.savefig(out / 'motherboard-gpu-groove-location.png', dpi=170)
    plt.close(fig)


def render_gpu_relief(out):
    """Review exported meshes in the same orientation as their print plates."""
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    views = ((90, -90, 'Above'), (-90, -90, 'Below / bed face'),
             (15, 0, 'Rear edge'), (15, 180, 'Board-facing edge'),
             (25, 45, 'Oblique'), (-25, 225, 'Bed-face oblique'))
    for part in ('atx_mobo_adapter_rail', 'h12d_mobo_adapter_rail'):
        mesh, _ = print_orientation(part, read_binary_stl(out / f'{part}.stl'))
        vertices, indices, (width, depth, height) = mesh
        triangles = np.asarray(vertices)[np.asarray(indices)]
        # Show only the rear 36 mm; full-frame views hide a 2 mm feature.
        clipped = []
        for triangle in triangles:
            polygon = []
            for a, b in zip(triangle, np.roll(triangle, -1, axis=0)):
                inside_a, inside_b = a[0] >= width-36, b[0] >= width-36
                if inside_a:
                    polygon.append(a)
                if inside_a != inside_b:
                    polygon.append(a+(b-a)*((width-36-a[0])/(b[0]-a[0])))
            for j in range(1, len(polygon)-1):
                clipped.append([polygon[0], polygon[j], polygon[j+1]])
        triangles = np.asarray(clipped)
        normal = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        magnitude = np.linalg.norm(normal, axis=1)
        sloped = (np.abs(normal[:, 0]) > .01*magnitude) & (np.abs(normal[:, 2]) > .01*magnitude)
        floor = np.all(np.abs(triangles[:, :, 2]-2) < .001, axis=1)
        colors = np.where(sloped | floor, '#de8a38', '#82bfc8')
        fig = plt.figure(figsize=(15, 10))
        for index, (elev, azim, label) in enumerate(views, 1):
            ax = fig.add_subplot(2, 3, index, projection='3d', computed_zorder=False)
            # Back-face culling avoids the painter's algorithm drawing long
            # hidden triangles over the narrow recesses on the visible side.
            er, ar = np.radians([elev, azim])
            camera = np.array([np.cos(er)*np.cos(ar), np.cos(er)*np.sin(ar), np.sin(er)])
            visible = (normal @ camera) > 1e-7
            ax.add_collection3d(Poly3DCollection(triangles[visible], facecolors=colors[visible],
                                               linewidths=0, antialiaseds=False,
                                               shade=True, zorder=2))
            # Rear rail ends16.5mm behind the PCB edge. Project its datum
            # onto each visible surface; this is not the +7.5mm post line.
            datum_x = width-16.5
            ax.plot([datum_x, datum_x], [0, depth],
                    [-.05, -.05] if elev < 0 else [height+.05, height+.05],
                    color='#bb2639', ls='--', lw=1.3, zorder=10)
            ax.set(xlim=(width-36, width), ylim=(0, depth), zlim=(0, height))
            ax.set_box_aspect((36, depth, height), zoom=.88)
            ax.view_init(elev=elev, azim=azim)
            ax.set_title(label, pad=8)
            ax.set_axis_off()
        fig.suptitle(f'{part}: 2 x 2 mm GPU-tab groove (orange roof)\nOriginal plate orientation: screw recesses up, groove toward bed', fontsize=16)
        fig.text(.5, .03, 'Red dashed line: projected motherboard rear edge. Groove spans 1–3 mm behind this edge.\nOriginal washer seats preserved; 2 mm bridge, no supports. Actual hardware dry-fit required.', ha='center', fontsize=11)
        fig.subplots_adjust(left=0, right=1, bottom=.08, top=.89, wspace=0, hspace=.05)
        fig.savefig(out / f'{part}-print-review.png', dpi=170)
        plt.close(fig)


def render(out):
    data = json.loads((out / "fit-report.json").read_text())
    patterns = data["motherboard_adapter_revision"]["support_patterns"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 8))
    colors = {"left": "#91d1db", "right": "#f0bd76"}
    for ax, system in zip(axes, ("Berserk", "Kenshin")):
        required_counts = []
        for pattern in (p for p in patterns if p["part"].startswith(system.lower())):
            label = pattern["part"]
            dx,dy=pattern["installed_origin_xy_mm"]
            vertices, triangles, _ = read_binary_stl(out / f"{data['installed_part_models'][label]}.stl")
            vertices=np.asarray(vertices)
            vertices = vertices + (dx, dy, 0)
            triangles = vertices[np.asarray(triangles)]
            normal_z = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])[:, 2]
            face = "right" if pattern["shelf_anchor_end"] == "rear" else "left"
            ax.add_collection(PolyCollection(triangles[np.abs(normal_z)>1e-6, :, :2],
                                             facecolors=colors[face], edgecolors="none"))
            shared=pattern.get("shared_post_anchor_centers_mm",[])
            for x, y in pattern["shelf_anchor_centers_mm"]:
                ax.plot(x,y,marker="D" if [x,y] in shared else "+",color="#88429b" if [x,y] in shared else "#b52730",ms=5 if [x,y] in shared else 8,mew=1.5)
            for x,y in pattern.get("common_post_slot_centers_mm",[]):
                ax.plot(x,y,marker="|",color="#777777",ms=5,mew=.8)
            for x,y in pattern["optional_shelf_anchor_centers_mm"]:
                ax.plot(x,y,marker="o",mfc="none",mec="#178642",ms=7,mew=1.5)
            required_counts.append(pattern["required_motherboard_screw_count"])
        for m in (m for m in data["motherboard_mounts_mm"] if m["system"] == system):
            x, y = m["center_x_mm"], m["center_y_mm"]
            optional = system == "Kenshin" and m["ATX_site"] == "B"
            ax.plot(x, y, "o", ms=4.8, color="#263a48", mfc="white" if optional else "#263a48")
            ax.text(x, y+8.5, m["ATX_site"]+("*" if optional else ""), ha="center", va="bottom", fontsize=8)
        from matplotlib.patches import Rectangle
        import atx_shelf_mounts as model
        x,y,w,d=model.BOARDS[system]
        ax.add_patch(Rectangle((x,y),w,d,fill=False,edgecolor="#596b74",ls="--",lw=1.2))
        reserve=model.io_keepout(system)
        rx0,rx1=reserve["x_range_mm"];ry0,ry1=reserve["y_range_mm"]
        ax.add_patch(Rectangle((rx0,ry0),rx1-rx0,ry1-ry0,facecolor="#f3dcd6",edgecolor="#a96b58",hatch="///",lw=.8))
        ax.text((rx0+rx1)/2,(ry0+ry1)/2,"Rear I/O above Z10.55\nCheck tall post/plug clearance",ha="center",va="center",fontsize=8,color="#6a3b2b")
        for j in (j for j in data["motherboard_adapter_seams"] if j["system"]==system):
            x,y=j["center_xy_mm"];ax.plot(x,y,"s",mfc="none",mec="#8b3a7d",ms=20,mew=1)
        ax.autoscale_view()
        ax.margins(.09)
        ax.set_aspect("equal")
        ax.set_title(f"{system}: {required_counts[0]} + {required_counts[1]} motherboard screws", fontsize=13)
        ax.set_xlabel("Shelf X (mm); left/right viewed from rack front")
        ax.set_ylabel("Shelf Y (mm), rear upward")
        ax.grid(alpha=.12)
    fig.suptitle("Interlocking adapter pairs — eight selectable post slots per board", fontsize=17, y=.97)
    fig.legend(handles=[Line2D([],[],marker="D",ls="",color="#88429b",label="Selected GPU posts: 8 Berserk / 2 Kenshin"),Line2D([],[],marker="o",ls="",color="#263a48",label="Motherboard screw"),
                        Line2D([],[],marker="+",ls="",color="#b52730",label="Front M3 shelf anchors: two per board"),
                        Line2D([],[],marker="o",ls="",color="#178642",mfc="none",label="Optional shelf slots: six per board; fit before PCB"),
                        Line2D([],[],marker="o",ls="",color="#263a48",mfc="white",label="B*: optional Kenshin PCB hole"),
                        Line2D([],[],marker="s",ls="",color="#8b3a7d",mfc="none",label="Drop-in X/Y key"),
                        Line2D([],[],marker="|",ls="",color="#777777",label="Selectable post slot; drill only when used"),
                        Line2D([],[],ls="--",color="#596b74",label="Motherboard outline; front at bottom")],
               loc="lower center",ncol=2,frameon=False,bbox_to_anchor=(.5,.015))
    fig.subplots_adjust(left=.07,right=.98,top=.88,bottom=.24,wspace=.26)
    fig.savefig(out / "motherboard-independent-mounts.png",dpi=170)
    plt.close(fig)
    render_gpu_relief(out)
    render_gpu_groove_location(out)


if __name__ == "__main__":
    render(Path(__file__).resolve().parents[1] / "models")
