#!/usr/bin/env python3
"""Build a deterministic inventory for an extracted Wii DATA partition."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def printable_magic(data: bytes) -> str:
    return "".join(chr(value) if 0x20 <= value <= 0x7E else "." for value in data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    records: list[dict[str, object]] = []
    extension_counts: Counter[str] = Counter()
    extension_bytes: Counter[str] = Counter()
    magic_counts: Counter[str] = Counter()
    magic_examples: dict[str, list[str]] = defaultdict(list)

    paths = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda p: p.relative_to(root).as_posix())
    for path in paths:
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        with path.open("rb") as stream:
            head = stream.read(32)
        magic_hex = head[:16].hex().upper()
        magic_ascii = printable_magic(head[:16])
        magic_key = f"{magic_hex}|{magic_ascii}"
        suffix = path.suffix.lower() or "<none>"

        extension_counts[suffix] += 1
        extension_bytes[suffix] += size
        magic_counts[magic_key] += 1
        if len(magic_examples[magic_key]) < 5:
            magic_examples[magic_key].append(relative)

        records.append(
            {
                "path": relative,
                "size": size,
                "sha256": sha256_file(path),
                "extension": suffix,
                "head16_hex": magic_hex,
                "head16_ascii": magic_ascii,
            }
        )

    result = {
        "schema": "arf-disc-inventory-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "root_role": "extracted DATA/files (derivative of immutable RVZ baseline)",
        "file_count": len(records),
        "total_bytes": sum(int(record["size"]) for record in records),
        "extension_summary": [
            {"extension": ext, "count": extension_counts[ext], "bytes": extension_bytes[ext]}
            for ext in sorted(extension_counts, key=lambda item: (-extension_counts[item], item))
        ],
        "magic_summary": [
            {
                "head16": key,
                "count": count,
                "examples": magic_examples[key],
            }
            for key, count in sorted(magic_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "files": records,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(records), "bytes": result["total_bytes"], "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
