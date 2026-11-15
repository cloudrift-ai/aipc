"""Part specifications: a shared library plus one reference file per part in each build.

``parts/<category>/<id>/part.toml`` at the repo root is the single source of
truth for what a part is: identity, dimensions, interfaces, datasheets, model
and evidence. A build uses a part through ``<build>/parts/<id>.toml``::

    part = "purchased/<id>"          # the library spec it references
    role = "what it does in this build"
    status = "selected"
    quantity = 2
    systems = ["node"]
    notes = "build-specific notes"    # optional
    on_shelf = false                  # optional

    [dims]                            # optional: add or override dims for this build
    [[requires]]                      # optional: interface changes for this build
    type = "dc-power"                 # updates the library entry of this type,
    load_limited = 400.0              #   or is added when the library has none
    # replaces = "<type>"             # takes over the library entry of another type
    # remove = true                   # drops the library entry of this type
    [assembly]                        # how the build's assembly instances map to this part

``load_all()`` returns the build's parts with the two merged. Generators read
dimensions through ``dim()`` so the CAD can never silently drift from the spec.

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
WEAK_EVIDENCE = ("listing", "review", "photo-estimate", "allowance", "assumed")
EVIDENCE = STRONG_EVIDENCE + WEAK_EVIDENCE + ("unknown",)
STATUSES = ("owned", "ordered", "selected", "candidate", "unspecified", "design")
LIBRARY_FIELDS = ("id", "name", "category")
USAGE_FIELDS = ("part", "role", "status", "quantity", "systems")  # required in a build's <id>.toml
USAGE_SCALARS = ("role", "status", "quantity", "systems", "on_shelf")  # usage values that override the library
USAGE_KEYS = (*USAGE_FIELDS, "notes", "on_shelf", "dims", "provides", "requires", "assembly")


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
    """A library part; with ``use`` set, as one build uses it (``data`` is then the merged spec)."""

    id: str
    category: str
    dir: Path  # the library folder parts/<category>/<id>/
    data: dict = field(repr=False)
    library: dict = field(repr=False, default_factory=dict)  # the library spec alone
    use: dict | None = field(repr=False, default=None)  # the build's <id>.toml
    use_file: Path | None = None

    # Identity -----------------------------------------------------------
    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def status(self) -> str:
        return self.data["status"]

    @property
    def quantity(self) -> int:
        return int(self.data["quantity"])

    @property
    def systems(self) -> list[str]:
        return list(self.data.get("systems", []))  # a library part alone has no systems

    @property
    def role(self) -> str:
        return self.data["role"]

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
            out[key] = Dim(
                key,
                raw.get("value"),
                raw.get("unit", "mm"),
                raw.get("evidence", self.data.get("evidence", "unknown")),
                raw.get("source", ""),
                raw.get("note", ""),
            )
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
    def provides(self) -> list[dict]:
        return self._interfaces("provides")

    @property
    def requires(self) -> list[dict]:
        return self._interfaces("requires")

    # Assembly and files -------------------------------------------------
    @property
    def assembly(self) -> dict:
        return self.data.get("assembly", {})

    @property
    def model_step(self) -> Path:
        return self.dir / f"{self.id}.step"

    @property
    def model_stl(self) -> Path:
        return self.dir / f"{self.id}.stl"

    @property
    def render_png(self) -> Path:
        return self.dir / "render.png"

    @property
    def datasheets(self) -> list[dict]:
        return list(self.data.get("datasheets", []))

    # Build usage --------------------------------------------------------
    @property
    def use_notes(self) -> str:
        return (self.use or {}).get("notes") or ""

    @property
    def page(self) -> Path:
        """Generated page for this part in the current build: parts/<id>.md."""
        return paths.PARTS / f"{self.id}.md"

    @property
    def in_assembly_png(self) -> Path:
        return paths.PART_RENDERS / f"{self.id}.png"

    @property
    def model_build(self) -> str | None:
        """The build whose generator writes and renders this part's model.

        ``[model] build`` in part.toml, else the first build (by name) that uses
        the part. Other builds model the part in their own assembly but never
        write the library copy.
        """
        users = library_users().get(self.id, [])
        return self.data.get("model", {}).get("build") or (users[0] if users else None)

    @property
    def owns_model(self) -> bool:
        return self.model_build == paths.BUILD_ID


def _blank_to_none(obj):
    """TOML has no null; an empty string means 'unknown' everywhere in the specs."""
    if isinstance(obj, dict):
        return {k: _blank_to_none(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_blank_to_none(v) for v in obj]
    return None if obj == "" else obj


def _read(path: Path) -> dict:
    data = tomllib.loads(path.read_text())
    for key in ("dims", "provides", "requires"):
        if key in data:
            data[key] = _blank_to_none(data[key])
    return data


@lru_cache(maxsize=1)
def load_library() -> dict[str, Part]:
    """Every part in the shared library, without any build's usage."""
    parts = {}
    for category in paths.CATEGORIES:
        for toml in sorted((paths.LIBRARY / category).glob("*/part.toml")):
            data = _read(toml)
            part = Part(data.get("id", toml.parent.name), data.get("category", category), toml.parent, data, data)
            assert part.id not in parts, f"duplicate part id {part.id}"
            parts[part.id] = part
    return parts


def _use_files(build: Path) -> list[Path]:
    return sorted((build / "parts").glob("*.toml"))


@lru_cache(maxsize=1)
def library_users() -> dict[str, list[str]]:
    """Library part id -> names of the builds that reference it."""
    users: dict[str, list[str]] = {}
    for build in paths.builds():
        for toml in _use_files(build):
            ref = tomllib.loads(toml.read_text()).get("part", "")
            users.setdefault(ref.rpartition("/")[2], []).append(build.name)
    return users


def _merge_interfaces(base: list[dict], changes: list[dict], where: str) -> list[dict]:
    out = [dict(i) for i in base]
    for change in changes:
        change = dict(change)
        target = change.pop("replaces", None) or change["type"]
        hits = [n for n, i in enumerate(out) if i.get("type") == target]
        if len(hits) > 1:
            raise ValueError(f"{where}: library has several '{target}' entries; a build can only change a unique one")
        if change.pop("remove", False):
            if not hits:
                raise ValueError(f"{where}: remove '{target}' but the library has no such entry")
            del out[hits[0]]
        elif hits:
            out[hits[0]].update(change)
        else:
            if target != change["type"]:
                raise ValueError(f"{where}: replaces '{target}' but the library has no such entry")
            out.append(change)
    return out


def _merge(lib: Part, use: dict, where: str) -> dict:
    data = {k: v for k, v in lib.library.items()}
    for key in USAGE_SCALARS:
        if key in use:
            data[key] = use[key]
    data["dims"] = {**lib.library.get("dims", {}), **use.get("dims", {})}
    for kind in ("provides", "requires"):
        data[kind] = _merge_interfaces(lib.library.get(kind, []), use.get(kind, []), f"{where} {kind}")
    data["assembly"] = use.get("assembly", {})
    return data


@lru_cache(maxsize=1)
def load_all() -> dict[str, Part]:
    """The current build's parts: each <build>/parts/<id>.toml merged over its library spec."""
    library = load_library()
    parts = {}
    for toml in _use_files(paths.ROOT):
        use = _read(toml)
        ref = use.get("part", "")
        lib = library.get(ref.rpartition("/")[2])
        if lib is None or f"{lib.category}/{lib.id}" != ref:
            raise KeyError(f"{toml.relative_to(paths.REPO)}: part = '{ref}' is not in the parts/ library")
        data = _merge(lib, use, str(toml.relative_to(paths.REPO)))
        parts[lib.id] = Part(lib.id, lib.category, lib.dir, data, lib.library, use, toml)
    return parts


def get(part_id: str) -> Part:
    try:
        return load_all()[part_id]
    except KeyError:
        raise KeyError(f"{paths.BUILD_ID} has no parts/{part_id}.toml (library spec: parts/*/{part_id}/part.toml)") from None


def dim(part_id: str, key: str) -> float:
    """Dimension value from a part spec. Use this in generators instead of literals."""
    return get(part_id).dim(key)


def system_spec() -> dict:
    """System-level requirements and keepouts derived from the layout (<build>/system.toml)."""
    return tomllib.loads(paths.SYSTEM.read_text()) if paths.SYSTEM.exists() else {}


def lint(parts: dict[str, Part] | None = None) -> list[str]:
    """Structural problems in the library and the build's part references. Empty means well formed."""
    parts = parts or load_all()
    problems = []
    for lib in load_library().values():
        for key in LIBRARY_FIELDS:
            if key not in lib.library:
                problems.append(f"parts/{lib.category}/{lib.id}: missing field '{key}'")
        for key in USAGE_FIELDS[1:] + ("assembly",):
            if key in lib.library:
                problems.append(f"parts/{lib.category}/{lib.id}: '{key}' belongs in each build's parts/{lib.id}.toml")
        model_build = lib.library.get("model", {}).get("build")
        if model_build and model_build not in [b.name for b in paths.builds()]:
            problems.append(f"parts/{lib.category}/{lib.id}: [model] build '{model_build}' is not a build")
    for p in parts.values():
        where = f"{paths.BUILD_ID}/parts/{p.id}.toml"
        if p.use_file.stem != p.id:
            problems.append(f"{where}: file name does not match part '{p.id}'")
        for key in USAGE_FIELDS:
            if key not in p.use:
                problems.append(f"{where}: missing field '{key}'")
        for key in p.use:
            if key not in USAGE_KEYS:
                problems.append(f"{where}: '{key}' is not a usage field; put it in the library part.toml")
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
