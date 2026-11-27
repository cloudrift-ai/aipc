# Rack cooling design notes

## Goal

Move more air through the closed cabinet while keeping noise low. The approach is large, slow fans, with intake low at the front and exhaust at the top. Two DS18B20 probes close the loop, and an ESP32 runs it independently of every computer in the rack.

## Fans

Eight [Noctua NF-A20 PWM](../parts/noctua-nf-a20-pwm.md) fans (200 × 30 mm, 350–800 rpm, 86.46 CFM and 18.1 dB(A) at full speed) in two 2 × 2 banks:

- **Intake:** low on the front door or front panel, blowing in.
- **Exhaust:** in the roof or high on the rear, blowing out.

Each bank is 405 × 405 mm (200 mm frames with 5 mm gaps).

The intake and exhaust banks are **in series**: the same air passes through both. Together they give one bank's airflow with roughly twice the pressure to push past the equipment. Their CFM ratings don't add.

## How much heat this removes

From [models/cooling-report.json](../models/cooling-report.json). All values are allowances, not measurements:

| | Value |
| --- | --- |
| One bank, free air | 4 × 86.46 = 345.8 CFM |
| Derate for guards, grilles and equipment in the path | 0.5 (allowance) |
| Estimated cabinet airflow at full speed | **about 173 CFM** |
| Heat removed at a 10 °C intake-to-exhaust rise | about 980 W |
| … at 15 °C | about **1,470 W** |
| … at 20 °C | about 1,970 W |

Heat removed in W ≈ CFM × rise in °C ÷ 1.76.

Compared with the builds:

- **AIPC** (about 1.3 kW in [aipc/docs/design.md](../../aipc/docs/design.md)) fits at a rise of about 13 °C.
- **gpulab's** 2.4 kW PSU budget needs about a 24 °C rise, too warm for GPU intakes.
- **Both builds together** (about 3.7 kW) need roughly twice the fans, or a high-pressure duct fan on the GPU exhaust.

The heat load is generic for now ([system.toml](../system.toml) leaves it blank), so `make check` reports the heat budget as BLOCKED until a load is set.

**Measure it.** Once installed, the firmware's *Temperature rise* sensor at a known load gives the real airflow: CFM ≈ 1.76 × W ÷ rise. Replace the 0.5 derate in the fan spec with the measured value.

## Fan bank cutouts

You can cut panels to any size, so each fan gets its own cutout and four screw holes on the 154 mm pattern. Coordinates are in mm from the bank centre: u across, v up (intake) or toward the rear (exhaust).

| Fan | Centre | Screw holes |
| --- | --- | --- |
| 1 | (−102.5, 102.5) | (−179.5, 179.5), (−25.5, 179.5), (−179.5, 25.5), (−25.5, 25.5) |
| 2 | (102.5, 102.5) | (25.5, 179.5), (179.5, 179.5), (25.5, 25.5), (179.5, 25.5) |
| 3 | (−102.5, −102.5) | (−179.5, −25.5), (−25.5, −25.5), (−179.5, −179.5), (−25.5, −179.5) |
| 4 | (102.5, −102.5) | (25.5, −25.5), (179.5, −25.5), (25.5, −179.5), (179.5, −179.5) |

Before cutting:

- Noctua doesn't publish the bore diameter or the screw-hole size. Measure the fan you bought, cut the round opening to the bore (not larger than the frame), and drill the screw holes to the size of the included fan screws.
- Use wire fan guards on the outside, not stamped grilles.
- Leave at least 50 mm of clear air on both sides of each bank (a quarter of the fan diameter). Fans pressed against the ceiling, a door or equipment lose most of their airflow.

## Controller

Firmware: [firmware/rack-fans.yaml](../firmware/rack-fans.yaml), ESPHome. Hardware: [wiring.md](wiring.md).

- **Two PWM channels** (intake and exhaust). The intake runs 5% faster (*Intake bias*) to keep slight positive pressure, so dust comes in only through the intake.
- **Fan curve:** each bank's speed is the larger of two demands.
  - The exhaust temperature, ramping from 30 °C (minimum duty) to 42 °C (full).
  - The intake-to-exhaust rise, ramping from 5 °C to 15 °C.

  The minimum duty is 25%. All six values can be changed from the web page or Home Assistant and survive reboots.
- **Smoothing:** speed rises at once and falls at most 2% every 5 s, so the fans don't hunt.
- **Fail-safe:** full speed at boot, on a probe fault, on a fan fault and when *Force full speed* is on. Hardware also defaults to full speed when the ESP32 is not running. Details in [wiring.md](wiring.md#behaviour-if-something-fails).
- **Monitoring:** both temperatures, the rise, both duties, all eight rpm readings, and fan and probe faults. These appear on the built-in web page (port 80) and in Home Assistant through the encrypted native API. Firmware updates go only through encrypted OTA; the web page's upload endpoint is disabled.

## Open items

- **Cabinet not identified** ([rack-cabinet](../parts/rack-cabinet.md)). Panel space for the two banks, the clearances, and where the controller and supply mount are all unknown, so `cabinet-fan-opening` is BLOCKED. Positions in the CAD are provisional.
- **Wi-Fi inside a closed metal cabinet** may be weak with the DevKitC's PCB antenna. Mount the controller near a fan opening or a plastic panel. If the signal is poor, switch to the ESP32-DevKitC-32UE (same board, external antenna connector) and run an antenna outside the cabinet.
- **Probe placement:**
  - Intake probe: about 60 mm inside the intake bank.
  - Exhaust probe: about 60 mm before the exhaust bank, in the airstream, not touching metal.

  Confirm these locations read the real intake and exhaust air once installed.
- **Mains supply:** the GST60A12 needs a C13 outlet on the PDU. `ac-power` is BLOCKED because the rack's mains is not specified.
- **Not built:** the perfboard layout, the controller enclosure (a printed part later, after the cabinet is measured) and the cable lengths.
- **Firmware:** validated with `esphome config` and compiled, but not run on hardware.
