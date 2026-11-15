"""hwkit: shared tooling for the hardware builds in this repo.

Part specs, compatibility, assembly registry, export, rendering, print plates
and slicing. Every build's generators import from here instead of
re-implementing spec lookup, file layout, STEP/STL export or image rendering.
The current build is the folder with build.toml (see hwkit.paths).

    from hwkit import spec          # library part.toml merged with the build's parts/<id>.toml
    from hwkit import paths         # build locations
    from hwkit.export import export_print, export_component
    from hwkit.registry import classify_assembly
    from hwkit.render import render_views
    from hwkit.compat import run_checks
    from hwkit import plates, printers
"""
