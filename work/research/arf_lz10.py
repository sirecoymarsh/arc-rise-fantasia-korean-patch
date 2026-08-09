#!/usr/bin/env python3
"""Nintendo LZ10 decompressor used by Arc Rise Fantasia .cxd/.bin files."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def decompress_lz10(data: bytes) -> bytes:
    if len(data) < 4 or data[0] != 0x10:
        raise ValueError("not an LZ10 stream")
    expected = int.from_bytes(data[1:4], "little")
    source = 4
    output = bytearray()
    while len(output) < expected:
        if source >= len(data):
            raise ValueError(f"truncated flag byte at output {len(output)}/{expected}")
        flags = data[source]
        source += 1
        for bit in range(7, -1, -1):
            if len(output) >= expected:
                break
            if flags & (1 << bit):
                if source + 2 > len(data):
                    raise ValueError("truncated back-reference")
                first, second = data[source], data[source + 1]
                source += 2
                length = (first >> 4) + 3
                distance = (((first & 0x0F) << 8) | second) + 1
                if distance > len(output):
                    raise ValueError(f"invalid distance {distance} at output {len(output)}")
                for _ in range(length):
                    output.append(output[-distance])
                    if len(output) >= expected:
                        break
            else:
                if source >= len(data):
                    raise ValueError("truncated literal")
                output.append(data[source])
                source += 1
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    packed = args.input.read_bytes()
    unpacked = decompress_lz10(packed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(unpacked)
    print(
        f"packed={len(packed)} unpacked={len(unpacked)} "
        f"sha256={hashlib.sha256(unpacked).hexdigest()} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
