# AIPC: two AI workstations on one rack shelf

An open-shelf build that puts two PCs side by side on a single 1U four-post rack shelf, inside about 6U of rack height, using 3D-printed mounts instead of cases:

- **Berserk**: HUANANZHI H12D-8D with an AMD EPYC 7702P, 128 GB ECC RDIMM and **four NVIDIA V100 PCIe** cards cooled by one 140 mm pressure fan through a printed hood and an overhead exhaust duct. Corsair H115i AIO at the front.
- **Kenshin**: Gigabyte X870E AORUS PRO with a Ryzen 9 9950X3D and an **RTX 5090**. Lian Li GA II LITE 360 AIO at the rear.

![Shelf layout and side clearance](models/kenshin-berserk-6u-shelf-layout.png)

Everything is generated from Python ([CadQuery](https://cadquery.readthedocs.io/)) and checked in CAD for collisions, fastener access and bed fit. The design is a **fit prototype**: the CAD and slicer checks pass, but parts of it (GPU flange positions, the H12D board, cable bends, thermal behavior) still need measuring and dry-fitting on real hardware. The [design notes](docs/design.md) say what is verified and what is not.

## What's here

| Path | Contents |
| --- | --- |
| [parts.xlsx](parts.xlsx) | Parts spreadsheet with tabs for the shelf hardware, Berserk and Kenshin |
| [docs/design.md](docs/design.md) | How the layout, mounts and cooling work, with coordinates and open checks |
| [docs/assembly.md](docs/assembly.md) | Assembly order, fastener stacks and what to tighten before it gets covered |
| [docs/printing.md](docs/printing.md) | 3D printing guidelines: printer, materials, design and printability rules |
| [models/](models) | Generated STEP/STL for every printed part, the assembly STEP, drill-plan deck, fit reports and preview images |
| [print/](print/README.md) | Print plates (3MF) for the Qidi X-Plus, slicer profiles and the plate manifest |
| [cad/](cad) | Generators: [shelf_layout.py](cad/shelf_layout.py) builds the models; [print_jobs.py](cad/print_jobs.py) packs plates; [slice_jobs.py](cad/slice_jobs.py) slices and validates G-code |

## Printed parts

One model per unique part; the plate manifest says how many to print.

| Part | Qty | Used for |
| --- | ---: | --- |
| `atx_mobo_adapter_front` | 2 | Shelf-front half of each motherboard adapter (common to both boards) |
| `atx_mobo_adapter_rail` | 1 | Rear half with GPU-post rail at standard ATX positions (Kenshin) |
| `h12d_mobo_adapter_rail` | 1 | Rear half with the rail shifted for four dual-slot V100s (Berserk) |
| `psu_bracket` | 2 | Rear restraint for an 86 × 150 mm ATX PSU face (both PSUs) |
| `fan140_aio_frame` | 2 | 140 mm fan/radiator frame with bearing ledge (H115i) |
| `fan140_aio_hose_brace` | 1 | Hose-end brace for the 140 mm radiator |
| `fan120_aio_frame` | 2 | 120 mm fan/radiator frame with bearing ledge (360 mm AIO) |
| `fan120_aio_hose_brace` | 1 | Hose-end brace for the 120 mm radiator |
| `fan120_aio_center_spacer` | 1 | Keeps the middle 120 mm fan coplanar |
| `gpu_rest` | 1 | Front-end rest for the RTX 5090 |
| `v100_gpu_shroud` | 1 | Hood over the four V100s with integral 45° fan panel |
| `gpu_exhaust_fan_flange` | 1 | Fan outlet to 6-inch duct |
| `gpu_exhaust_roof_flange` | 1 | Duct to cabinet inner ceiling |
| `tnut_fit_coupon` | 1 | Test print for the M4 T-nut pocket |

## Regenerating

Requires Python 3.11+ and, for G-code, [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) with its bundled Qidi presets.

```bash
make setup
```

```bash
make cad plates
```

```bash
make gcode
```

`make cad` rebuilds `models/` (about a minute), `make plates` rebuilds the 3MF plates in `print/`, and `make gcode` slices every plate into `print/gcode/`. G-code is not committed; it is always generated from the plates and profiles. Run `make help` for the full list.

The plates target a first-generation **Qidi X-Plus** with a 0.4 mm nozzle: PETG for most mounts and Polymaker HT-PLA-GF (hardened steel nozzle) for the PSU brackets and GPU cooling parts. For another printer, change the bed size in [cad/print_jobs.py](cad/print_jobs.py), the machine preset in [cad/slice_jobs.py](cad/slice_jobs.py) and the profiles in [print/profiles/](print/profiles), and read [docs/printing.md](docs/printing.md) first.

## Adapting it

The generators are parametric but written for this hardware. Common changes:

- **Different shelf positions**: component placement lives at the top of [cad/shelf_layout.py](cad/shelf_layout.py); every printed mount, shelf hole and clearance check follows from it.
- **Different GPUs or slots**: the rear rail's eight post-slot positions are in [cad/atx_shelf_mounts.py](cad/atx_shelf_mounts.py) (`POST_SLOT_X`) and [cad/berserk_platform.py](cad/berserk_platform.py) for the H12D.
- **Different AIOs**: the 140 mm frame is `radiator_screw_frame()` in [cad/shelf_layout.py](cad/shelf_layout.py); the 120 mm frame and braces are in [cad/kenshin_aio_mount.py](cad/kenshin_aio_mount.py) and [cad/berserk_aio_brace.py](cad/berserk_aio_brace.py).

The script asserts on every collision and access check, so a change that breaks the layout fails loudly instead of exporting a bad part.

## License

[MIT](LICENSE): covers the code, models, print files and docs.
