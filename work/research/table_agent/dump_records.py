#!/usr/bin/env python3
"""Print binary/EUC-JP anatomy for selected fixed-size records."""

from __future__ import annotations

import argparse
from pathlib import Path


def render_ascii(blob: bytes) -> str:
    return "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in blob)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("record_size", type=lambda x: int(x, 0))
    ap.add_argument("indices", nargs="+", type=lambda x: int(x, 0))
    ap.add_argument("--width", type=int, default=16)
    ns = ap.parse_args()
    data = ns.path.read_bytes()
    print(f"file={ns.path} size={len(data)} record_size={ns.record_size} count={len(data)//ns.record_size} rem={len(data)%ns.record_size}")
    for index in ns.indices:
        base = index * ns.record_size
        rec = data[base : base + ns.record_size]
        print(f"\n== record {index} @0x{base:X} ==")
        for off in range(0, len(rec), ns.width):
            row = rec[off : off + ns.width]
            print(f"{off:04X}: {row.hex(' '):<{ns.width*3-1}}  {render_ascii(row)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
