"""Print plates for the rack cooling build.

Run with ``hwkit plates``. The build has no printed parts yet (the controller
enclosure and any fan adapters come after the cabinet is measured), so this writes
an empty job list for the slicer.
"""

from __future__ import annotations

import json

from hwkit import paths

paths.PRINT.mkdir(parents=True, exist_ok=True)
(paths.PRINT / "manifest.json").write_text(json.dumps({"jobs": []}, indent=2) + "\n")
print("plates: no printed parts in", paths.BUILD_ID)
