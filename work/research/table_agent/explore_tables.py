#!/usr/bin/env python3
"""One-off structural survey for Arc Rise Fantasia data tables.

This script is intentionally read-only.  It scans likely EUC-JP strings and
prints offsets, terminator locations, and common offset deltas to help infer
record schemas.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


def is_japanese(text: str) -> bool:
    return any(
        "\u3040" <= c <= "\u30ff"
        or "\u3400" <= c <= "\u9fff"
        or "\uff01" <= c <= "\uff60"
        for c in text
    )


def scan_nul_strings(data: bytes, minimum_chars: int = 2):
    out = []
    start = 0
    while start < len(data):
        end = data.find(b"\0", start)
        if end < 0:
            break
        blob = data[start:end]
        if blob:
            try:
                text = blob.decode("euc_jp")
            except UnicodeDecodeError:
                pass
            else:
                if len(text) >= minimum_chars and is_japanese(text):
                    out.append((start, end, text))
        start = end + 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--limit", type=int, default=60)
    ns = ap.parse_args()
    report = {}
    for path in ns.paths:
        data = path.read_bytes()
        strings = scan_nul_strings(data)
        deltas = collections.Counter(
            b[0] - a[0] for a, b in zip(strings, strings[1:]) if b[0] > a[0]
        )
        entry = {
            "path": str(path.resolve()),
            "size": len(data),
            "head_hex": data[:64].hex(" "),
            "string_count": len(strings),
            "common_start_deltas": deltas.most_common(20),
            "strings": [
                {"start": s, "end": e, "byte_length": e - s, "text": t}
                for s, e, t in strings[: ns.limit]
            ],
        }
        report[path.name] = entry
        print(f"\n== {path.name} ({len(data)} bytes, {len(strings)} strings) ==")
        print("head:", entry["head_hex"])
        print("deltas:", entry["common_start_deltas"][:10])
        for s, e, t in strings[: ns.limit]:
            print(f"0x{s:08X}-0x{e:08X} ({e-s:3}) {t!r}")
    if ns.json:
        ns.json.parent.mkdir(parents=True, exist_ok=True)
        ns.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
