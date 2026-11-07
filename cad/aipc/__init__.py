"""Shared library for the AIPC build: part specs, compatibility, assembly, export, rendering.

Every generator and check script imports from here instead of re-implementing
spec lookup, file layout, STEP/STL export or image rendering.

    from aipc import spec          # parts/<category>/<id>/part.toml lookups
    from aipc import paths         # repository locations
    from aipc.export import export_print, export_component
    from aipc.registry import classify_assembly
    from aipc.render import render_views
    from aipc.compat import run_checks
"""
