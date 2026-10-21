"""Compare the generated AIO bearing frames with their fan-face outlines."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle, Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def render(path, front, rear):
    """Shapes use installed local coordinates: X width, Z height, Y depth."""
    fig = plt.figure(figsize=(12, 9))
    for row, (name, shape, size, pitch) in enumerate((
        ("Berserk · 140 mm", front, 140, 124.5),
        ("Kenshin · 120 mm", rear, 120, 105),
    )):
        vertices, indices = shape.val().tessellate(.1)
        points = np.array([[v.x, v.y, v.z] for v in vertices])
        faces = points[np.array(indices)]
        ax = fig.add_subplot(2, 2, row * 2 + 1)
        ax.add_collection(PolyCollection(faces[:, :, [0, 2]],
                                         facecolors="#63a7af", edgecolors="none"))
        ax.add_patch(Rectangle((0, 20), size, size, fill=False,
                               ec="#202a37", ls="--", lw=1.8))
        offset = (size - pitch) / 2
        for x in (offset, size - offset):
            for z in (20 + offset, 20 + size - offset):
                ax.add_patch(Circle((x, z), 1.5, fill=False, ec="#bd5a22", lw=1))
        ax.text(size / 2, 20 + size / 2,
                f"{pitch:g} × {pitch:g} mm hole pitch\n7 × 4.5 mm mounting slots",
                ha="center", va="center", fontsize=9)
        ax.annotate("20 mm lower support", (size / 2, 10), (size / 2, -16),
                    ha="center", fontsize=10, arrowprops={"arrowstyle": "->"})
        ax.set(xlim=(-8, size + 8), ylim=(-27, size + 29), aspect="equal",
               xlabel="Width (mm)", ylabel="Height above shelf (mm)",
               title=f"{name}: top and sides flush")

        ax = fig.add_subplot(2, 2, row * 2 + 2, projection="3d")
        normals = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-9)
        shades = .55 + .4 * np.abs(normals @ np.array([.3, -.4, .866]))
        ax.add_collection3d(Poly3DCollection(faces, edgecolors="none",
                            facecolors=shades[:, None] * np.array([.25, .64, .69])))
        low, high = points.min(axis=0), points.max(axis=0)
        ax.set(xlim=(low[0], high[0]), ylim=(low[1], high[1]), zlim=(0, high[2]))
        ax.set_box_aspect(high - low)
        ax.view_init(elev=25, azim=65 if row == 0 else -65)
        ax.set_axis_off()
        ax.set_title("Bearing ledge and two-slot shelf foot retained")
    fig.suptitle("AIO mounts aligned to standard fan faces", fontsize=16)
    fig.text(.5, .035,
             "Dashed: nominal fan outline. Existing screw axes and shelf anchors stay in place.\n"
             "Hose braces remain 2 mm above the radiator tops. Print each main frame broad face down.",
             ha="center", fontsize=10)
    fig.tight_layout(rect=(0, .09, 1, .96))
    fig.savefig(path, dpi=160)
    plt.close(fig)
