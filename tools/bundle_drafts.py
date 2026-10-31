#!/usr/bin/env python3
"""Zip a run's tailored CVs and cover letters into one archive.

Used by /nightly to bundle the documents it drafted so the morning report can
point at a single file. Paths are flattened into <company>_<role>/ subfolders so
a CV and its cover letter stay together inside the zip.
"""

from __future__ import annotations

import argparse
import os
import sys
import zipfile


def _arcname(path: str, group: str | None) -> str:
    base = os.path.basename(path)
    return f"{group}/{base}" if group else base


def bundle(paths: list[str], out: str, groups: list[str] | None = None) -> int:
    """Write `paths` into `out`. Returns the number of files actually added."""
    if groups and len(groups) != len(paths):
        raise ValueError("--group must be given once per --file, or not at all")

    pairs = list(zip(paths, groups)) if groups else [(p, None) for p in paths]
    present = [(p, g) for p, g in pairs if os.path.isfile(p)]

    for p, _ in pairs:
        if not os.path.isfile(p):
            print(f"skipped (not found): {p}", file=sys.stderr)

    if not present:
        print("nothing to bundle", file=sys.stderr)
        return 0

    parent = os.path.dirname(os.path.abspath(out))
    os.makedirs(parent, exist_ok=True)

    seen: set[str] = set()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, group in present:
            name = _arcname(path, group)
            # Two jobs at the same company+role would collide inside the zip.
            if name in seen:
                stem, ext = os.path.splitext(name)
                n = 2
                while f"{stem}-{n}{ext}" in seen:
                    n += 1
                name = f"{stem}-{n}{ext}"
            seen.add(name)
            zf.write(path, arcname=name)

    print(f"bundled {len(present)} file(s) -> {out}")
    return len(present)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", action="append", default=[], metavar="PATH",
                    help="a file to include; repeat for each file")
    ap.add_argument("--group", action="append", default=[], metavar="NAME",
                    help="subfolder for the matching --file; repeat in the same order")
    ap.add_argument("--out", required=True, help="output .zip path")
    args = ap.parse_args()

    if not args.file:
        ap.error("at least one --file is required")

    groups = args.group or None
    try:
        added = bundle(args.file, args.out, groups)
    except ValueError as exc:
        ap.error(str(exc))
        return 2
    return 0 if added else 1


if __name__ == "__main__":
    sys.exit(main())
