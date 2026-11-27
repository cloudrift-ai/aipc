# Rack cooling: cabinet fans and ESP32 fan controller

Eight 200 mm Noctua NF-A20 PWM fans move air through the SysRacks SP 12.900 acoustic cabinet: four intake under the floor at the front, four exhaust in place of the stock roof fans at the rear. An ESP32 running ESPHome sets their speed from two DS18B20 probes, one at the intake and one at the exhaust. It runs on its own 12 V supply, so cooling doesn't depend on any computer in the rack being on.

**Status: design.** Nothing is bought or built. Fan positions follow the cabinet's outer drawing; its interior is not measured. Airflow and heat removal are estimates from free-air ratings (about 173 CFM, about 1.5 kW at a 15 °C rise), not measurements.

![Assembly renders](models/renders/assembly.png)

## Parts

| Part | Qty | Role |
| --- | --- | --- |
| [Noctua NF-A20 PWM](parts/noctua-nf-a20-pwm.md) | 8 | Two 2 × 2 banks, intake and exhaust |
| [ESP32-DevKitC-32E](parts/espressif-esp32-devkitc-32e.md) | 1 | Controller running ESPHome |
| [DS18B20 waterproof probe](parts/ds18b20-waterproof-probe.md) | 2 | Intake and exhaust air temperature |
| [Mean Well GST60A12-P1J](parts/meanwell-gst60a12-p1j.md) | 1 | 12 V 5 A supply, plugged into the PDU (load about 10.4 W) |
| [Controller board](parts/rack-fan-controller-board.md) | 1 | Perfboard: fuse, 5 V converter, PWM drivers, tach pull-ups, 8 fan headers |
| [Fan and probe cabling](parts/rack-fan-harness.md) | 1 | Extensions sized once the cabinet is known |
| [UniFi Pro Max 16](parts/ubiquiti-usw-pro-max-16.md) | 1 | Rack switch: AIPC onboard 2.5GbE and BMC, 10G SFP+ uplink to the home network |
| [UACC-Pro-Max-16-RM](parts/ubiquiti-uacc-pro-max-16-rm.md) | 1 | 1U rack kit for the half-width switch |
| [SysRacks SP 12.900](parts/rack-cabinet.md) | 1 | 11U acoustic cabinet, 600 × 900 mm; takes eight cutouts (four in the inner top, four in the floor) |

## Docs

- [docs/design.md](docs/design.md): airflow and heat budget, cutout pattern, control strategy, open items
- [docs/wiring.md](docs/wiring.md): schematic, pin map, board parts, failure behaviour, first power-up
- [firmware/rack-fans.yaml](firmware/rack-fans.yaml): ESPHome configuration
- [docs/system-check.md](docs/system-check.md): generated compatibility report

## Build

```bash
make all BUILD=rack
```

```bash
esphome run rack/firmware/rack-fans.yaml
```

The second command needs `rack/firmware/secrets.yaml`, copied from `secrets.example.yaml`.
