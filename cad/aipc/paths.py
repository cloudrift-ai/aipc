"""Repository locations. Import these instead of building paths by hand."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "parts"          # one folder per part: part.toml, README, model, renders, datasheets
MODELS = ROOT / "models"        # assembly-level outputs: assembly STEP, reports, layout figures
RENDERS = MODELS / "renders"    # assembly render views
PRINT = ROOT / "print"          # plates, slicer profiles, manifest
CATEGORIES = ("purchased", "printed", "fabricated")
