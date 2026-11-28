# Fan controller wiring

The controller is a hand-wired perfboard ([rack-fan-controller-board](../parts/rack-fan-controller-board.md)) carrying an [Olimex ESP32-POE](../parts/olimex-esp32-poe.md) on female headers. It runs [firmware/rack-fans.yaml](../firmware/rack-fans.yaml) and talks to the network over wired Ethernet. **Status: design, not built or tested.**

Every outside connection plugs in, with no cables to crimp or solder. The fans plug into keyed 4-pin headers, the 12 V adapter into a DC jack, and the network into the ESP32-POE's own RJ45. The probes' bare leads go into a screw terminal.

## Block diagram

```text
PDU (C13) ── GST60A12 ──12 V, 5.5×2.1 mm──┬── 2 A fuse ──┬── 12 V bus ── pin 2 of fan headers 1–8
                                          │              └── R-78E5.0-1.0 ── 5 V ── ESP32-POE EXT1-1 (+5V)
                                          └── GND bus ──── pin 1 of fan headers 1–8, ESP32-POE EXT1-3 (GND)

ESP32-POE RJ45 ── patch lead ── UniFi Pro Max 16, 1GbE port (no PoE)

GPIO32 ─ 1 kΩ ─┬─ 2N3904 base     collector ── pin 4 of headers 1–4 (intake PWM)
              10 kΩ to GND        emitter ──── GND
GPIO33 ─ 1 kΩ ─┬─ 2N3904 base     collector ── pin 4 of headers 5–8 (exhaust PWM)
              10 kΩ to GND        emitter ──── GND

headers 1–7, pin 3 (tach) ──┬── 10 kΩ ── 3V3 (EXT1-2)
                            └── 1 kΩ ─── GPIO (see table)
header 8, pin 3 (tach) ─────────────── GPIO16 (2.2 kΩ pull-up on the ESP32-POE)

1-Wire terminal: 3V3 ── DQ (GPIO13, 2.2 kΩ pull-up on the ESP32-POE) ── GND  ← both DS18B20 probes in parallel
```

## Pin map

| Header | Fan | PWM GPIO | Tach GPIO | ESP32-POE pin |
| --- | --- | --- | --- | --- |
| 1 | Intake 1 (rear left, seen from above) | 32 | 35 | EXT2-3 |
| 2 | Intake 2 (rear right) | 32 | 36 | EXT2-2 |
| 3 | Intake 3 (front left) | 32 | 34 | EXT2-4 |
| 4 | Intake 4 (front right) | 32 | 4 | EXT1-9 |
| 5 | Exhaust 1 (rear left, seen from above) | 33 | 14 | EXT2-9 |
| 6 | Exhaust 2 (rear right) | 33 | 5 | EXT1-10 |
| 7 | Exhaust 3 (front left) | 33 | 15 | EXT2-8 |
| 8 | Exhaust 4 (front right) | 33 | 16 | EXT2-7 |
| 1-Wire | Both probes | — | DQ on 13 | EXT2-10 |

PWM: GPIO32 is EXT2-6, GPIO33 is EXT2-5. Power: EXT1-1 +5V in, EXT1-2 3.3 V out (for the pull-ups and probes), EXT1-3 GND.

Fan header pins follow the 4-wire fan standard: 1 GND, 2 +12 V, 3 tach, 4 PWM. Noctua's wire colours are not the usual black/yellow/green/blue, so wire by pin number.

Why these pins (from the ESP32-POE rev M2 schematic and PCB nets):

- **Ethernet takes ten pins:** GPIO17 (clock), 12 (PHY power), 18, 19, 21, 22, 23, 25, 26 and 27. The old DevKitC pin map used five of them.
- **Classic ESP32:** it has eight hardware pulse counters, one per tach. The S2, S3 and C3 have four or none. Order the plain WROOM-32E variant; the WROVER variants take GPIO16 and 17 for PSRAM and move the Ethernet clock.
- **PWM on GPIO32 and 33** because they have no pull-up on the ESP32-POE. A pull-up there would turn the transistor on while the ESP32 resets, slowing the fans instead of running them at full speed.
- **Board pull-ups on the tach pins** are fine: GPIO5, 15, 34 and 36 have 10 kΩ, which leaves about 0.3 V at the pin when a fan pulls low through the 1 kΩ series resistor. GPIO16 has 2.2 kΩ, which with 1 kΩ in series would leave about 1 V, too close to the ESP32's logic threshold. So header 8 skips the series resistor and the external pull-up, and the board's 2.2 kΩ is its pull-up (1.5 mA into the fan's open collector).
- **GPIO13's 2.2 kΩ** is the 1-Wire pull-up, the value recommended for long probe cables.
- **GPIO34** is also the ESP32-POE's user button. Pressing it fakes a stall on intake fan 3, so leave it alone.
- **GPIO36** can see short low glitches when some analog blocks power up (an ESP32 erratum). Wi-Fi and the ADC are off and the pulse counter's 13 µs filter drops them.
- **GPIO5 and 15 are strapping pins.** A fan holding them low at power-up only changes SDIO timing and silences the boot log, both harmless. The 1 kΩ series resistors limit the current if they drive a signal at boot.
- **Avoided pins:**
  - GPIO39, which senses the 5 V input through a divider.
  - GPIO0 and 2, strapping pins wired to the board's auto-program circuit; GPIO1 and 3, the USB UART.
  - GPIO6–11, the module's flash.
- **Leave the microSD slot empty:** it shares GPIO14 and 15.

## Parts on the board

| Qty | Part | Note |
| --- | --- | --- |
| 1 | Perfboard, about 100 × 80 mm | Size is an allowance until laid out |
| 2 | 1 × 10-pin female headers, 2.54 mm, rows 25.4 mm apart | ESP32-POE socket. Its RJ45 end faces the board edge so the patch lead has room |
| 8 | 4-pin PC fan headers (2.54 mm, keyed) | One per fan, no splitters |
| 1 | 5.5 × 2.1 mm PCB DC jack, rated 5 A or more | Matches the GST60A12 P1J plug, centre positive |
| 1 | 5 × 20 mm fuse holder and 2 A fast fuse | Protects the perfboard bus |
| 1 | Recom R-78E5.0-1.0 | 8–28 V in, 5 V 1 A out, 91%. Add 10 µF ceramic on input and output |
| 2 | 2N3904 NPN | One per PWM channel |
| 2 + 2 | 1 kΩ and 10 kΩ | Base resistor and base pull-down per channel |
| 7 + 7 | 10 kΩ and 1 kΩ | Tach pull-up and series resistor, headers 1–7 |
| 1 | 3-way 5.08 mm screw terminal | 1-Wire: 3V3, DQ, GND |
| 1 | 100 µF electrolytic, 25 V | Across the 12 V bus near the headers |

Use 0.8 mm or thicker tinned wire for the 12 V and GND buses. The total current is under 1 A (8 × 0.08 A for the fans plus about 0.1 A for the converter).

## Behaviour if something fails

| Failure | What happens |
| --- | --- |
| ESP32 unpowered, crashed, resetting or never flashed | Base pull-downs turn both transistors off. The fans see an open PWM line and run at **full speed** |
| A probe unplugged, misread, or reading 85.0 °C | Firmware reports a probe fault and runs both banks at full speed |
| A fan stalls or is unplugged (below 150 rpm for 30 s) | Firmware reports a fan fault and runs the others at full speed. The NF-A20 never drops below about 310 rpm while powered, so 150 rpm is always a fault |
| Network lost (cable, switch reboot or update) | Control is local, so nothing changes. Only monitoring stops |
| 12 V supply fails | Fans stop. The GST60A12 has short-circuit, overload, over-voltage and over-temperature protection. Watch for this from the host side, for example a fan fault that goes unavailable in Home Assistant |

## First power-up

1. Before plugging in the ESP32-POE, power the board from the GST60A12 and measure 12 V on each header (pin 2 to pin 1) and 5 V at the socket (EXT1-1 to EXT1-3).
2. Copy `firmware/secrets.example.yaml` to `firmware/secrets.yaml` and fill it in. Then, **with the ESP32-POE out of its socket**, flash it over USB:

   ```bash
   esphome run rack/firmware/rack-fans.yaml
   ```

3. Unplug USB, seat the ESP32-POE in its socket, connect the patch lead and power up. Never feed it from USB and EXT1-1 at the same time: they are the same 5 V net. Never plug it into a PoE port: the board is not isolated. Find it in UniFi or Home Assistant by its name, `rack-fans`; later updates go over Ethernet.
4. The log lists the ROM code of each probe it finds. Warm one probe in your hand to tell which is which, enter the codes as `intake_probe` and `exhaust_probe`, and reflash over the air.
5. Check all eight rpm readings at 100% (about 800 rpm) and at the 25% minimum (about 330 rpm). Unplug one fan and confirm a fan fault after 30 s.
