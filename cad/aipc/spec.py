"""Part specifications: parts/<category>/<id>/part.toml.

Each part folder is the single source of truth for that part's identity,
dimensions, interfaces, datasheets and evidence. Generators read dimensions
through ``dim()`` so the CAD can never silently drift from the spec.

Every dimension and interface carries an evidence class. Only the strong
classes (measured, datasheet, standard) count as verified; everything else
makes a check provisional.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from . import paths

STRONG_EVIDENCE = ("measured", "datasheet", "standard")
WEAK_EVIDENCE = ("listing", "photo-estimate", "allowance", "assumed")
EVIDENCE = STRONG_EVIDENCE + WEAK_EVIDENCE + ("unknown",)
STATUSES = ("owned", "ordered", "selected", "candidate", "unspecified", "design")
REQUIRED_FIELDS = ("id", "name", "category", "status", "quantity", "systems", "role")


@dataclass(frozen=True)
class Dim:
    key: str
    value: float | str | None
    unit: str
    evidence: str
    source: str
    note: str = ""

    @property
    def strong(self) -> bool:
        return self.evidence in STRONG_EVIDENCE


@dataclass
class Part:
    id: str
    category: str
    dir: Path
    data: dict = field(repr=False)

    # Identity -----------------------------------------------------------
    @property
    def name(self) -> str: return self.data["name"]
    @property
    def status(self) -> str: return self.data["status"]
    @property
    def quantity(self) -> int: return int(self.data["quantity"])
    @property
    def systems(self) -> list[str]: return list(self.data["systems"])
    @property
    def role(self) -> str: return self.data["role"]
    @property
    def mass_kg(self) -> Dim | None:
        return self.dims.get("mass") if "mass" in self.data.get("dims", {}) else None

    # Dimensions ---------------------------------------------------------
    @property
    def dims(self) -> dict[str, Dim]:
        out = {}
        for key, raw in self.data.get("dims", {}).items():
            if not isinstance(raw, dict):
                raw = {"value": raw}
            out[key] = Dim(key, raw.get("value"), raw.get("unit", "mm"),
                           raw.get("evidence", self.data.get("evidence", "unknown")),
                           raw.get("source", ""), raw.get("note", ""))
        return out

    def dim(self, key: str) -> float:
        d = self.dims[key]
        if d.value is None:
            raise ValueError(f"{self.id}.{key} has no value ({d.evidence}); measure or source it first")
        return d.value

    # Interfaces ---------------------------------------------------------
    def _interfaces(self, kind: str) -> list[dict]:
        out = []
        for raw in self.data.get(kind, []):
            item = dict(raw)
            item.setdefault("evidence", self.data.get("evidence", "unknown"))
            item.setdefault("systems", self.systems)
            item["part"] = self.id
            out.append(item)
        return out

    @property
    def provides(self) -> list[dict]: return self._interfaces("provides")
    @property
    def requires(self) -> list[dict]: return self._interfaces("requires")

    # Assembly and files -------------------------------------------------
    @property
    def assembly(self) -> dict: return self.data.get("assembly", {})
    @property
    def model_step(self) -> Path: return self.dir / f"{self.id}.step"
    @property
    def model_stl(self) -> Path: return self.dir / f"{self.id}.stl"
    @property
    def render_png(self) -> Path: return self.dir / "render.png"
    @property
    def datasheets(self) -> list[dict]: return list(self.data.get("datasheets", []))


def _blank_to_none(obj):
    """TOML has no null; an empty string means 'unknown' everywhere in the specs."""
    if isinstance(obj, dict):
        return {k: _blank_to_none(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_blank_to_none(v) for v in obj]
    return None if obj == "" else obj


def _load(path: Path) -> Part:
    data = tomllib.loads(path.read_text())
    for key in ("dims", "provides", "requires"):
        if key in data:
            data[key] = _blank_to_none(data[key])
    return Part(data.get("id", path.parent.name), data.get("category", path.parent.parent.name),
                path.parent, data)


@lru_cache(maxsize=1)
def load_all() -> dict[str, Part]:
    parts = {}
    for category in paths.CATEGORIES:
        for toml in sorted((paths.PARTS / category).glob("*/part.toml")):
            part = _load(toml)
            assert part.id not in parts, f"duplicate part id {part.id}"
            parts[part.id] = part
    return parts


def get(part_id: str) -> Part:
    try:
        return load_all()[part_id]
    except KeyError:
        raise KeyError(f"no parts/*/{part_id}/part.toml") from None


def dim(part_id: str, key: str) -> float:
    """Dimension value from a part spec. Use this in generators instead of literals."""
    return get(part_id).dim(key)


def system_spec() -> dict:
    """System-level requirements derived from the layout (parts/system.toml)."""
    path = paths.PARTS / "system.toml"
    return tomllib.loads(path.read_text()) if path.exists() else {}


def lint(parts: dict[str, Part] | None = None) -> list[str]:
    """Structural problems in the part specs. Empty list means the specs are well formed."""
    parts = parts or load_all()
    problems = []
    for p in parts.values():
        where = f"{p.category}/{p.id}"
        for key in REQUIRED_FIELDS:
            if key not in p.data:
                problems.append(f"{where}: missing field '{key}'")
        if p.data.get("id") != p.dir.name:
            problems.append(f"{where}: id '{p.data.get('id')}' does not match folder name")
        if p.data.get("category") != p.dir.parent.name:
            problems.append(f"{where}: category does not match parent folder")
        if p.data.get("status") not in STATUSES:
            problems.append(f"{where}: status '{p.data.get('status')}' not in {STATUSES}")
        for d in p.dims.values():
            if d.evidence not in EVIDENCE:
                problems.append(f"{where}: dim {d.key} evidence '{d.evidence}' not in {EVIDENCE}")
            if d.evidence in STRONG_EVIDENCE + ("listing", "photo-estimate") and not d.source:
                problems.append(f"{where}: dim {d.key} is '{d.evidence}' but has no source")
        for kind in ("provides", "requires"):
            for item in p._interfaces(kind):
                if "type" not in item:
                    problems.append(f"{where}: {kind} entry without type")
                if item["evidence"] not in EVIDENCE:
                    problems.append(f"{where}: {kind} {item.get('type')} evidence '{item['evidence']}' invalid")
        if p.category == "purchased" and not p.datasheets and p.status != "unspecified":
            if not p.data.get("no_datasheet_reason"):
                problems.append(f"{where}: purchased part needs [[datasheets]] or no_datasheet_reason")
        a = p.assembly
        if not a.get("match") and not a.get("not_modeled") and not a.get("covered_by"):
            problems.append(f"{where}: [assembly] needs match patterns, covered_by or not_modeled reason")
    return problems
