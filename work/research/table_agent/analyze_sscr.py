#!/usr/bin/env python3
"""Probe SSCR pointer/reference behavior without modifying inputs."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from explore_tables import scan_nul_strings


def occurrences(data: bytes, needle: bytes, end: int) -> list[int]:
    out = []
    pos = 0
    while True:
        pos = data.find(needle, pos, end)
        if pos < 0:
            return out
        out.append(pos)
        pos += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--limit", type=int, default=100)
    ns = ap.parse_args()
    data = ns.path.read_bytes()
    if data[:4] != b"SSCR":
        raise SystemExit("not SSCR")
    declared_pool = struct.unpack_from(">I", data, 4)[0]
    print(f"size={len(data)} declared_pool=0x{declared_pool:X}")
    for s, e, text in scan_nul_strings(data)[0 : ns.limit]:
        exact_be = occurrences(data, struct.pack(">I", s), min(s, declared_pool))
        exact_le = occurrences(data, struct.pack("<I", s), min(s, declared_pool))
        rel = s - declared_pool
        rel_be = occurrences(data, struct.pack(">I", rel & 0xFFFFFFFF), min(s, declared_pool))
        rel_le = occurrences(data, struct.pack("<I", rel & 0xFFFFFFFF), min(s, declared_pool))
        print(
            f"0x{s:08X} len={e-s:3} text={text!r}\n"
            f"  absBE={[hex(x) for x in exact_be]} absLE={[hex(x) for x in exact_le]} "
            f"rel=0x{rel:X} relBE={[hex(x) for x in rel_be]} relLE={[hex(x) for x in rel_le]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
