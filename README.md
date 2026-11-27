# AI hardware builds

Designs for self-built AI compute, one folder per build. Each build is modeled in CAD and checked for compatibility from the datasheets, and lists what is verified and what is not.

| Build | What it is | Status |
| --- | --- | --- |
| [aipc/](aipc/README.md) | **AIPC**: two AI workstations on one rack shelf. Berserk (EPYC 7702P, 4 × V100) and Kenshin (Ryzen 9 9950X3D, RTX 5090), with printed mounts instead of cases | Fit prototype |
| [gpulab/](gpulab/README.md) | **GPU lab**: seven test GPUs (RTX 3090/4090/5090, R9700, 7900 XTX, Arc Pro B60/B70) on cabled x8 risers from one H12D-8D, on a Hammond shelf | Design; GPUs power-capped |
| [rack/](rack/README.md) | **Rack cooling**: eight 200 mm Noctua fans (4 intake, 4 exhaust) on the cabinet, run by an ESP32/ESPHome controller from intake and exhaust temperature probes | Design; cabinet not identified |

The builds share one [parts library](parts/README.md): each part's spec, datasheet links and model live once in `parts/`, and a build references the parts it uses from its own `parts/<id>.toml` (quantity, role, systems, assembly mapping and build-specific limits). They also share [hwkit](hwkit), a Python package for part specs, compatibility checks, assembly coverage, renders, print plates and slicing, plus the [design process](docs/process.md) and [printing guidelines](docs/printing.md).

## Getting started

Requires Python 3.11+ (the Makefile uses `python3.13`; override with `PYTHON=`) and, for G-code, [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) 2.5.x.

```bash
make setup
```

```bash
make all BUILD=aipc
```

```bash
make gcode BUILD=aipc
```

Run `make help` for every target. Without `BUILD=`, targets run for every build that has a `build.toml`.

Agents: read [AGENTS.md](AGENTS.md); it lists every required step and the per-build notes.

## License

[MIT](LICENSE): covers the code, models, print files and docs.
