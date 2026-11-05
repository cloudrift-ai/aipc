"""Rail/shelf spacing trials with a tapered ridge in an UNUSED shelf slot.

The owner confirms side holes share the nominal 40 x 6.5 mm deck vent size.
No measured slide or side-hole survey exists. These are local fit samples; the main
assembly shows representative 2 mm copies at provisional positions. Only the pad
thickness spans the gap; the ridge points into the shelf. Screws use separate
metal mounting points, never the ridge.
"""

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

import cadquery as cq
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from shelf_interfaces import SIDE_SLOT_LENGTH, SIDE_SLOT_WIDTH


# Slot size combines the published deck vent dimensions with the owner's
# side/deck equivalence. Printed clearance and pad dimensions are fit choices.
LOCATOR_CLEARANCE = .2  # each side, nominal; confirm printed fit
TRIAL_THICKNESSES = (1.0, 2.0, 3.0, 4.0)
FIT_COPIES = 4  # four of each thickness on one plate, not an installed quantity


@dataclass(frozen=True)
class Shim:
    thickness: float
    width: float = 52.0
    height: float = 16.0
    locator_length: float = SIDE_SLOT_LENGTH - 2 * LOCATOR_CLEARANCE
    locator_width: float = SIDE_SLOT_WIDTH - 2 * LOCATOR_CLEARANCE
    locator_height: float = 4.0
    crest_length: float = SIDE_SLOT_LENGTH - 2 * LOCATOR_CLEARANCE - 4.0
    crest_width: float = 3.2

    @property
    def name(self):
        return f"rail_shelf_shim_{self.thickness:g}mm".replace(".", "p")


def build(spec: Shim):
    values = asdict(spec)
    assert all(math.isfinite(v) and v > 0 for v in values.values()), values
    assert spec.thickness >= 1.0, "trial pad needs at least five 0.20 mm layers"
    for name in ("thickness", "locator_height"):
        layers = values[name] / .2
        assert abs(layers - round(layers)) < 1e-6, (name, "use 0.20 mm increments")
    assert spec.width > spec.height
    assert spec.locator_length > spec.locator_width >= 3.2
    assert spec.locator_height >= 2.0, "keep a useful insertion lead"
    assert spec.crest_length > spec.crest_width >= 2.4, "no sharp or single-road crest"
    assert spec.crest_length < spec.locator_length and spec.crest_width < spec.locator_width
    # Nested capsule spines plus decreasing radii keep every higher section
    # inside the one below it. The ridge has no barb, undercut or exterior roof.
    assert spec.crest_length - spec.crest_width <= spec.locator_length - spec.locator_width
    assert spec.locator_length - spec.locator_width <= spec.width - spec.height
    assert (spec.height - spec.locator_width) / 2 >= 4, "continuous bearing land around ridge"
    assert spec.locator_length < SIDE_SLOT_LENGTH and spec.locator_width < SIDE_SLOT_WIDTH
    assert spec.width - spec.height >= SIDE_SLOT_LENGTH - SIDE_SLOT_WIDTH
    assert min((spec.width - SIDE_SLOT_LENGTH) / 2,
               (spec.height - SIDE_SLOT_WIDTH) / 2) >= 4, "pad must surround the entire shelf slot"

    pad = (cq.Workplane("XY").center(spec.width / 2, spec.height / 2)
           .slot2D(spec.width, spec.height).extrude(spec.thickness))
    ridge = (cq.Workplane("XY").workplane(offset=spec.thickness)
             .center(spec.width / 2, spec.height / 2)
             .slot2D(spec.locator_length, spec.locator_width)
             .workplane(offset=spec.locator_height)
             .slot2D(spec.crest_length, spec.crest_width).loft(ruled=True))
    result = pad.union(ridge)
    assert result.val().isValid() and len(result.solids().vals()) == 1
    # The slide-facing bearing face stays uninterrupted; the ridge is rooted
    # in a broad pad and insertion depth is separate from spacing thickness.
    bb = result.val().BoundingBox()
    assert abs(bb.zmin) < 1e-6 and abs(bb.zmax - spec.thickness - spec.locator_height) < 1e-6
    assert ridge.val().BoundingBox().xmin >= 4 and ridge.val().BoundingBox().ymin >= 4
    return result


def specs():
    assert len(TRIAL_THICKNESSES) == len(set(TRIAL_THICKNESSES)), "one model per thickness"
    return [Shim(thickness) for thickness in TRIAL_THICKNESSES]


def print_parts():
    return {spec.name: build(spec) for spec in specs()}


def report():
    return {
        "status": "owner-confirmed nominal slot size; printed fit and rail gap unmeasured; empty-shelf fit samples only",
        "installation_released": False,
        "installed_quantity": None,
        "fit_copies_per_unique_part": FIT_COPIES,
        "dimensions_mm": {spec.name: asdict(spec) for spec in specs()},
        "dimension_basis": "Published deck vents are 40 x 6.5 mm; owner confirms side mounting holes share those dimensions. Pad, taper and print clearances are chosen prototype parameters; no caliper measurements supplied.",
        "nominal_side_slot_mm": [SIDE_SLOT_LENGTH, SIDE_SLOT_WIDTH],
        "nominal_locator_clearance_per_side_mm": LOCATOR_CLEARANCE,
        "gap_rule": "For a centered shelf: thickness=(installed inner-slide face spacing - actual bare shelf width)/2. Measure each side if asymmetric. A zero/negative gap needs no shim or a geometry change.",
        "published_reference_only": {
            "StarTech_shelf_body_width_mm": 446.0,
            "StarTech_shelf_body_width_tolerance_mm": 1.0,
            "Gigabyte_R162_ZA0_body_width_mm": 438.0,
            "note": "Body-width difference does not establish slide contact-plane spacing or stud stand-off.",
            "StarTech_drawing": "https://sgcdn.startech.com/005329/media/sets/ADJSHELFHDV_Diagram/ADJSHELFHDV_Diagram.PDF",
            "Gigabyte_rail_guide": "https://download.gigabyte.com/FileList/Manual/server_system_qig_25HB2-3A0202-K0R.pdf",
        },
        "unmeasured": [
            "actual left/right gap, rail straightness and free travel",
            "actual side-hole tolerances and end shape, wall thickness and unobstructed insertion depth",
            "unused hole positions with full pad bearing on steel and the inner rail",
            "separate steel fastener locations, thread, length, head and nut access",
            "rail moving-member clearance and slide load rating for the modified shelf",
        ],
        "locator_fit": "Rounded 35.6 x 3.2 mm crest leads into the nominal 40 x 6.5 mm slot; 4 mm continuous taper widens to a 39.6 x 6.1 mm root, leaving 0.2 mm nominal clearance around its outline. A 52 x 16 mm capsule pad surrounds the whole opening with at least 4.75 mm bearing land. Check 4 mm unobstructed insertion depth. Actual aperture tolerances, end shape and printed fit remain unmeasured. Taper guides insertion but has no snap retention; the pad must seat fully, and a wedged ridge must not add to the selected gap.",
        "load_path": "Screws fasten the metal inner slide to the metal shelf at separate sites. Pads set spacing and carry compression; the tapered ridge only locates an otherwise unoccupied slot. No plastic threads, snap barb or structural ridge retention. Steel fasteners do not eliminate plastic creep in a joint whose spacing depends on the pads.",
        "fit_sequence": [
            "Support the empty shelf. Try one sample at a time; do not stack the ridged parts.",
            "Align the long ridge with an unused shelf side slot and press the rounded crest in by hand, flat opposite face toward the inner slide. Stop if it jams before the pad seats; resize the ridge rather than force the slot.",
            "Seat the pad face on sound steel around the whole slot and under a flat rail face. Check 4 mm inward ridge projection; a bottomed or wedged ridge is not a seated pad.",
            "Choose the thickness without pulling a slide inward or spreading it outward. Regenerate to a 0.20 mm intermediate thickness if needed.",
            "Check separate metal screws/nuts and tools clear the pad footprint, and no head or thread enters the moving rail. No screw size or length is assumed here.",
            "Check full empty-shelf travel and actual part temperature. Confirm sustained clamp spacing before loaded use; use metal spacers where creep-free spacing is needed.",
        ],
        "print_orientation": "flat slide face on bed; tapered locating ridge up; no supports",
        "material": "Duramic PETG, existing 0.20 mm / 240 C / 75 C process",
        "assembly_collision_checks": "The main STEP includes four representative 2 mm copies with schematic closed rails and slotted sidewalls. Their placement is checked against modeled geometry; see rail-shelf-assembly-report.json. Actual rail interfaces, fasteners and travel remain unverified.",
    }


def _mesh(out, spec):
    from print_jobs import read_binary_stl
    vertices, indices, _ = read_binary_stl(out / f"{spec.name}.stl")
    return np.asarray(vertices)[np.asarray(indices)]


def _surface(triangles, elev, azim):
    # Opaque face shading: triangulation edges are not physical ribs.
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
    el, az = np.radians((elev, azim))
    direction = np.array((np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)))
    visible = normals @ direction > 1e-7
    triangles, normals = triangles[visible], normals[visible]
    light = np.array((-.3, -.4, 1.0))
    light /= np.linalg.norm(light)
    shade = .65 + .35 * np.clip(normals @ light, 0, 1)
    colors = np.column_stack((shade[:, None] * np.array((.38, .7, .74)), np.ones(len(shade))))
    return Poly3DCollection(triangles, facecolors=colors, edgecolors="none", linewidths=0,
                            antialiaseds=False)


def preview(out: Path):
    """Review the exported meshes, including both faces and the full taper."""
    views = ((90, -90, "Ridge face"), (-90, -90, "Bed / slide face"),
             (0, 0, "End"), (0, 90, "Side"),
             (25, -55, "Oblique"), (-25, 125, "Below oblique"))
    variants = specs()
    max_z = max(spec.thickness + spec.locator_height for spec in variants) + 1
    fig = plt.figure(figsize=(18, 3 * len(variants)))
    for row, spec in enumerate(variants):
        triangles = _mesh(out, spec)
        for col, (elev, azim, title) in enumerate(views):
            ax = fig.add_subplot(len(variants), 6, row * 6 + col + 1, projection="3d")
            ax.add_collection3d(_surface(triangles, elev, azim))
            ax.set(xlim=(-1, spec.width + 1), ylim=(-1, spec.height + 1), zlim=(0, max_z))
            ax.set_box_aspect((spec.width + 2, spec.height + 2, max_z))
            ax.view_init(elev=elev, azim=azim)
            ax.set_proj_type("ortho")
            ax.set_title(f"{spec.thickness:g} mm pad — {title}", fontsize=10)
            ax.set_axis_off()
    fig.suptitle("Rail/shelf shim fit samples — actual print orientation, tapered ridge up", fontsize=16)
    fig.tight_layout(rect=(0, 0, 1, .97))
    fig.savefig(out / "rail-shelf-shims-print-review.png", dpi=140)
    plt.close(fig)

    fig = plt.figure(figsize=(12, 6.5))
    grid = fig.add_gridspec(2, len(variants), height_ratios=(1.3, 1))
    for i, spec in enumerate(variants):
        ax = fig.add_subplot(grid[0, i], projection="3d")
        ax.add_collection3d(_surface(_mesh(out, spec), 33, -65))
        ax.set(xlim=(-1, spec.width + 1), ylim=(-1, spec.height + 1), zlim=(0, max_z))
        ax.set_box_aspect((spec.width + 2, spec.height + 2, max_z), zoom=1.0)
        ax.view_init(elev=33, azim=-65)
        ax.set_proj_type("ortho")
        ax.set_axis_off()
        ax.set_title(f"{spec.thickness:g} mm pad", fontsize=13, pad=-10)

    # Explanatory longitudinal section: a wall with an UNUSED slot. It is not
    # surveyed installation geometry, and does not imply screw clearance.
    example = variants[min(1, len(variants) - 1)]
    pad_half = example.width / 2
    root_half, crest_half = example.locator_length / 2, example.crest_length / 2
    hole_half = SIDE_SLOT_LENGTH / 2
    wall_end = pad_half + 7
    section = fig.add_subplot(grid[1, :])
    for x in (-wall_end, hole_half):
        section.add_patch(Rectangle((x, 0), wall_end - hole_half, 1.2, color="#9aa5ad"))
    section.add_patch(Rectangle((-pad_half, -example.thickness), example.width, example.thickness, color="#65aab2"))
    section.add_patch(plt.Polygon([(-root_half, 0), (-crest_half, example.locator_height),
                                  (crest_half, example.locator_height), (root_half, 0)], color="#65aab2"))
    section.add_patch(Rectangle((-wall_end, -example.thickness - 1.2), 2 * wall_end, 1.2, color="#647787"))
    section.text(wall_end + 1, .6, "Steel shelf side\nRidge enters unused slot", va="center", fontsize=10)
    section.text(wall_end + 1, -example.thickness - .6, "Inner slide\nFlat face against shim", va="center", fontsize=10)
    section.annotate("", xy=(-pad_half - 3, -example.thickness), xytext=(-pad_half - 3, 0),
                     arrowprops={"arrowstyle": "<->", "color": "#36545b"})
    section.text(-wall_end - 1, -example.thickness / 2, f"{example.thickness:g} mm\ntrial gap", ha="right", va="center", fontsize=10)
    section.annotate(f"{example.locator_height:g} mm insertion", xy=(0, example.locator_height),
                     xytext=(0, example.locator_height + 2), ha="center", fontsize=10,
                     arrowprops={"arrowstyle": "-", "color": "#36545b"})
    section.set(xlim=(-wall_end - 10, wall_end + 31),
                ylim=(-example.thickness - 3, example.locator_height + 3), aspect="equal")
    section.set_axis_off()
    section.set_title("Along an unused shelf slot (schematic)\nMetal screws use separate locations outside the pad", fontsize=11)
    fig.suptitle("Rail-to-shelf locating shims", fontsize=19)
    fig.text(.5, .91, f"{example.width:g} × {example.height:g} mm pads; {example.locator_height:g} mm-tall tapered ridges guide insertion", ha="center", fontsize=12)
    fig.text(.5, .035, "FIT SAMPLES: slot fit, inside clearance and screw access remain unmeasured.\nPress in by hand until the pad seats flat. Print flat face down; use one thickness at a time.", ha="center", fontsize=10)
    fig.subplots_adjust(top=.81, bottom=.16, left=.03, right=.97, hspace=.2)
    fig.savefig(out / "rail-shelf-shims.png", dpi=170)
    plt.close(fig)
    (out / "rail-shelf-shims-report.json").write_text(json.dumps(report(), indent=2) + "\n")
