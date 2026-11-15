"""`hwkit` command line, run from a build folder (one with build.toml).

    hwkit cad                 run the build's assembly generator (build.toml [scripts] cad)
    hwkit plates              run the build's plate packer (build.toml [scripts] plates)
    hwkit render [id ...]     render parts and the assembly
    hwkit check               spec lint, compatibility, assembly coverage; writes docs/system-check.md
    hwkit datasheets [--refresh] [id ...]
                              download each part's datasheets (gitignored)
    hwkit slice [plate ...]   slice the plates with OrcaSlicer into print/gcode/ (gitignored)

The root Makefile wraps these: `make all BUILD=aipc`.
"""

from __future__ import annotations

import runpy
import sys

COMMANDS = ("cad", "plates", "render", "check", "datasheets", "slice")


def _run_build_script(kind: str, args: list[str]) -> int:
    from . import paths

    script = paths.BUILD.get("scripts", {}).get(kind)
    if not script:
        raise SystemExit(f"hwkit {kind}: {paths.ROOT / 'build.toml'} has no [scripts] {kind}")
    path = paths.ROOT / script
    sys.argv = [str(path), *args]
    sys.path.insert(0, str(path.parent))  # build scripts import their sibling modules
    runpy.run_path(str(path), run_name="__main__")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help") or argv[0] not in COMMANDS:
        print(__doc__.strip())
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    command, args = argv[0], argv[1:]
    if command in ("cad", "plates"):
        return _run_build_script(command, args)
    if command == "render":
        from . import renders

        renders.main(args)
        return 0
    if command == "check":
        from . import check

        return check.main()
    if command == "datasheets":
        from . import datasheets

        datasheets.main(args)
        return 0
    from . import slicer

    slicer.main(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
