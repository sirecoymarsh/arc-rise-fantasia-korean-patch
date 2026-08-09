#!/usr/bin/env python3
"""Measure SSCR absolute-pointer coverage of NUL-terminated text fields."""

from __future__ import annotations

import argparse
import collections
import struct
from pathlib import Path

from explore_tables import scan_nul_strings


def all_occurrences(data: bytes, needle: bytes, end: int) -> list[int]:
    result = []
    pos = 0
    while True:
        pos = data.find(needle, pos, end)
        if pos < 0:
            return result
        result.append(pos)
        pos += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ns = ap.parse_args()
    data = ns.path.read_bytes()
    strings = scan_nul_strings(data)
    first = strings[0][0] if strings else len(data)
    covered = []
    missing = []
    refs = collections.Counter()
    for s, e, text in strings:
        occ = all_occurrences(data, struct.pack(">I", s), min(first, s))
        if occ:
            covered.append((s, e, text, occ))
            refs[len(occ)] += 1
        else:
            missing.append((s, e, text))
    print(f"file={ns.path} size={len(data)} declared=0x{struct.unpack_from('>I', data, 4)[0]:X}")
    print(f"strings={len(strings)} first=0x{first:X} covered={len(covered)} missing={len(missing)} refcounts={dict(refs)}")
    print("covered first/last:")
    for row in (covered[:10] + covered[-10:]):
        print(hex(row[0]), [hex(x) for x in row[3]], repr(row[2]))
    print("missing first/last:")
    for row in (missing[:20] + missing[-20:]):
        print(hex(row[0]), repr(row[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
