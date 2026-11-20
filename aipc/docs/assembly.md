# Assembly guide

Use the Hammond RSUS1931BK1 **with its supplied slides**. Retire the StarTech/King Slide adaptation and printed rail shims. The current [assembly](../models/dual-pc-hammond-assembly.step), [drill manifest](../models/mount-hole-manifest.json) and [design notes](design.md) describe a fit prototype; measure actual hardware before drilling.

There are **17 installed printed pieces plus one fit coupon on 14 plates**, and **47 component-to-deck joints: 27 M4 and 20 M3**. Factory shelf/rack mounting hardware is separate. Berserk uses eight motherboard standoffs; Kenshin uses nine.

## Before mounting components

1. Check actual rack-post spacing against Hammond’s current **457.2–711.2 mm** range, mount the empty shelf per its instructions, and check full travel and latches. Confirm rack stability and actual equipment mass against the **39 kg** limit. The conflicting older drawing’s higher rating is not used here.
2. Verify cabinet width, doors and rear depth. The HX1200i overhangs the deck rear by **24.5 mm** and the side radiator by 18 mm. On the left, the Hercules overhangs by 10 mm and the GA II screw heads stop 1 mm inside a 450 mm rail opening; Kenshin's I/O, RTX 5090 and ConnectX ports face the right edge. Front fans extend 16 mm ahead of the deck. Shelf-only 2U mounting / 3U clearance does not include the PC/overhead duct envelope.
3. Dry-place both systems. Kenshin turns 90°: I/O and PCIe brackets face the right shelf edge, PCIe end toward the rear. Unplug its side cables (or use right-angle plugs) before sliding the shelf. Check the 24-pin plug against the V100 hood: the CAD leaves under 0.1 mm there. Check both PSU intake paths, BMC/GPU undersides, H115i TR4/SP3 bracket and cold-plate seating, EPS plugs and all hoses.
4. Survey real deck thickness, folds, underside screws and factory slides. Mark the proposed 47 component holes from positioned bare mounts; remove all electronics, protect slides from chips, drill, deburr and protect exposed steel. Do not drill a motherboard, PSU, radiator, GPU or slide race.

## Fasteners and load paths

- **Ordinary M4 printed mounts:** through-bolt, Ø12 steel washers top/bottom and nut. Use Ø9 washers at the 5090 rest and ≤4 mm heads; combined washer/head height ≤5 mm above its recessed seat. Choose lengths from the real stack.
- **Motherboard anchors:** ten M3 × 16 bolts, Ø7 × 0.5 mm top/back washers and nuts. Six under-PCB anchors go in before the boards. Optional anchors are not in the required count.
- **GPU bases:** ten 14 mm Würth M3 F/F bases pass through plastic and seat on steel. Each uses **M3 × 8 from below, two Ø7 × 0.5 washers and two Ø12 × 1 backing washers**. Nominal 1.52 mm steel gives 3.48 mm engagement and 1.52 mm gap to the owner-reported 9 mm OBT stud. Measure the real stack; hold the SW5.5 base with a wrench, never the plastic. The rod’s fixed lower nut must meet a fully seated card without pulling it into position.
- **V100 tails:** four M4 F/F 20 mm metal spacers with 4 mm silicone pads, fastened from below; support rigid frame surfaces clear of PCB parts.
- **PSUs:** full body depth rests on steel; common printed brackets restrain tipping/sliding through two existing factory screws and two shelf bolts each. Verify thread engagement and seated AC plugs.
- **Side radiator:** the two bearing frames and the brace bolt straight to the deck (no steel extension) with M4 screws, Ø12 × 1 washers top/back and nuts; their slots run along X. Check foot bearing and loaded deflection.

The [access audit](../models/assembly-access-audit.json) checks nominal washer/head and straight-driver envelopes across slot travel, not hands or tool handles. Install every covered shelf bolt before the PCB, radiator or hood blocks it.

## Assembly order

1. **Motherboard mounts:** fit the two keyed 6 mm sections per board. Insert recessed #6-32 standoff screws from below, then 9.525 mm metal standoffs. Use only populated holes: H12D A/C/F/G/H/K/L/M, no B/J; verify X870E holes. Tighten five independent M3 shelf anchors per board before fitting PCBs. Bond a metal standoff on each board to the steel shelf.
2. **GPU hardware:** fit ten metal bases from below, clocking one hex corner toward the board. Fit the OBT rods and metal tail supports. Dry-seat cards to verify bracket tabs, post height, base axes, silicone contact and BMC clearance before tightening retainers.
3. **Compact 5090 rest:** use the revised 50 × 42 × 24 mm block at X107–149, Y639–689 under the card tail. Tighten its recessed shelf bolts before placing the card; ensure it contacts a rigid surface without lifting the card or obstructing fans. It must clear the board.
4. **Front H115i:** bolt bare 140 mm frames first, then support the radiator evenly on both ledges and assemble fans → frame → radiator. Preserve safe factory screw engagement. Fit the independent hose brace loosely to the rear factory threads, then its two shelf bolts, without hose preload.
5. **PSUs:** place both on their sides and fit their common restraint brackets. The HX1200i lies along the rear edge, AC inlet toward −X; its bracket is turned +90°. Check AC plugs, cable bends and fan arrows; retain each PSU’s own modular leads.
6. **Side Lian Li AIO:** bolt the bare frames to the deck along the left edge (anchors X39.3, under the radiator), hose end toward the front. Their 33 mm feet stay inside the radiator footprint; there is no inward brace. Dry-load the supported mounts and check both ledges contact the radiator. Fit radiator → 6 mm frames/center spacer → fans, all coplanar. Account for the added 6 mm and actual washers when choosing safe factory screws. Route the 400 mm hoses from the front tank to the pump with relaxed bends; the CAD route is only a lower length bound.
   **Berserk NIC holder:** in the strip between the radiator's inner face and Kenshin's motherboard mount (owner-measured about 75 mm), bolt the bare plate to the deck with four M4 bolts (anchors at Y477 and Y552, X60.6 on the radiator side and X115.1 on the socket side); the radiator-side bolts are under the card, so fit the plate first. Screw the LRFC6911N riser onto the four bosses with M3 self-tapping screws (board plus 8–10 mm), slot edge toward the radiator and the power-circuit end toward the rack front. Seat the ConnectX card; its full-height bracket stands free in front of the plate. Plug the SATA power into the socket under the rear end of the riser, then the SFF-8643 cable and the QSFP28 DAC.
7. **V100 hood:** tighten its three internal M4 shelf bolts through the bare fan opening. Keep all four internal ribs. Fit a flexible nonconductive seal to the four GPU outlets, without contacting the rotor or live components. Test the T-nut coupon before fitting the pressure fan and flange.
8. **Duct and ceiling flange:** install the fixed roof flange and independently supported 6-inch flexible duct. Keep roof outlets open. The roof height/route are provisional; avoid pulling on the printed fan panel. Make the duct removable for shelf service.
9. **Final mechanical check:** inspect all washer seats, screw tips, GPU seating, fan clearance, plug insertion, cable restraint and frame deflection. Inspect the changed prints and perform a loaded dry fit before power-up.

## Sliding service

**Power down and disconnect all fixed-rack power/data and the roof duct before extending.** No live-service carrier/slack loop is designed. Check the entire 711.2 mm travel empty first; then follow the rack/shelf stability instructions for loaded service. Keep internal cables on the moving shelf and prevent snagging. Reconnect and re-support the duct before restarting.

## Fan wiring and first power-up

- Power the Sanyo Denki fan motor from the PSU through the [fused harness](../parts/fan-power-harness.md) (Molex 12 V, 5 A fuse), never from a motherboard header or directly from a QUADRO output (25 W per channel, below the fan's 37.2 W). Leads: red +12 V, black ground, yellow tach, brown 25 kHz PWM. Only tach, PWM and ground go to the [QUADRO](../parts/aquacomputer-quadro.md); its +12 V pin stays unconnected. An open PWM line runs the fan at full speed, and 0% duty stops it.
- On Linux the `aquacomputer_d5next` driver exposes the QUADRO as hwmon (`pwm1`-`pwm4`, `fan1`-`fan4`). A host service sets the duty from the hottest GPU; it must write 100% on start, on exit and on error, because the QUADRO otherwise holds its last duty.
- Configure full speed at startup and on faults. Control from the hottest GPU, and stop GPU load if tach is lost. Keep leads and seals away from the rotor.
- Check the V100 power adapters' pinout before connecting: the cards take CPU/EPS 8-pin wiring. Never plug a PCIe 8-pin directly into a V100.
- Start at about **180 W per V100** with the fan at full speed. Measure GPU / HBM, hood, base and fan-panel temperatures with the cabinet closed. A loaded printed surface at 50 °C is an inspection trigger, not a rating. Stop for softening, creep, looseness, fan failure, duct collapse, backflow or a loosening joint. Raise power only after a stable sustained test and reinspection.
- Check Berserk's total draw against the PSU and any UPS.
- Test exhaust performance with the roof chamber open to its factory outlets. The pressure fan and the roof fans do not have additive CFM ratings.

The angled EPS projection and BMC/GPU underside clearance remain open physical checks; see [design.md](design.md#physical-release-checks).
