#!/usr/bin/env python3
"""Collect original B0A1..F4FE glyph IDs used by cataloged EUC-JP text."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def iter_euc_pairs(raw: bytes):
    cursor = 0
    while cursor < len(raw):
        first = raw[cursor]
        if 0xA1 <= first <= 0xFE and cursor + 1 < len(raw) and 0xA1 <= raw[cursor + 1] <= 0xFE:
            yield raw[cursor : cursor + 2]
            cursor += 2
        elif first == 0x8E and cursor + 1 < len(raw) and 0xA1 <= raw[cursor + 1] <= 0xDF:
            cursor += 2
        elif (
            first == 0x8F
            and cursor + 2 < len(raw)
            and 0xA1 <= raw[cursor + 1] <= 0xFE
            and 0xA1 <= raw[cursor + 2] <= 0xFE
        ):
            cursor += 3
        else:
            cursor += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("output_pairs", type=Path)
    parser.add_argument("output_stats", type=Path)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    counts: Counter[str] = Counter()
    for record in catalog["records"]:
        raw = bytes.fromhex(record["raw_hex"])
        for pair in iter_euc_pairs(raw):
            if 0xB0 <= pair[0] <= 0xF4:
                counts[pair.hex().upper()] += 1
    args.output_pairs.parent.mkdir(parents=True, exist_ok=True)
    args.output_pairs.write_text("\n".join(sorted(counts)) + "\n", encoding="ascii")
    stats = {
        "schema": "arf-original-font-reservations-v1",
        "source_catalog": str(args.catalog.resolve()),
        "source_record_count": len(catalog["records"]),
        "reserved_pair_count": len(counts),
        "allocatable_pair_count": 6486,
        "remaining_pair_count": 6486 - len(counts),
        "total_catalog_occurrences": sum(counts.values()),
        "pairs_by_frequency": [
            {"bytes_hex": pair, "count": count}
            for pair, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ],
    }
    args.output_stats.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: stats[key] for key in ("reserved_pair_count", "remaining_pair_count")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
