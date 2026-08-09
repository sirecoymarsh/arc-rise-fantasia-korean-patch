#!/usr/bin/env python3
"""Count Japanese NUL-string starts modulo a proposed record size."""

from __future__ import annotations

import argparse
import collections
from pathlib import Path

from explore_tables import scan_nul_strings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("record_size", type=lambda x: int(x, 0))
    ns = ap.parse_args()
    data = ns.path.read_bytes()
    strings = scan_nul_strings(data)
    counts = collections.Counter(s % ns.record_size for s, _, _ in strings)
    print(f"size={len(data)} stride={ns.record_size} count={len(data)//ns.record_size} remainder={len(data)%ns.record_size}")
    for off, count in counts.most_common():
        examples = [(hex(s), t) for s, _, t in strings if s % ns.record_size == off][:3]
        print(f"0x{off:04X} {count:4d} {examples}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
