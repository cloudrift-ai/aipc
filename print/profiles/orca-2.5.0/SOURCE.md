# Vendored OrcaSlicer base presets

Unmodified copies of the Qidi system presets that the project profiles in
`print/profiles/*.json` inherit from, taken from
[SoftFever/OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) tag `v2.5.0`
(commit `40ecc66f78ed72dc368e0c1ebe40d77f00cc8a19`), `resources/profiles/Qidi/`.
Contents are unchanged; `Qidi X-Plus 0.4 nozzle.json` is saved as
`Qidi_X-Plus_0.4_nozzle.json` because make cannot handle spaces in file names.
Presets are matched by their internal `name`, not their file name.

OrcaSlicer 2.5.0 packs its installed system presets into opaque `.opc` files,
so its CLI can no longer load them by path or resolve `inherits` against them.
`cad/slice_jobs.py` resolves each `inherits` chain against these files and
passes OrcaSlicer fully flattened presets instead.

OrcaSlicer 2.4.2 resolved `inherits` for the leaf presets only: its logs show
42 machine and 109 process keys loaded, with `fdm_qidi_common` and
`fdm_process_qidi_common` never applied, so settings set only by those parents
fell back to OrcaSlicer's built-in defaults. G-code sliced here applies the
full chain, which changes retraction and wipe (`retraction_speed`, `wipe`,
`wipe_distance`, `retract_before_wipe`, `retract_when_changing_layer`),
automatic Z-hop and first-layer fan delay (`close_fan_the_first_x_layers`).
Test prints made from 2.4.2 G-code are not representative for stringing or
first-layer cooling.

Do not edit these files. Override settings in the project profiles. When moving
to a new OrcaSlicer release, copy the same files from that tag into a new
`orca-<version>/` folder, update `ORCA_BASE` and `ORCA_VERSION` in
`cad/slice_jobs.py`, and diff the flattened presets before re-auditing prints.
