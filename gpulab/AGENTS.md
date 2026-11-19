# AGENTS.md

Notes for coding agents working on the GPU lab build. Paths are relative to this `gpulab/` folder. Run `make <target> BUILD=gpulab` from the repo root. Read the repo's [AGENTS.md](../AGENTS.md) first; the workflow is in [docs/process.md](../docs/process.md).

- [cad/layout.py](cad/layout.py) is the only geometry generator. It asserts on collisions, air gaps, riser screws in the baseboard slots, cards on the deck and MCIO cable reach. Fix the layout or the spec when one fails; do not loosen it.
- Card order, air gaps and the start position live in `cad/layout.py`. Each GPU's `gpu-baseboard-position` count in `parts/<id>.toml` is the most positions it may take; keep the two in step.
- The H12D mount sections and the PSU bracket are AIPC library parts built by `hwkit.components.atx_mobo_mount` and `atx_psu_bracket`. The layout rebuilds them and asserts they match the library models; it never exports them. Change their design in hwkit and regenerate AIPC first.
- Both baseboards are one model (`quantity = 2`); baseboard B is a translated copy of A, and the generator asserts it.
- The riser board outline and holes are photo estimates. Replace them in the library's [part.toml](../parts/purchased/cpayne-cp0231-mcio-device-adapter/part.toml) from C-Payne's 3D model or a measured board before printing.
- The power budget passes only with each GPU's `load_limited` cap (set in this build's `parts/<id>.toml`) (see [README.md](README.md#power)). Changing a card or a cap means rechecking the 2,400 W budget; never drop a cap to make a card fit.
- Follow [docs/printing.md](../docs/printing.md) for every printable change.
