"""System compatibility from the part specs.

Parts declare ``[[provides]]`` and ``[[requires]]`` interfaces. Requirements
are matched to providers of the same ``type`` that share a system
(berserk, kenshin, shelf, rack). Three kinds of rule follow from the fields:

* value:   requirement ``value`` must equal a provider ``value`` or be in its
           ``accepts`` list; a numeric value must lie in provider ``min``..``max``.
* count:   sum of required ``count`` x part quantity must not exceed the
           provided ``count`` x quantity (slots, connectors, standoff holes).
* budget:  sum of ``load`` (or ``load_limited`` when a configured limit is
           relied on) must not exceed provider ``capacity`` x ``derate``.

Statuses: FAIL (declared data conflict), BLOCKED (data missing, cannot
decide), PROVISIONAL (passes on weak evidence or a configured limit),
PASS (passes on measured/datasheet/standard evidence only).
"""
from __future__ import annotations

from collections import defaultdict

from . import spec

ORDER = {"FAIL": 0, "BLOCKED": 1, "PROVISIONAL": 2, "PASS": 3}


def _weak(items) -> list[str]:
    return sorted({f"{i['part']}:{i['type']}({i['evidence']})" for i in items
                   if i["evidence"] not in spec.STRONG_EVIDENCE})


def _shares(a: dict, b: dict) -> bool:
    return bool(set(a["systems"]) & set(b["systems"]))


def _norm(v):
    return v.strip().casefold() if isinstance(v, str) else v


def _value_ok(req, prov):
    """True/False when decidable, None when the provider value is unknown."""
    rv = req.get("value")
    if rv is None and ("min" in req or "max" in req):
        pv = prov.get("value")
        if pv is None:
            return None
        return req.get("min", float("-inf")) <= pv <= req.get("max", float("inf"))
    if rv is None:
        return True
    if isinstance(rv, (int, float)) and "min" not in prov and "max" not in prov and isinstance(prov.get("value"), (int, float)):
        return prov["value"] >= rv  # numeric need vs offered size: provider must be at least as large
    if isinstance(rv, (int, float)) and "value" in prov and prov["value"] is None:
        return None
    if isinstance(rv, (int, float)) and ("min" in prov or "max" in prov):
        if prov.get("min") is None and prov.get("max") is None:
            return None
        return prov.get("min", float("-inf")) <= rv <= prov.get("max", float("inf"))
    accepted = [prov["value"]] if "value" in prov else []
    accepted += prov.get("accepts", [])
    if not accepted:
        return None
    return _norm(rv) in {_norm(a) for a in accepted}


def _qty(parts, item):
    return parts[item["part"]].quantity if item["part"] in parts else 1


def _pseudo_items(parts):
    """Interfaces that are derived rather than declared: shelf mass, system-level needs."""
    reqs, provs = [], []
    for p in parts.values():
        if p.data.get("on_shelf", True) is False:
            continue
        m = p.dims.get("mass")
        reqs.append({"type": "shelf-load", "part": p.id, "systems": ["shelf"],
                     "load": None if m is None else m.value,
                     "evidence": "unknown" if m is None else m.evidence, "unit": "kg",
                     "note": "derived from dims.mass"})
    sysdata = spec.system_spec()
    for kind, out in (("requires", reqs), ("provides", provs)):
        for raw in sysdata.get(kind, []):
            item = dict(raw); item["part"] = "system"
            item.setdefault("evidence", "allowance"); item.setdefault("systems", ["rack"])
            out.append(item)
    return reqs, provs


def run_checks() -> list[dict]:
    parts = spec.load_all()
    provides = [i for p in parts.values() for i in p.provides]
    requires = [i for p in parts.values() for i in p.requires]
    extra_r, extra_p = _pseudo_items(parts)
    requires += extra_r
    provides += extra_p
    results = []

    # Group requirements of one type by the provider set they can draw from.
    groups = defaultdict(list)
    for r in requires:
        provs = [p for p in provides if p["type"] == r["type"] and _shares(r, p)]
        key = (r["type"], tuple(sorted({(p["part"], id(p)) for p in provs})))
        groups[key].append((r, provs))

    for (typ, _), members in sorted(groups.items(), key=lambda kv: kv[0][0]):
        provs = members[0][1]
        reqs = [r for r, _ in members]
        systems = sorted({s for r in reqs for s in r["systems"]})
        base = {"type": typ, "systems": systems,
                "requirers": sorted({r["part"] for r in reqs}),
                "providers": sorted({p["part"] for p in provs})}
        if not provs:
            if all(r.get("optional") for r in reqs):
                continue
            results.append({**base, "rule": "presence", "status": "BLOCKED",
                            "detail": f"nothing in systems {systems} provides '{typ}'"})
            continue

        # Value rule, per requirement.
        for r in reqs:
            if r.get("value") is None and "min" not in r and "max" not in r:
                continue
            if r.get("value") is None:
                r = {**r, "value": f"{r.get('min', '')}..{r.get('max', '')}"}
                verdicts = [_value_ok({k: v for k, v in r.items() if k != "value"}, p) for p in provs]
            else:
                verdicts = None
            if verdicts is None:
                verdicts = [_value_ok(r, p) for p in provs]
            if any(v is True for v in verdicts):
                ok = [p for p, v in zip(provs, verdicts) if v]
                status = "PASS" if not _weak([r, *ok]) else "PROVISIONAL"
                detail = f"{r['part']} needs {r['value']}; provided by {', '.join(sorted({p['part'] for p in ok}))}"
            elif any(v is None for v in verdicts):
                status, detail = "BLOCKED", f"{r['part']} needs {r['value']}; provider value unknown"
            else:
                offered = sorted({str(p['value']) if p.get('value') is not None else ', '.join(map(str, p.get('accepts', []))) for p in provs})
                status, detail = "FAIL", f"{r['part']} needs {r['value']}; providers offer {offered}"
            results.append({**base, "rule": "value", "status": status, "detail": detail,
                            "requirers": [r["part"]], "note": r.get("note", ""),
                            "weak_evidence": _weak([r, *provs])})

        # Count rule, per required value.
        counted = [r for r in reqs if "count" in r]
        by_value = defaultdict(list)
        for r in counted:
            by_value[_norm(r.get("value"))].append(r)
        for value, rs in by_value.items():
            need = sum(r["count"] * _qty(parts, r) for r in rs)
            ok_provs = [p for p in provs if _value_ok(rs[0], p) is not False and "count" in p]
            if not ok_provs or any(p["count"] is None for p in ok_provs):
                status, have = "BLOCKED", None
            else:
                have = sum(p["count"] * _qty(parts, p) for p in ok_provs)
                weak = _weak([*rs, *ok_provs])
                status = "FAIL" if need > have else ("PROVISIONAL" if weak else "PASS")
            results.append({**base, "rule": "count", "status": status,
                            "detail": f"need {need} x {typ}{'=' + str(value) if value else ''}, have {have}",
                            "requirers": sorted({r['part'] for r in rs}),
                            "weak_evidence": _weak([*rs, *ok_provs])})

        # Budget rule.
        cap_provs = [p for p in provs if "capacity" in p]
        loaded = [r for r in reqs if "load" in r or "load_limited" in r]
        if cap_provs and loaded:
            missing = [r["part"] for r in loaded if r.get("load_limited", r.get("load")) is None]
            capacity = sum((p["capacity"] or 0) * _qty(parts, p) for p in cap_provs)
            derate = min(p.get("derate", 1.0) for p in cap_provs)
            limited = [r["part"] for r in loaded if "load_limited" in r]
            total = sum((r.get("load_limited", r.get("load")) or 0) * _qty(parts, r) for r in loaded)
            peak = sum((r.get("load") or r.get("load_limited") or 0) * _qty(parts, r) for r in loaded)
            unit = cap_provs[0].get("unit", "")
            weak = _weak([*loaded, *cap_provs])
            if any(p["capacity"] is None for p in cap_provs):
                status = "BLOCKED"
            elif total > capacity * derate:
                status = "FAIL"
            elif missing:
                status = "BLOCKED"
            elif weak or limited:
                status = "PROVISIONAL"
            else:
                status = "PASS"
            if any(p["capacity"] is None for p in cap_provs):
                detail = f"load {total:.1f} {unit}; capacity unknown"
            else:
              detail = (f"load {total:.1f} {unit} of {capacity:.1f} {unit} x derate {derate} "
                      f"= {capacity * derate:.1f} {unit} ({100 * total / capacity if capacity else 0:.0f}% of rating)")
            if limited:
                detail += f"; relies on configured limits of {sorted(set(limited))}; unlimited peak {peak:.1f} {unit}"
            if missing:
                detail += f"; unknown load for {sorted(set(missing))}"
            # Blame only the parts whose data is missing; everyone else is a contributor.
            results.append({**base, "rule": "budget", "status": status, "detail": detail,
                            "requirers": sorted(set(missing)), "contributors": base["requirers"],
                            "weak_evidence": weak})

    results.sort(key=lambda r: (ORDER[r["status"]], r["type"]))
    return results
