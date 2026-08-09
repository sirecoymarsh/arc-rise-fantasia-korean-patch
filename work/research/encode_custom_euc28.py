#!/usr/bin/env python3
"""Encode UTF-8 Korean text with an ARF custom EUC28 glyph codebook."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CONTROL_RE = re.compile(r"<\$([0-9A-Fa-f]{2})>")


def encode_text(text: str, codebook: dict) -> bytes:
    mapping = {
        char: bytes.fromhex(entry["bytes_hex"])
        for char, entry in codebook["characters"].items()
    }
    output = bytearray()
    cursor = 0
    for match in CONTROL_RE.finditer(text):
        if match.start() > cursor:
            output.extend(encode_plain(text[cursor : match.start()], mapping))
        output.append(int(match.group(1), 16))
        cursor = match.end()
    output.extend(encode_plain(text[cursor:], mapping))
    return bytes(output)


def encode_plain(text: str, mapping: dict[str, bytes]) -> bytes:
    output = bytearray()
    for char in text:
        if char in mapping:
            output.extend(mapping[char])
            continue
        try:
            output.extend(char.encode("euc_jp"))
        except UnicodeEncodeError as exc:
            raise ValueError(f"character is neither codebook-mapped nor EUC-JP encodable: {char!r}") from exc
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("codebook", type=Path)
    parser.add_argument("input_text", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--hex-output", type=Path)
    args = parser.parse_args()
    codebook = json.loads(args.codebook.read_text(encoding="utf-8"))
    text = args.input_text.read_text(encoding="utf-8").rstrip("\r\n")
    encoded = encode_text(text, codebook)
    if b"\0" in encoded:
        raise ValueError("encoded payload contains NUL; use structural terminators outside this tool")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    if args.hex_output:
        args.hex_output.write_text(encoded.hex().upper() + "\n", encoding="ascii")
    print(json.dumps({"characters": len(text), "bytes": len(encoded), "hex": encoded.hex().upper()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
