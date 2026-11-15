"""Locations for the current build. Import these instead of building paths by hand.

A build is a folder with a ``build.toml`` (for example ``aipc/``). The build is
found from ``HWKIT_BUILD``, else from the current directory or the running
script's directory, searching upward. The root Makefile runs hwkit inside each
build folder, so ``make`` always picks the right one.
"""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parent
CATEGORIES = ("purchased", "printed", "fabricated")


def find_build_root() -> Path:
    if os.environ.get("HWKIT_BUILD"):
        root = Path(os.environ["HWKIT_BUILD"]).resolve()
        if not (root / "build.toml").is_file():
            raise SystemExit(f"hwkit: HWKIT_BUILD={root} has no build.toml")
        return root
    starts = [Path.cwd()]
    if sys.argv and sys.argv[0]:
        starts.append(Path(sys.argv[0]).resolve().parent)
    for start in starts:
        start = start.resolve()
        for folder in (start, *start.parents):
            if (folder / "build.toml").is_file():
                return folder
    raise SystemExit("hwkit: no build.toml here or above; run from a build folder (for example aipc/) or set HWKIT_BUILD")


ROOT = find_build_root()  # the build folder
BUILD = tomllib.loads((ROOT / "build.toml").read_text())
PARTS = ROOT / "parts"  # one folder per part: part.toml, README, model, renders, datasheets
MODELS = ROOT / "models"  # assembly-level outputs: assembly STEP, reports, layout figures
RENDERS = MODELS / "renders"  # assembly render views
PRINT = ROOT / "print"  # plates, build-specific slicer profiles, manifest
DOCS = ROOT / "docs"
ASSEMBLY_STEP = ROOT / BUILD["assembly_step"] if "assembly_step" in BUILD else None
