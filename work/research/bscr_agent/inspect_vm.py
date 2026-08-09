#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
from pathlib import Path


PTR_OPS = {b"\x1a\xf0\xf1\x5a": "literal", b"\x81\x00\xf3\xf2": "call-target"}


def parse_strings(data: bytes) -> tuple[int, int, dict[int, bytes]]:
    pool_start = struct.unpack_from(">I", data, 0x34)[0]
    bytecode_start = struct.unpack_from(">I", data, 0x3C)[0]
    pool = data[pool_start:bytecode_start]
    strings: dict[int, bytes] = {}
    cursor = 0
    while cursor < len(pool):
        end = pool.find(b"\0", cursor)
        if end < 0:
            break
        if not any(pool[cursor:]):
            break
        strings[cursor] = pool[cursor:end]
        cursor = end + 1
    return pool_start, bytecode_start, strings


def show(data: bytes, target: int, radius: int) -> None:
    _, bytecode_start, strings = parse_strings(data)
    bytecode_size = struct.unpack_from(">I", data, 0x38)[0]
    cells = []
    for index in range(bytecode_size // 16):
        pos = bytecode_start + index * 16
        opcode = data[pos : pos + 4]
        operand = struct.unpack_from(">I", data, pos + 4)[0]
        cells.append((index, pos, opcode, operand, data[pos + 8 : pos + 16]))
    hits = [index for index, _, opcode, operand, _ in cells if opcode == b"\x1a\xf0\xf1\x5a" and operand == target]
    print(f"target={target:#x}, hits={hits}")
    for hit in hits:
        print(f"\n--- instruction {hit} ---")
        for index, pos, opcode, operand, tail in cells[max(0, hit - radius) : hit + radius + 1]:
            meaning = PTR_OPS.get(opcode, "")
            decoded = ""
            if meaning and operand in strings:
                decoded = strings[operand].decode("euc_jp", errors="backslashreplace")
            print(
                f"{index:06d} @{pos:#08x} op={opcode.hex()} operand={operand:#010x} "
                f"tail={tail.hex()} {meaning} {decoded!r}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("target", type=lambda value: int(value, 0))
    parser.add_argument("--radius", type=int, default=30)
    args = parser.parse_args()
    show(args.path.read_bytes(), args.target, args.radius)


if __name__ == "__main__":
    main()
