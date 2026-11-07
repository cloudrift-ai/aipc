"""Headless shaded renders for visual inspection (VTK, no display needed).

``render_views`` writes one labeled contact sheet of a shape, workplane,
assembly or STEP file. ``Scene`` tessellates an assembly once and renders it
many times with different highlighting, e.g. one part in context with the rest
ghosted. A person or a fresh-context agent must look at the sheets before a
change is accepted; a clean render is evidence for review, not a fit approval.

Coordinates: X left->right seen from the rack front, Y front->rear, Z up.
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq
import vtk
from PIL import Image, ImageDraw, ImageFont
from vtk.util.numpy_support import vtk_to_numpy

# name: (camera direction from the focal point, view-up, parallel projection)
VIEWS = {
    "iso front-left": ((-1, -1.3, 0.9), (0, 0, 1), False),
    "iso front-right": ((1, -1.3, 0.9), (0, 0, 1), False),
    "iso rear-right": ((1, 1.3, 0.9), (0, 0, 1), False),
    "iso rear-left": ((-1, 1.3, 0.9), (0, 0, 1), False),
    "iso front-right below": ((1, -1.3, -0.8), (0, 0, 1), False),
    "top": ((0, 0, 1), (0, 1, 0), True),
    "front": ((0, -1, 0), (0, 0, 1), True),
    "rear": ((0, 1, 0), (0, 0, 1), True),
    "left": ((-1, 0, 0), (0, 0, 1), True),
    "right": ((1, 0, 0), (0, 0, 1), True),
    "bottom": ((0, 0, -1), (0, 1, 0), True),
}
PART_VIEWS = ("iso front-left", "iso rear-right", "iso front-right below",
              "top", "bottom", "front", "rear", "left", "right")
ASSEMBLY_VIEWS = ("iso front-left", "iso front-right", "iso rear-right", "iso rear-left",
                  "top", "front", "rear", "left", "right")
CONTEXT_VIEWS = ("iso front-left", "iso rear-right", "top")
DEFAULT_RGB = (0.55, 0.72, 0.85)
HIGHLIGHT_RGB = (0.95, 0.45, 0.10)
GHOST_RGB = (0.78, 0.80, 0.83)


def _font(size):
    for name in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


class Scene:
    """Tessellated items ``(name, polydata faces, polydata edges, rgb, opacity, bounds)``."""

    def __init__(self, obj, color=DEFAULT_RGB):
        if isinstance(obj, (str, Path)):
            path = str(obj)
            try:
                obj = cq.Assembly.importStep(path)
            except Exception:
                obj = cq.importers.importStep(path)
        self.items = []
        if isinstance(obj, cq.Assembly):
            for shape, name, loc, col in obj:
                c = col.toTuple() if col else (*color, 1.0)
                self._add(name.split("/", 1)[-1], shape.moved(loc), c[:3], c[3])
        else:
            if isinstance(obj, cq.Workplane):
                obj = cq.Compound.makeCompound([v for v in obj.vals() if isinstance(v, cq.Shape)])
            self._add("shape", obj, color, 1.0)

    def _add(self, name, shape, rgb, opacity):
        bb = shape.BoundingBox()
        size = max(bb.xlen, bb.ylen, bb.zlen, 1.0)
        data = shape.toVtkPolyData(tolerance=max(size / 600, 0.03), angularTolerance=0.25)
        geom = vtk.vtkGeometryFilter(); geom.SetInputData(data); geom.Update()
        poly = geom.GetOutput()
        faces = vtk.vtkPolyData(); faces.SetPoints(poly.GetPoints()); faces.SetPolys(poly.GetPolys())
        normals = vtk.vtkPolyDataNormals(); normals.SetInputData(faces); normals.SetFeatureAngle(35); normals.Update()
        lines = vtk.vtkPolyData(); lines.SetPoints(poly.GetPoints()); lines.SetLines(poly.GetLines())
        self.items.append((name, normals.GetOutput(), lines, rgb, opacity,
                           (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)))

    def names(self):
        return [i[0] for i in self.items]

    def _renderer(self, style):
        ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
        ren.SetUseDepthPeeling(1); ren.SetMaximumNumberOfPeels(4)
        bounds = None
        for name, faces, lines, rgb, opacity, b in self.items:
            rgb, opacity, edges, frame = style(name, rgb, opacity)
            if opacity <= 0:
                continue
            m = vtk.vtkPolyDataMapper(); m.SetInputData(faces)
            a = vtk.vtkActor(); a.SetMapper(m)
            p = a.GetProperty(); p.SetColor(*rgb); p.SetOpacity(opacity)
            p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.08)
            ren.AddActor(a)
            if edges and lines.GetNumberOfLines():
                lm = vtk.vtkPolyDataMapper(); lm.SetInputData(lines)
                la = vtk.vtkActor(); la.SetMapper(lm)
                la.GetProperty().SetColor(0.12, 0.12, 0.14); la.GetProperty().SetOpacity(min(1, opacity * 1.5))
                ren.AddActor(la)
            if frame:
                bounds = b if bounds is None else tuple(
                    min(bounds[i], b[i]) if i % 2 == 0 else max(bounds[i], b[i]) for i in range(6))
        kit = vtk.vtkLightKit(); kit.AddLightsToRenderer(ren)
        return ren, bounds

    def sheet(self, out: Path, title="", views=PART_VIEWS, size=(520, 400), columns=3,
              style=None, frame_bounds=None) -> Path:
        style = style or (lambda name, rgb, op: (rgb, op, True, True))
        ren, bounds = self._renderer(style)
        bounds = frame_bounds or bounds
        assert bounds is not None, f"nothing to render for {out}"
        tiles = []
        for view in views:
            direction, up, parallel = VIEWS[view]
            tile = _snapshot(ren, bounds, direction, up, parallel, size)
            ImageDraw.Draw(tile).text((10, 8), view, fill=(40, 40, 40), font=_font(18))
            tiles.append(tile)
        rows = (len(tiles) + columns - 1) // columns
        head = 46 if title else 0
        img = Image.new("RGB", (columns * size[0], rows * size[1] + head), "white")
        draw = ImageDraw.Draw(img)
        if title:
            dims = f"   bbox {bounds[1]-bounds[0]:.1f} x {bounds[3]-bounds[2]:.1f} x {bounds[5]-bounds[4]:.1f} mm (X x Y x Z)"
            draw.text((12, 12), title + dims, fill=(10, 10, 10), font=_font(22))
        for i, tile in enumerate(tiles):
            x, y = (i % columns) * size[0], head + (i // columns) * size[1]
            img.paste(tile, (x, y))
            draw.rectangle((x, y, x + size[0] - 1, y + size[1] - 1), outline=(215, 215, 215))
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out, optimize=True)
        return out

    def highlight(self, out: Path, selected: set[str], title="", views=CONTEXT_VIEWS, size=(620, 460)):
        """Render ``selected`` instance names in orange with everything else ghosted."""
        def style(name, rgb, op):
            if name in selected:
                return HIGHLIGHT_RGB, 1.0, True, True
            return GHOST_RGB, 0.12, False, True
        return self.sheet(out, title, views, size, columns=len(views), style=style)


_WINDOW = None


def _window():
    """One offscreen window for the whole process: creating many stalls macOS."""
    global _WINDOW
    if _WINDOW is None:
        _WINDOW = vtk.vtkRenderWindow(); _WINDOW.SetOffScreenRendering(1)
        _WINDOW.SetAlphaBitPlanes(1); _WINDOW.SetMultiSamples(0)
    return _WINDOW


def _snapshot(ren, bounds, direction, up, parallel, size):
    win = _window()
    renderers = win.GetRenderers()
    renderers.InitTraversal()
    for _ in range(renderers.GetNumberOfItems()):
        win.RemoveRenderer(renderers.GetNextItem())
    win.AddRenderer(ren); win.SetSize(*size)
    cx, cy, cz = ((bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, (bounds[4] + bounds[5]) / 2)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(cx, cy, cz)
    cam.SetPosition(cx + direction[0] * 1000, cy + direction[1] * 1000, cz + direction[2] * 1000)
    cam.SetViewUp(*up)
    cam.SetParallelProjection(parallel)
    ren.ResetCamera(bounds)
    if parallel:
        cam.SetParallelScale(cam.GetParallelScale() * 0.9)
    else:
        cam.Zoom(1.25)
    ren.ResetCameraClippingRange()
    win.Render()
    grab = vtk.vtkWindowToImageFilter(); grab.SetInput(win); grab.ReadFrontBufferOff(); grab.Update()
    img = grab.GetOutput()
    w, h, _ = img.GetDimensions()
    arr = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(h, w, -1)[::-1]
    win.RemoveRenderer(ren)
    return Image.fromarray(arr[:, :, :3].copy())


def render_views(obj, out: Path, title: str = "", views=PART_VIEWS, size=(520, 400),
                 columns: int = 3, color=DEFAULT_RGB) -> Path:
    """Write a labeled contact sheet of ``views`` for a shape, workplane, assembly or STEP file."""
    return Scene(obj, color).sheet(out, title, views, size, columns)
