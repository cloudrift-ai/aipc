# Print plates

Four plates on the first-generation Qidi X-Plus. The first is this build's own; the other three are AIPC library parts, oriented and sliced the same way as on the AIPC plates, so their 3MF files are identical to AIPC's.

| Plate | Part | Prints | Material and profile |
| --- | --- | ---: | --- |
| [01_gpulab_baseboard](01_gpulab_baseboard.3mf) | 13-position GPU baseboard | 2 | Duramic PETG, [no brim](profiles/baseboard-no-brim.json) |
| [02_h12d_mobo_adapter_rail](02_h12d_mobo_adapter_rail.3mf) | H12D mount section with the I/O-side rail | 1 | Duramic PETG, [rails, no brim](profiles/motherboard-rails.json) |
| [03_atx_mobo_adapter_front](03_atx_mobo_adapter_front.3mf) | H12D mount section on the far side | 1 | Duramic PETG, [no skirt](profiles/motherboard-ears.json) |
| [04_psu_bracket](04_psu_bracket.3mf) | PSU bracket | 1 | HT-PLA-GF, `printer:ht-pla-gf-psu.json`, 0.4 mm hardened nozzle |

The notes and print audit for plates 02–04 are in [AIPC's print README](../../aipc/print/README.md). If AIPC already printed spares of these parts, they fit here unchanged.

## Baseboard

OrcaSlicer 2.5.1 estimates 1 d 5 h 30 min and 193 g per baseboard print.

- The plate prints as installed, nut channels open to the bed, turned 90 degrees so its 258 mm length runs along the 270 mm bed axis with 3.25 mm edge margins.
- It prints **without a brim or skirt** ([profiles/baseboard-no-brim.json](profiles/baseboard-no-brim.json), derived from the shared `printer:process.json`). The channels are open at both ends for the M3 nuts, and a brim would fill their mouths, as happened on the AIPC rear rails. Clean the bed well.
- Over each channel, the 3.4 mm screw slot leaves a 1.5 mm ledge on each side that holds the nuts. Check that the ledges print cleanly and that an M3 nut (5.5 mm across flats) slides along the channel.
- The hex post holes are 6.0 mm across flats (0.25 mm clearance per face), the same as the AIPC rails that fitted the Wurth base snugly.

G-code is not committed. From the repo root:

```bash
make gcode BUILD=gpulab
```

These are **fit prototypes**: the riser board holes are photo estimates. Print one baseboard and dry-fit a riser board, a post and a card before printing the second.
