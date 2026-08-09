#!/usr/bin/env python3
"""Extract NUL-terminated EUC-JP display-string candidates from ARF binaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path


def valid_token_length(data: bytes, pos: int) -> int:
    value = data[pos]
    if value in (0x09, 0x0A, 0x0D) or 0x20 <= value <= 0x7E:
        return 1
    if 0xA1 <= value <= 0xFE and pos + 1 < len(data) and 0xA1 <= data[pos + 1] <= 0xFE:
        return 2
    if value == 0x8E and pos + 1 < len(data) and 0xA1 <= data[pos + 1] <= 0xDF:
        return 2
    if (
        value == 0x8F
        and pos + 2 < len(data)
        and 0xA1 <= data[pos + 1] <= 0xFE
        and 0xA1 <= data[pos + 2] <= 0xFE
    ):
        return 3
    return 0


def japanese_count(text: str) -> int:
    count = 0
    for char in text:
        code = ord(char)
        if (
            0x3040 <= code <= 0x30FF
            or 0x3400 <= code <= 0x9FFF
            or 0xFF01 <= code <= 0xFFEF
            or unicodedata.east_asian_width(char) in {"W", "F"}
        ):
            count += 1
    return count


def extract(data: bytes, minimum_japanese: int, minimum_chars: int) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    seen: set[tuple[int, int]] = set()
    pos = 0
    while pos < len(data):
        token_len = valid_token_length(data, pos)
        if not token_len:
            pos += 1
            continue
        start = pos
        cursor = pos
        while cursor < len(data):
            token_len = valid_token_length(data, cursor)
            if not token_len:
                break
            cursor += token_len
        if cursor < len(data) and data[cursor] == 0:
            raw = data[start:cursor]
            try:
                text = raw.decode("euc_jp")
            except UnicodeDecodeError:
                text = ""
            jp = japanese_count(text)
            key = (start, cursor)
            if key not in seen and len(text.strip()) >= minimum_chars and jp >= minimum_japanese:
                records.append(
                    {
                        "offset": start,
                        "byte_length": len(raw),
                        "capacity_to_nul": len(raw),
                        "text": text,
                        "japanese_chars": jp,
                        "raw_hex": raw.hex().upper(),
                    }
                )
                seen.add(key)
            pos = cursor + 1
        else:
            pos = start + 1
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--minimum-japanese", type=int, default=2)
    parser.add_argument("--minimum-chars", type=int, default=2)
    args = parser.parse_args()

    data = args.input.read_bytes()
    records = extract(data, args.minimum_japanese, args.minimum_chars)
    result = {
        "schema": "arf-eucjp-string-candidates-v1",
        "source": str(args.input.resolve()),
        "source_size": len(data),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "encoding": "EUC-JP",
        "candidate_count": len(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidates": len(records), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
