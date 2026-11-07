"""Download each part's [[datasheets]] into parts/<category>/<id>/datasheets/.

Local copies are gitignored: manufacturer PDFs are not ours to redistribute,
so the repository keeps the URLs and the extracted, evidence-tagged values in
part.toml. Existing files are kept; pass --refresh to download again.
A failed download is reported, not fatal: add a working URL or a local copy.

Usage: python cad/fetch_datasheets.py [--refresh] [part-id ...]
"""
from __future__ import annotations

import re
import sys
import urllib.request

from aipc import spec

UA = "Mozilla/5.0 (aipc datasheet fetch)"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def fetch(url: str, dest_base):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        ctype = r.headers.get("Content-Type", "")
    ext = ".pdf" if data[:4] == b"%PDF" or "pdf" in ctype else ".html"
    dest = dest_base.with_suffix(ext)
    dest.write_bytes(data)
    return dest, len(data)


def main(args):
    refresh = "--refresh" in args
    ids = [a for a in args if not a.startswith("--")]
    parts = spec.load_all()
    failures = 0
    for p in ([parts[i] for i in ids] if ids else parts.values()):
        for ds in p.datasheets:
            folder = p.dir / "datasheets"
            folder.mkdir(exist_ok=True)
            base = folder / slug(ds["title"])
            existing = [f for f in folder.glob(base.name + ".*")]
            if existing and not refresh:
                continue
            try:
                dest, size = fetch(ds["url"], base)
                print(f"ok   {p.id}: {dest.name} ({size // 1024} KiB)")
            except Exception as exc:  # network, 403, 404
                failures += 1
                print(f"FAIL {p.id}: {ds['url']} ({exc})")
    print(f"{failures} download(s) failed" if failures else "all datasheets present")


if __name__ == "__main__":
    main(sys.argv[1:])
