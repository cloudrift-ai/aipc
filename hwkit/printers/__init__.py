"""Printers and their slicer profiles, shared by every build.

Each printer has a folder ``hwkit/printers/<id>/`` with ``printer.toml`` (bed,
OrcaSlicer version, G-code policy, materials), the vendored OrcaSlicer base
presets and the shared process and filament profiles. A build names its
printer in ``build.toml``.

Plate manifests refer to profiles as ``printer:<file>`` (shared, in the
printer folder) or as a path relative to the build's ``print/`` folder
(build-specific overrides).
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from .. import paths

PRINTERS = Path(__file__).resolve().parent
PREFIX = "printer:"


@dataclass(frozen=True)
class Printer:
    id: str
    dir: Path
    config: dict

    @property
    def name(self) -> str:
        return self.config["name"]

    @property
    def bed(self) -> tuple[float, float]:
        return tuple(self.config["bed_mm"])

    @property
    def orca_base(self) -> Path:
        return self.dir / self.config["orca_base"]

    @property
    def machine_preset(self) -> Path:
        return self.orca_base / "machine" / self.config["machine_preset"]

    @property
    def materials(self) -> dict:
        return self.config.get("materials", {})

    def profile(self, ref: str) -> Path:
        """Resolve a manifest profile reference to a file."""
        if ref.startswith(PREFIX):
            return self.dir / ref.removeprefix(PREFIX)
        return paths.PRINT / ref

    def load_profile(self, ref: str) -> dict:
        return json.loads(self.profile(ref).read_text())


@cache
def get(printer_id: str | None = None) -> Printer:
    """The named printer, or the current build's printer."""
    printer_id = printer_id or paths.BUILD["printer"]
    folder = PRINTERS / printer_id
    return Printer(printer_id, folder, tomllib.loads((folder / "printer.toml").read_text()))
