#!/usr/bin/env python3
"""Locate variable-block battle tutorial records."""

from __future__ import annotations

import collections
from pathlib import Path


PATH = Path("work/disc_extracted/DATA/files/Btl/btl_tutorial.vld")


def decode_field(blob: bytes) -> str:
    raw = blob.split(b"\0", 1)[0]
    try:
        return raw.decode("euc_jp")
    except UnicodeDecodeError:
        return "<binary>"


def main() -> int:
    data = PATH.read_bytes()
    starts = []
    # Record headers are 0x14 bytes and begin on 0x10-byte boundaries.
    # 0x0C is consistently -1 for active entries.
    for pos in range(0, len(data) - 0x170 + 1, 0x10):
        if data[pos + 0x0C : pos + 0x10] != b"\xff\xff\xff\xff":
            continue
        message = decode_field(data[pos + 0x14 : pos + 0x114])
        speaker = decode_field(data[pos + 0x114 : pos + 0x154])
        if message != "<binary>" and (message or speaker):
            starts.append(pos)
    print("count", len(starts))
    print("deltas", collections.Counter(b-a for a,b in zip(starts, starts[1:])).most_common())
    for i, pos in enumerate(starts):
        message = decode_field(data[pos + 0x14 : pos + 0x114])
        speaker = decode_field(data[pos + 0x114 : pos + 0x154])
        trailer = data[pos + 0x154 : pos + 0x170]
        print(f"{i:03} @0x{pos:05X} next={(starts[i+1]-pos if i+1<len(starts) else None)} msg={message!r} speaker={speaker!r} trailer={trailer.hex()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
