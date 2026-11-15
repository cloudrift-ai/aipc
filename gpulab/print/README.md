# Print plates

One plate, printed twice: [01_gpulab_baseboard](01_gpulab_baseboard.3mf), the 13-position GPU baseboard, in Duramic PETG on the first-generation Qidi X-Plus (0.4 mm nozzle). OrcaSlicer 2.5.1 estimates 1 d 5 h 30 min and 193 g per print.

- The plate prints as installed, nut channels open to the bed, turned 90 degrees so its 258 mm length runs along the 270 mm bed axis with 3.25 mm edge margins.
- It prints **without a brim or skirt** ([profiles/baseboard-no-brim.json](profiles/baseboard-no-brim.json), derived from the shared `printer:process.json`). The channels are open at both ends for the M3 nuts, and a brim would fill their mouths, as happened on the AIPC rear rails. Clean the bed well.
- Over each channel, the 3.4 mm screw slot leaves a 1.5 mm ledge on each side that holds the nuts. Check that the ledges print cleanly and that an M3 nut (5.5 mm across flats) slides along the channel.
- The hex post holes are 6.0 mm across flats (0.25 mm clearance per face), the same as the AIPC rails that fitted the Wurth base snugly.

G-code is not committed. From the repo root:

```bash
make gcode BUILD=gpulab
```

These are **fit prototypes**: the riser board holes are photo estimates. Print one baseboard and dry-fit a riser board, a post and a card before printing the second.
