import os
from pathlib import Path

# hwkit.paths resolves the build at import time; the tests run against the AIPC build.
os.environ.setdefault("HWKIT_BUILD", str(Path(__file__).resolve().parents[1] / "aipc"))
