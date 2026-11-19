# 3D printing guidelines

These are the design and printability guidelines for printed parts in every build, and the reference the independent print auditor checks against. The required steps for any new or changed printed part are in the root [AGENTS.md](../AGENTS.md#3d-printed-parts-required-steps); this file does not repeat them. Build-specific print notes (which plates use which profile, part orientations, fit test results) are in each build's `print/README.md`, for example [aipc/print/README.md](../aipc/print/README.md).

## Printer, slicer and profiles

- Target printer: **first-generation Qidi X-Plus**, 270 × 200 mm bed, **0.4 mm nozzle**, sliced with **OrcaSlicer 2.5.x** using the `Qidi X-Plus 0.4 nozzle` machine preset. The Qidi base presets are vendored unmodified from the OrcaSlicer v2.5.0 tag in [hwkit/printers/qidi-x-plus/orca-2.5.0/](../hwkit/printers/qidi-x-plus/orca-2.5.0/SOURCE.md), and `hwkit slice` ([slicer.py](../hwkit/slicer.py)) flattens each profile's `inherits` chain before slicing. OrcaSlicer 2.4.2 had never applied the parent presets, so G-code from before 2026-11-13 used different retraction, wipe, Z-hop and first-layer fan settings; see [SOURCE.md](../hwkit/printers/qidi-x-plus/orca-2.5.0/SOURCE.md). The printer, its bed, the G-code policy the slicer enforces and the materials are defined in [printer.toml](../hwkit/printers/qidi-x-plus/printer.toml).
- Default material: **Duramic PETG**, [process.json](../hwkit/printers/qidi-x-plus/process.json) and [duramic-petg-240c.json](../hwkit/printers/qidi-x-plus/duramic-petg-240c.json): 0.20 mm layers, 240 °C nozzle (never higher), 75 °C bed, four walls, five top and bottom layers, 40% gyroid infill, 3 mm brim, 5 mm³/s flow limit.
- Conservative speeds: first-layer walls, skirt, brim and infill 15 mm/s; outer walls and top surfaces 25 mm/s; inner walls 30 mm/s; infill 35 mm/s at most; travel 100 mm/s (60 mm/s on the first layer). Acceleration 300 mm/s² for printing, 200 on the first layer and 500 for travel.
- `make gcode` keeps its temporary slicing files inside the build's `print/gcode/` so Flatpak OrcaSlicer and the host share the output directory. Per-plate `.log` files there retain the command, exit status and slicer diagnostics, including when slicing fails.
- Check the nozzle, bed surface, filament dryness and first layer before a long print, and tune a small test piece when anything changes.

## Heat-exposed parts

- Parts that sit in hot air use **Polymaker HT-PLA-GF** with a **0.4 mm hardened steel nozzle** at 230 °C / 50 °C ([ht-pla-gf-psu.json](../hwkit/printers/qidi-x-plus/ht-pla-gf-psu.json), [polymaker-ht-pla-gf-230c.json](../hwkit/printers/qidi-x-plus/polymaker-ht-pla-gf-230c.json)). Every other part stays in PETG. Keep the material choice explicit for each plate. The slicer cannot check the nozzle: the stock X-Plus preset always reports `hardened_steel`, so fit the hardened steel nozzle before printing these plates.
- Follow Polymaker's [technical data sheet](https://cdn.shopify.com/s/files/1/0548/7299/7945/files/Polymaker_HT-PLA-GF_TDS_EN_V1.1.pdf?v=1746635222) for drying (60 °C for 6 h) and annealing (80–100 °C for 20–30 min; it recommends 100 °C for 30 min). Anneal on a flat support, let it cool, then re-measure hole pitch, slots and flatness; never force a warped part into place.
- Unloaded heat stability is not a loaded-part rating. The data sheet gives a heat deflection temperature at 1.8 MPa of 59.7 °C as printed and 84 °C annealed; the marketed 150 °C is unloaded shape stability.
- Treat 50 °C on any loaded printed part as an inspection trigger: stop and check for softening, creep or loose fasteners. Switch to metal where a printed part cannot stay stiff or cool enough.

## Design

- **Keep parts simple.** Broad, straightforward shapes that are easy to inspect, print and assemble. Remove small features unless they serve a mounting, clearance or structural purpose. Use the fewest practical parts and assembly steps.
- **Reuse dimensions and shapes.** Use the same bar widths, ear widths, hole and slot sizes and fasteners for equivalent functions. Mirror or repeat a common shape before adding a special variant, and keep one model per unique part: identical copies share a file and the plate's print count covers the quantity.
- **Challenge every small lip, ledge, notch, step, sliver, isolated pad and partial fillet.** Keep it only for a specific fit, load path or tool access; otherwise remove it or merge it into a broad surface. Prefer flush junctions and full-width transitions over cosmetic details.
- **Design the load path and print orientation together.** Put tensile stress along continuous roads in the layer plane rather than pulling layers apart; avoid thin upright tabs that can peel at a layer boundary. Favor balanced frames, paired ribs and broad feet. A large one-piece part is fine if it fits the bed and is stronger or simpler than an assembly; split only for fit, orientation, service access or warping.
- **Starting dimensions** for a 0.4 mm nozzle (fit-test, these are not load ratings): 3–5 mm for load-bearing ribs and gussets, 4–6 mm for plates and feet, 15–30 mm of gusset reach along each side of a loaded corner, triangular or tapered gussets with 2–4 mm root fillets, and at least 4 mm of material from a hole edge to a free edge.
- **Let steel carry the weight.** Put washers or metal backing under concentrated fasteners. Printed parts restrain components; the shelf supports them.
- **Fasteners.** Add nut pockets only when they are easy to print and use; otherwise use suitable screws with proper pilot holes and engagement. No captive nuts or intricate retention features by default. Check washer and screw-head envelopes across the full slot travel plus a straight driver path, and document which bolts must be tightened before a component covers them.
- **Snug fits.** 0.25 mm clearance per face gives a snug, hand-assembled fit on this printer and profile (6.0 mm hex over a 5.5 mm metal hex base; owner test print of the AIPC mobo rear rail on 2026-11-14 with the no-brim [motherboard-rails.json](../aipc/print/profiles/motherboard-rails.json) PETG profile, OrcaSlicer 2.5). Use it as the starting clearance for close-fitting metal parts in printed holes, and still dry-fit each new interface.
- **Real interfaces first.** Model the real component hole patterns, port clearances and tool access from manufacturer drawings or measurements, mark anything unmeasured as provisional, and use elongated shelf slots for adjustment.

## Printability

- Choose a broad, stable bed face and minimize large unsupported horizontal surfaces. Small or gradual overhangs and short anchored bridges are fine when the sliced preview and a test print look clean; do not add supports or split a sound part just to remove every overhang.
- Prefer gradual tapers, chamfers and printable arches to abrupt ledges or flat ceilings. Check how each layer steps beyond the one below and how a span finally closes; a circular arch can still go flat near its crown. Make sure every newly starting wall or roof has material beneath it.
- Permanent internal ribs are acceptable inside an airflow chamber: a few broad tapered ribs that grow from existing walls and stay in the finished part. Keep fastener and driver paths clear and mark the ribs so nobody removes them.
- Pack parts near the **bed center**, not at the cooler edges. The AIPC plate generator keeps 12 mm edge margin and 8 mm between parts before the 3 mm brims (3.25 mm edge margin for the long motherboard sections).

## Audit checklist

The independent print auditor (step 5 of the required steps) checks each new or changed part against everything above and reports must-fix, should-fix and notes with measured evidence. At minimum:

1. **Every overhang and span, layer by layer.** Slice the solid into thin slabs and compare each layer with the one below: where does each feature start, bridge or close? Accept short anchored bridges and 45-degree-or-steeper faces; flag flat ceilings over air and cantilevered ledges. Reconcile the part's figure in `<build>/print/orientation-audit.json` and the sliced G-code (`;TYPE:Bridge` regions) with what you find.
2. **Load path and stiffness.** Name the real loads (plug forces, cable pull, component weight) and check that they run along layers and through broad sections; flag thin or tall slender features and claims in the code or docs about what bears where that the geometry does not support.
3. **Edges, walls and small features.** At least 4 mm from any hole or slot to a free edge, ribs and gussets per the starting dimensions, and every lip, sliver, isolated pad or tiny peg justified by a fit, load or tool-access need.
4. **Fasteners.** Pilot and clearance sizes, engagement and screw length, washer and head envelopes across slot travel, and a straight driver path to each fastener in the documented assembly order.
5. **Dimensions the part depends on.** Mark every interface that rests on a photo estimate, allowance or assumption, and check that the part either tolerates the error (slot, drill-at-assembly, shim) or is flagged to measure before printing.
6. **First layer and warping.** Bed footprint, long thin features, brim and plate position.

The auditor reads the generator, exported STL/STEP, renders, orientation audit and G-code, not the author's conclusions, and changes no files.

Background reading: [Prusa's guide to modeling for 3D printing](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135), [Prusa's PETG guide](https://help.prusa3d.com/article/petg_2059) and [Stratasys Direct's FDM design guide](https://www.stratasys.com/en/stratasysdirect/resources/resource-guides/fused-deposition-modeling).
