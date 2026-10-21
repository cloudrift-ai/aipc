"""Draw interlocking motherboard frames and outside-PCB shelf anchors."""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
from print_jobs import read_binary_stl


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


if __name__ == "__main__":
    render(Path(__file__).resolve().parents[1] / "models")
