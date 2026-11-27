# Fan controller wiring

The controller is a hand-wired perfboard ([rack-fan-controller-board](../parts/rack-fan-controller-board.md)) carrying an [ESP32-DevKitC-32E](../parts/espressif-esp32-devkitc-32e.md) on female headers. It runs [firmware/rack-fans.yaml](../firmware/rack-fans.yaml). **Status: design, not built or tested.**

## Block diagram

```text
PDU (C13) ── GST60A12 ──12 V, 5.5×2.1 mm──┬── 2 A fuse ──┬── 12 V bus ── pin 2 of fan headers 1–8
                                          │              └── R-78E5.0-1.0 ── 5 V ── DevKitC 5V (J2-19)
                                          └── GND bus ──── pin 1 of fan headers 1–8, DevKitC GND

GPIO18 ─ 1 kΩ ─┬─ 2N3904 base     collector ── pin 4 of headers 1–4 (intake PWM)
              10 kΩ to GND        emitter ──── GND
GPIO19 ─ 1 kΩ ─┬─ 2N3904 base     collector ── pin 4 of headers 5–8 (exhaust PWM)
              10 kΩ to GND        emitter ──── GND

header pin 3 (tach) ──┬── 10 kΩ ── 3V3
                      └── 1 kΩ ─── GPIO (see table)

1-Wire terminal: 3V3 ── DQ (GPIO4, 4.7 kΩ to 3V3) ── GND  ← both DS18B20 probes in parallel
```

## Pin map

| Header | Fan | PWM GPIO | Tach GPIO |
| --- | --- | --- | --- |
| 1 | Intake 1 (top left, seen from the front) | 18 | 34 |
| 2 | Intake 2 (top right) | 18 | 35 |
| 3 | Intake 3 (bottom left) | 18 | 32 |
| 4 | Intake 4 (bottom right) | 18 | 33 |
| 5 | Exhaust 1 (rear left, seen from above) | 19 | 25 |
| 6 | Exhaust 2 (rear right) | 19 | 26 |
| 7 | Exhaust 3 (front left) | 19 | 27 |
| 8 | Exhaust 4 (front right) | 19 | 13 |
| 1-Wire | Both probes | — | DQ on 4 |

Fan header pins follow the 4-wire fan standard: 1 GND, 2 +12 V, 3 tach, 4 PWM. Noctua's wire colours are not the usual black/yellow/green/blue, so wire by pin number.

Why these pins:

- **Classic ESP32:** it has eight hardware pulse counters, one per tach. The S2, S3 and C3 have four or none.
- **GPIO34 and 35** are input-only with no internal pull-up. The board's 10 kΩ pull-ups provide them.
- **Avoided pins:**
  - GPIO36 and 39, because of an ESP32 erratum: short low glitches when some internal analog blocks power up.
  - Strapping pins 0, 2, 5, 12 and 15.
  - Flash pins 6–11.
- **GPIO13 and 27** briefly drive a signal at boot on some chip revisions. The 1 kΩ series resistor limits the current into a fan's open-collector tach.

## Parts on the board

| Qty | Part | Note |
| --- | --- | --- |
| 1 | Perfboard, about 100 × 80 mm | Size is an allowance until laid out |
| 1 | 2 × 19-pin female headers, 2.54 mm, rows 25.4 mm apart | DevKitC socket |
| 8 | 4-pin PC fan headers (2.54 mm, keyed) | One per fan, no splitters |
| 1 | 5.5 × 2.1 mm PCB DC jack, rated 5 A or more | Matches the GST60A12 P1J plug, centre positive |
| 1 | 5 × 20 mm fuse holder and 2 A fast fuse | Protects the perfboard bus |
| 1 | Recom R-78E5.0-1.0 | 8–28 V in, 5 V 1 A out, 91%. Add 10 µF ceramic on input and output |
| 2 | 2N3904 NPN | One per PWM channel |
| 2 + 2 | 1 kΩ and 10 kΩ | Base resistor and base pull-down per channel |
| 8 + 8 | 10 kΩ and 1 kΩ | Tach pull-up and series resistor per fan |
| 1 | 4.7 kΩ | 1-Wire pull-up. Use 2.2 kΩ if the probe cables total more than about 5 m and reads fail |
| 1 | 3-way 5.08 mm screw terminal | 1-Wire: 3V3, DQ, GND |
| 1 | 100 µF electrolytic, 25 V | Across the 12 V bus near the headers |

Use 0.8 mm or thicker tinned wire for the 12 V and GND buses. The total current is under 1 A (8 × 0.08 A for the fans plus about 0.25 A for the converter).

## Behaviour if something fails

| Failure | What happens |
| --- | --- |
| ESP32 unpowered, crashed, resetting or never flashed | Base pull-downs turn both transistors off. The fans see an open PWM line and run at **full speed** |
| A probe unplugged, misread, or reading 85.0 °C | Firmware reports a probe fault and runs both banks at full speed |
| A fan stalls or is unplugged (below 150 rpm for 30 s) | Firmware reports a fan fault and runs the others at full speed. The NF-A20 never drops below about 310 rpm while powered, so 150 rpm is always a fault |
| Wi-Fi lost | Control is local, so nothing changes. Only monitoring stops |
| 12 V supply fails | Fans stop. The GST60A12 has short-circuit, overload, over-voltage and over-temperature protection. Watch for this from the host side, for example a fan fault that goes unavailable in Home Assistant |

## First power-up

1. Before plugging in the DevKitC, power the board from the GST60A12 and measure 12 V on each header (pin 2 to pin 1) and 5 V at the DevKitC socket.
2. Copy `firmware/secrets.example.yaml` to `firmware/secrets.yaml` and fill it in. Then, **with the 12 V supply unplugged**, flash over USB:

   ```bash
   esphome run rack/firmware/rack-fans.yaml
   ```

3. Unplug USB and reconnect 12 V. Never power the DevKitC from USB and the 5V pin at the same time.
4. The log lists the ROM code of each probe it finds. Warm one probe in your hand to tell which is which, enter the codes as `intake_probe` and `exhaust_probe`, and reflash over the air.
5. Check all eight rpm readings at 100% (about 800 rpm) and at the 25% minimum (about 330 rpm). Unplug one fan and confirm a fan fault after 30 s.
