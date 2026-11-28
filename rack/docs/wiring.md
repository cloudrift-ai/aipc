# Fan controller wiring

The controller is an [Aqua Computer QUADRO](../parts/aquacomputer-quadro.md) powered by a [generic 12 V + 5 V adapter](../parts/generic-12v-5v-molex-adapter.md). Both sit on the inner top under the lid, in front of the exhaust bank. Every connection plugs in; nothing is crimped or soldered. **Status: design, not bought or tested.**

## Connections

```text
PDU ── 12 V + 5 V adapter ──4-pin Molex──► QUADRO "Power supply"

QUADRO Fan 1 ── Y ─┬─ Y ─┬─ exhaust fan 1
                   │     └─ exhaust fan 2
                   └─ Y ─┬─ exhaust fan 3
                         └─ exhaust fan 4

QUADRO Fan 2 ── ~1 m 4-pin extension (down a rear corner post) ── Y ─┬─ Y ─┬─ intake fan 1
                                                                      │     └─ intake fan 2
                                                                      └─ Y ─┬─ intake fan 3
                                                                            └─ intake fan 4
QUADRO Fan 3, Fan 4: spare

QUADRO temperature input 1 ── exhaust sensor (included, 70 cm lead)
QUADRO USB (9-pin header) ── header-to-USB-A adapter ── Windows laptop, for setup only
```

- **Y-cables:** the Noctua Y-cables from the fan boxes, three per bank (eight come with the fans). Only one fan per bank reports its rpm through them, which is fine: there's no stall alarm.
- **Fan leads:** each NF-A20 has a 200 mm lead, plus the 30 cm extension from its box where a Y-cable is further away. The exhaust bank is next to the QUADRO and needs nothing more. The intake bank is about the cabinet height away, so one standard 4-pin PWM extension carries its channel down; [models/cooling-report.json](../models/cooling-report.json) estimates the run.
- **Power:** QUADRO manual 5.2 gives the pin order: pin 1 +12 V, pins 2–3 GND, pin 4 +5 V. The fans take their 12 V through the QUADRO's outputs (2 A each; a bank draws 0.32 A).
- **Routing:** tie the intake extension along a rear corner post, clear of the rotors and the sliding shelf. Keep the QUADRO's connectors away from bare metal (manual section 4); it can be held down with its M3 screws or double-sided tape.

## Setup (once)

1. Before connecting the QUADRO, check the adapter's Molex plug with a meter: +12 V on pin 1, +5 V on pin 4.
2. On a Windows 10 or newer laptop, install aquasuite (it needs internet to activate). Connect the QUADRO's USB header through the header-to-USB-A adapter and power the QUADRO from its adapter.
3. In aquasuite, under the QUADRO's fans:
   - **Fan 1 (exhaust):** curve controller on temperature sensor 1, 25% at 30 °C rising to 100% at 38 °C.
   - **Fan 2 (intake):** the same curve 5 points higher, 30% to 100%.
   - Both: minimum power 25% with "Hold minimum power" ticked, maximum 100%.
   - Fans 3 and 4: off.
4. Save the settings into the device (the disk symbol in aquasuite), unplug USB and power-cycle the QUADRO. Check that the fans settle to the curve on their own.
5. Unplug the sensor with the fans running and note what the outputs do. The manual doesn't say. If they slow down, raise the minimum power.

## Behaviour if something fails

| Failure | What happens |
| --- | --- |
| Adapter or QUADRO fails | Fans stop. Nothing raises an alarm: check by ear and by the exhaust temperature |
| Sensor unplugged or failed | Not documented; tested in setup step 5 |
| A fan stalls or is unplugged | The others keep running on their curve. Nothing raises an alarm; check the fans when cleaning the intake filters |
| A computer or the switch is off or rebooting | Nothing changes; the QUADRO runs on its own |
