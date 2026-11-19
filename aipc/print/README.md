# Print plates

Fourteen centered plates for the first-generation **Qidi X-Plus** (270 × 200 mm bed, 0.4 mm nozzle) produce 18 printed pieces: 17 installed parts and one T-nut coupon. Each `.3mf` holds geometry and placement only; the slicer settings are listed per plate in [manifest.json](manifest.json): `printer:<file>` profiles are shared in [hwkit/printers/qidi-x-plus/](../../hwkit/printers/qidi-x-plus/printer.toml), the others are this build's overrides in [profiles/](profiles). Print a plate as many times as its **Prints** column says. The Hammond shelf uses its supplied slides, so the former rail-shim trial plate is retired.

G-code is not committed. Generate it with OrcaSlicer:

```bash
make gcode BUILD=aipc
```

from the repo root, or some plates only, for example `make gcode BUILD=aipc PLATES=05_psu_brackets`. The slicer ([hwkit/slicer.py](../../hwkit/slicer.py)) finds OrcaSlicer 2.5.x on macOS, Linux or Flatpak (set `ORCA` to override). OrcaSlicer 2.5 packs its installed presets into `.opc` files its CLI cannot load, so the Qidi base presets are vendored in [hwkit/printers/qidi-x-plus/orca-2.5.0/](../../hwkit/printers/qidi-x-plus/orca-2.5.0/SOURCE.md) and the slicer passes OrcaSlicer fully flattened presets. It rejects any toolpath that exceeds the profile's temperatures, speeds, accelerations or bed bounds, and writes hashes and estimates to `print/gcode/manifest.json`.

## AIPC print notes

- Motherboard sections use the same process without a skirt ([motherboard-ears.json](profiles/motherboard-ears.json)) so the 3 mm brim fits beside the long parts. The two rear rails (plates 02 and 03) also have **no brim** ([motherboard-rails.json](profiles/motherboard-rails.json)): their GPU-tab groove runs the full rail length, so on the first layer it is part of the outer outline and an outer brim filled it and, on H12D, the hex holes that open into it. Clean the bed well, since these long parts rely on first-layer adhesion alone. A no-brim rear-rail test print adhered and printed well (owner report, 2026-11-14).
- Hammond revision: plate 04 has the compact 50 × 42 × 24 mm GPU rest; plate 08 has the 75 mm rear AIO feet; plate 09 has the mirrored left hose brace. Inspect recess closures, foot/gusset growth and brace slot transitions in their actual plate orientations. Retired shim plate 15 is removed. Test one changed part before printing additional copies.
- All motherboard sections keep their original orientation: screw-head recesses up, no supports. On the two rear rails, the 2 × 2 mm GPU-tab groove spans 1–3 mm behind the motherboard rear edge and faces the bed; its walls start on the bed and its roof closes at print Z2 (first roof layer Z2.2). The regular hex holes are 6.0 mm across flats, 0.25 mm clearance per face; a test print gave a snug fit on the SW5.5 Würth base (owner report, 2026-11-14). H12D hex tips meet this groove; Kenshin holes remain separate. On 2026-11-14 the H12D hex centres moved about 9 mm toward the I/O end, onto the PCIe CEM bracket-screw axes. Earlier H12D rail prints have the old positions and must be reprinted. Inspect the first roof layer, including the pointed H12D intersections, and clean away first-layer excess before checking the fit.
- The PSU brackets, V100 shroud, T-nut coupon and both exhaust flanges sit in hot air. They use **Polymaker HT-PLA-GF** with a **0.4 mm hardened steel nozzle** at 230 °C / 50 °C ([ht-pla-gf-psu.json](../../hwkit/printers/qidi-x-plus/ht-pla-gf-psu.json), [ht-pla-gf-cooling.json](profiles/ht-pla-gf-cooling.json), [polymaker-ht-pla-gf-230c.json](../../hwkit/printers/qidi-x-plus/polymaker-ht-pla-gf-230c.json)). Every other part stays in PETG. Keep the material choice explicit for each plate. The slicer cannot check the nozzle: the stock X-Plus preset always reports `hardened_steel`, so fit the hardened steel nozzle before printing these plates.


| Plate | Contents | Prints | Material | Orca estimate per print |
| --- | --- | ---: | --- | --- |
| [01_atx_mobo_adapter_front](01_atx_mobo_adapter_front.3mf) | Shelf-front motherboard section with two M3 ears; common to both boards | 2 | PETG | 14h 27m 39s, 93.79 g |
| [02_atx_mobo_adapter_rail](02_atx_mobo_adapter_rail.3mf) | ATX rear rail with regular hex base holes and 2 × 2 mm groove | 1 | PETG | 14h 45m 47s, 94.18 g |
| [03_h12d_mobo_adapter_rail](03_h12d_mobo_adapter_rail.3mf) | H12D rear rail with regular hex base holes and 2 × 2 mm groove | 1 | PETG | 14h 40m 27s, 94.30 g |
| [04_gpu_rest](04_gpu_rest.3mf) | Compact 50 × 42 × 24 mm RTX 5090 rest with recessed shelf bolts | 1 | PETG | 5h 39m 20s, 31.82 g |
| [05_psu_brackets](05_psu_brackets.3mf) | Two identical rear PSU brackets | 1 | HT-PLA-GF | 13h 33m 26s, 94.67 g |
| [06_fan140_aio_frame](06_fan140_aio_frame.3mf) | 140 mm fan-flush radiator frame with bearing ledge | 2 | PETG | 11h 30m 16s, 76.14 g |
| [07_fan140_aio_hose_brace](07_fan140_aio_hose_brace.3mf) | 140 mm radiator hose-end brace | 1 | PETG | 6h 37m 23s, 41.69 g |
| [08_fan120_aio_frame](08_fan120_aio_frame.3mf) | 120 mm radiator frame with 75 mm feet bearing on the deck (side AIO) | 2 | PETG | 12h 15m 29s, 79.69 g |
| [09_fan120_aio_hose_brace](09_fan120_aio_hose_brace.3mf) | Mirrored left 120 mm radiator hose-end brace | 1 | PETG | 5h 52m 6s, 36.82 g |
| [10_fan120_aio_center_spacer](10_fan120_aio_center_spacer.3mf) | Flat spacer that keeps the middle 120 mm fan coplanar | 1 | PETG | 3h 49m 53s, 24.91 g |
| [11_tnut_fit_coupon](11_tnut_fit_coupon.3mf) | M4 hammer T-nut pocket test; print before plate 12 | 1 | HT-PLA-GF | 44m 12s, 4.80 g |
| [12_v100_gpu_shroud](12_v100_gpu_shroud.3mf) | One-piece V100 hood with integral 45° fan panel | 1 | HT-PLA-GF | 1d 22h 0m 22s, 407.40 g |
| [13_gpu_exhaust_fan_flange](13_gpu_exhaust_fan_flange.3mf) | Fan outlet to 6-inch duct | 1 | HT-PLA-GF | 16h 13m 18s, 129.75 g |
| [14_gpu_exhaust_roof_flange](14_gpu_exhaust_roof_flange.3mf) | Cabinet inner-ceiling duct flange | 1 | HT-PLA-GF | 17h 1m 6s, 149.81 g |

Estimates are from OrcaSlicer 2.5.0 with the profiles here; your slice will report its own. PETG plates use Duramic PETG at 240 °C / 75 °C. HT-PLA-GF plates use Polymaker HT-PLA-GF at 230 °C / 50 °C and need a **0.4 mm hardened steel nozzle**. All motherboard sections keep their original recesses-up orientation. Plates **02 and 03** print without a brim, because an outer brim filled their full-length groove and the H12D hex holes. They bridge the 2 mm-wide GPU-tab groove facing the bed, positioned 1–3 mm behind the motherboard rear edge. The regular hex holes are 6.0 mm across flats, giving 0.25 mm clearance per face with no elongated adjustment. Point one standoff corner toward the PCB. H12D tips meet the groove; ATX holes stay separate. Inspect the first roof layer at Z2.2 and check the snug fit on a test print after removing brim/first-layer excess. No plate needs supports; the shroud's four internal ribs are permanent and must stay.

Each `.svg` next to a plate shows its layout. [orientation-audit.json](orientation-audit.json) records each part's print orientation. See [docs/printing.md](../../docs/printing.md) for the printer, material and design rules these plates follow, and [docs/assembly.md](../docs/assembly.md) for where each part goes.

These are **fit prototypes**: fit-test one of each bracket against the real hardware before printing the rest.
