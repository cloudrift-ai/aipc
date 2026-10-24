# Print plates

Fourteen centered plates for the first-generation **Qidi X-Plus** (270 × 200 mm bed, 0.4 mm nozzle) produce all 18 printed parts: 17 installed parts plus one fit coupon. Each `.3mf` holds geometry and placement only; the slicer settings come from [profiles/](profiles) and are listed per plate in [manifest.json](manifest.json). Print a plate as many times as its **Prints** column says.

G-code is not committed. Generate it with OrcaSlicer:

```bash
make gcode
```

or one plate at a time, for example `make print/gcode/05_psu_brackets.gcode`. The slicer script ([cad/slice_jobs.py](../cad/slice_jobs.py)) finds OrcaSlicer and its bundled `Qidi X-Plus 0.4 nozzle` preset on macOS, Linux or Flatpak; set `ORCA` and `ORCA_MACHINE` to override. It rejects any toolpath that exceeds the profile's temperatures, speeds, accelerations or bed bounds, and writes hashes and estimates to `print/gcode/manifest.json`.

| Plate | Contents | Prints | Material | Orca estimate per print |
| --- | --- | ---: | --- | --- |
| [01_atx_mobo_adapter_front](01_atx_mobo_adapter_front.3mf) | Shelf-front motherboard section with two M3 ears; common to both boards | 2 | PETG | 14 h 30 m, 94 g |
| [02_atx_mobo_adapter_rail](02_atx_mobo_adapter_rail.3mf) | ATX rear rail with regular hex base holes and 2 × 2 mm groove | 1 | PETG | 14 h 51 m, 95 g |
| [03_h12d_mobo_adapter_rail](03_h12d_mobo_adapter_rail.3mf) | H12D rear rail with regular hex base holes and 2 × 2 mm groove | 1 | PETG | 14 h 51 m, 95 g |
| [04_gpu_rest](04_gpu_rest.3mf) | RTX 5090 front-end rest with recessed shelf bolts | 1 | PETG | 9 h 10 m, 51 g |
| [05_psu_brackets](05_psu_brackets.3mf) | Two identical rear PSU brackets | 1 | HT-PLA-GF | about 13 h 30 m, 95 g |
| [06_fan140_aio_frame](06_fan140_aio_frame.3mf) | 140 mm fan-flush radiator frame with bearing ledge | 2 | PETG | 11 h 25 m, 76 g |
| [07_fan140_aio_hose_brace](07_fan140_aio_hose_brace.3mf) | 140 mm radiator hose-end brace | 1 | PETG | 6 h 35 m, 42 g |
| [08_fan120_aio_frame](08_fan120_aio_frame.3mf) | 120 mm fan-flush radiator frame with bearing ledge | 2 | PETG | 10 h 7 m, 66 g |
| [09_fan120_aio_hose_brace](09_fan120_aio_hose_brace.3mf) | 120 mm radiator hose-end brace | 1 | PETG | 5 h 43 m, 36 g |
| [10_fan120_aio_center_spacer](10_fan120_aio_center_spacer.3mf) | Flat spacer that keeps the middle 120 mm fan coplanar | 1 | PETG | 3 h 51 m, 25 g |
| [11_tnut_fit_coupon](11_tnut_fit_coupon.3mf) | M4 hammer T-nut pocket test; print before plate 12 | 1 | HT-PLA-GF | 43 m, 5 g |
| [12_v100_gpu_shroud](12_v100_gpu_shroud.3mf) | One-piece V100 hood with integral 45° fan panel | 1 | HT-PLA-GF | 1 d 21 h 43 m, 404 g |
| [13_gpu_exhaust_fan_flange](13_gpu_exhaust_fan_flange.3mf) | Fan outlet to 6-inch duct | 1 | HT-PLA-GF | 16 h 15 m, 129 g |
| [14_gpu_exhaust_roof_flange](14_gpu_exhaust_roof_flange.3mf) | Cabinet inner-ceiling duct flange | 1 | HT-PLA-GF | 16 h 59 m, 149 g |

Estimates are from OrcaSlicer 2.4.2 with the profiles here; your slice will report its own. PETG plates use Duramic PETG at 240 °C / 75 °C. HT-PLA-GF plates use Polymaker HT-PLA-GF at 230 °C / 50 °C and need a **0.4 mm hardened steel nozzle**. All motherboard sections keep their original recesses-up orientation. Plates **02 and 03** bridge the 2 mm-wide GPU-tab groove facing the bed, positioned 1–3 mm behind the motherboard rear edge. The regular hex holes are 5.8 mm across flats, giving 0.15 mm clearance per face with no elongated adjustment. Point one standoff corner toward the PCB. H12D tips meet the groove; ATX holes stay separate. Inspect the first roof layer at Z2.2 and check the snug fit on a test print after removing brim/first-layer excess. No plate needs supports; the shroud's four internal ribs are permanent and must stay.

Each `.svg` next to a plate shows its layout. [orientation-audit.json](orientation-audit.json) records each part's print orientation. See [docs/printing.md](../docs/printing.md) for the printer, material and design rules these plates follow, and [docs/assembly.md](../docs/assembly.md) for where each part goes.

These are **fit prototypes**: fit-test one of each bracket against the real hardware before printing the rest.
