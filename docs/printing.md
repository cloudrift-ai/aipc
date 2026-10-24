# 3D printing guidelines

These are the rules every printed part in this repo follows. Use them when you change a part or add a new one, and when you adapt the build to different hardware.

## Printer, slicer and profiles

- Target printer: **first-generation Qidi X-Plus**, 270 × 200 mm bed, **0.4 mm nozzle**, sliced with **OrcaSlicer** using its bundled `Qidi X-Plus 0.4 nozzle` machine preset.
- Default material: **Duramic PETG**, [process.json](../print/profiles/process.json) and [duramic-petg-240c.json](../print/profiles/duramic-petg-240c.json): 0.20 mm layers, 240 °C nozzle (never higher), 75 °C bed, four walls, five top and bottom layers, 40% gyroid infill, 3 mm brim, 5 mm³/s flow limit.
- Conservative speeds: first-layer walls, skirt, brim and infill 15 mm/s; outer walls and top surfaces 25 mm/s; inner walls 30 mm/s; infill 35 mm/s at most; travel 100 mm/s (60 mm/s on the first layer). Acceleration 300 mm/s² for printing, 200 on the first layer and 500 for travel.
- Motherboard sections use the same process without a skirt ([motherboard-ears.json](../print/profiles/motherboard-ears.json)) so the 3 mm brim fits beside the long parts.
- All motherboard sections keep their original orientation: screw-head recesses up, no supports. On the two rear rails, the 2 × 2 mm GPU-tab groove spans 1–3 mm behind the motherboard rear edge and faces the bed; its walls start on the bed and its roof closes at print Z2 (first roof layer Z2.2). The regular hex holes are 5.8 mm across flats for a snug 0.15 mm clearance per face. H12D hex tips meet this groove; Kenshin holes remain separate. Inspect the first roof layer, including the pointed H12D intersections, and clean away brim/first-layer excess before checking the fit. Test-print before relying on physical fit.
- `make gcode` keeps its temporary slicing files inside `print/gcode/` so Flatpak OrcaSlicer and the host share the output directory. Per-plate `.log` files there retain the command, exit status and slicer diagnostics, including when slicing fails.
- Check the nozzle, bed surface, filament dryness and first layer before a long print, and tune a small test piece when anything changes.

## Heat-exposed parts

- The PSU brackets, V100 shroud, T-nut coupon and both exhaust flanges sit in hot air. They use **Polymaker HT-PLA-GF** with a **0.4 mm hardened steel nozzle** at 230 °C / 50 °C ([ht-pla-gf-psu.json](../print/profiles/ht-pla-gf-psu.json), [ht-pla-gf-cooling.json](../print/profiles/ht-pla-gf-cooling.json), [polymaker-ht-pla-gf-230c.json](../print/profiles/polymaker-ht-pla-gf-230c.json)). Every other part stays in PETG. Keep the material choice explicit for each plate.
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
- **Real interfaces first.** Model the real component hole patterns, port clearances and tool access from manufacturer drawings or measurements, mark anything unmeasured as provisional, and use elongated shelf slots for adjustment.

## Printability

- Choose a broad, stable bed face and minimize large unsupported horizontal surfaces. Small or gradual overhangs and short anchored bridges are fine when the sliced preview and a test print look clean; do not add supports or split a sound part just to remove every overhang.
- Prefer gradual tapers, chamfers and printable arches to abrupt ledges or flat ceilings. Check how each layer steps beyond the one below and how a span finally closes; a circular arch can still go flat near its crown. Make sure every newly starting wall or roof has material beneath it.
- Permanent internal ribs are acceptable inside an airflow chamber: a few broad tapered ribs that grow from existing walls and stay in the finished part. Keep fastener and driver paths clear and mark the ribs so nobody removes them.
- Pack parts near the **bed center**, not at the cooler edges. The plate generator keeps 12 mm edge margin and 8 mm between parts before the 3 mm brims (3.25 mm edge margin for the long motherboard sections).

## Checking a change

1. Change the generator in [cad/](../cad), not the exported files. Then regenerate everything that depends on it: `make cad plates gcode`.
2. Review every changed part in its actual print orientation from above, below, both sides and oblique angles, including joints and underside transitions. Step through the sliced layers where features begin, bridge or close. A clean render, a valid solid or a low overhang score is not enough.
3. Have someone (or a separate agent) audit the change independently, fix what they find, and recheck the affected areas.
4. Print one of each changed part and dry-fit it against the real hardware before printing the rest. A successful CAD or slicer check is a prototype review, not a fit approval.

Background reading: [Prusa's guide to modeling for 3D printing](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135), [Prusa's PETG guide](https://help.prusa3d.com/article/petg_2059) and [Stratasys Direct's FDM design guide](https://www.stratasys.com/en/stratasysdirect/resources/resource-guides/fused-deposition-modeling).
