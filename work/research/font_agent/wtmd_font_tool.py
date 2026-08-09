#!/usr/bin/env python3
"""Small, dependency-light WTMD inspector/editor for Arc Rise Fantasia fonts.

The game's EUC28-*.wtm files use a 0x20-byte WTMD header, a 16-color
RGB5A3 palette, and GX C4 (8x8 tiled, two pixels per byte) image data.

This tool deliberately preserves every byte outside the image payload.  A
decode -> encode no-op therefore acts as an exact, deterministic round-trip
test for the part of WTMD needed by the localization project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Sequence

try:
    from PIL import Image, ImageDraw
except ImportError:  # Inspection and exact no-op still work without Pillow.
    Image = None
    ImageDraw = None


GX_FORMAT_NAMES = {
    0x00: "I4",
    0x01: "I8",
    0x02: "IA4",
    0x03: "IA8",
    0x04: "RGB565",
    0x05: "RGB5A3",
    0x06: "RGBA32",
    0x08: "C4",
    0x09: "C8",
    0x0A: "C14X2",
    0x0E: "CMPR",
}

PALETTE_FORMAT_NAMES = {0: "none", 1: "RGB565", 2: "RGB5A3", 3: "IA8"}


@dataclass(frozen=True)
class WTMDHeader:
    path: str
    size: int
    sha256: str
    none: int
    palette_offset: int
    width: int
    height: int
    gx_format: int
    gx_format_name: str
    palette_format: int
    palette_format_name: str
    unknown1: int
    unknown2: int
    unknown3: int
    image_offset: int
    unknown4: int
    image_size: int
    palette_entries: int


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_header(data: bytes, path: str = "") -> WTMDHeader:
    if len(data) < 0x20 or data[:4] != b"WTMD":
        raise ValueError("not a WTMD file")
    none, paloff, width, height = struct.unpack_from(">4H", data, 4)
    gx_format, palette_format, unknown1, unknown2 = struct.unpack_from("4B", data, 12)
    unknown3, image_offset, unknown4 = struct.unpack_from(">3H", data, 16)
    if image_offset > len(data) or paloff > image_offset:
        raise ValueError("invalid WTMD offsets")
    return WTMDHeader(
        path=path,
        size=len(data),
        sha256=sha256(data),
        none=none,
        palette_offset=paloff,
        width=width,
        height=height,
        gx_format=gx_format,
        gx_format_name=GX_FORMAT_NAMES.get(gx_format, f"unknown_{gx_format:02x}"),
        palette_format=palette_format,
        palette_format_name=PALETTE_FORMAT_NAMES.get(
            palette_format, f"unknown_{palette_format:02x}"
        ),
        unknown1=unknown1,
        unknown2=unknown2,
        unknown3=unknown3,
        image_offset=image_offset,
        unknown4=unknown4,
        image_size=len(data) - image_offset,
        palette_entries=(image_offset - paloff) // 2,
    )


def decode_rgb5a3(value: int) -> tuple[int, int, int, int]:
    if value & 0x8000:
        r = (value >> 10) & 0x1F
        g = (value >> 5) & 0x1F
        b = value & 0x1F
        # Match common GX conversion: bit replication rather than truncation.
        return ((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2), 255)
    a = (value >> 12) & 0x7
    r = (value >> 8) & 0xF
    g = (value >> 4) & 0xF
    b = value & 0xF
    return (
        (r << 4) | r,
        (g << 4) | g,
        (b << 4) | b,
        (a << 5) | (a << 2) | (a >> 1),
    )


def read_palette(data: bytes, h: WTMDHeader) -> list[tuple[int, int, int, int]]:
    if h.palette_format != 2:
        raise NotImplementedError("only RGB5A3 palette is implemented")
    return [
        decode_rgb5a3(struct.unpack_from(">H", data, h.palette_offset + i * 2)[0])
        for i in range(h.palette_entries)
    ]


def decode_c4_indices(payload: bytes, width: int, height: int) -> bytearray:
    """Decode GX C4: row-major 8x8 tiles, high nibble then low nibble."""
    if width % 8 or height % 8:
        raise ValueError("GX C4 dimensions must be multiples of 8")
    expected = width * height // 2
    if len(payload) < expected:
        raise ValueError(f"short C4 payload: {len(payload)} < {expected}")
    out = bytearray(width * height)
    pos = 0
    for by in range(0, height, 8):
        for bx in range(0, width, 8):
            for y in range(8):
                row = (by + y) * width + bx
                for xpair in range(4):
                    value = payload[pos]
                    pos += 1
                    out[row + xpair * 2] = value >> 4
                    out[row + xpair * 2 + 1] = value & 0xF
    return out


def encode_c4_indices(indices: Sequence[int], width: int, height: int) -> bytes:
    if width % 8 or height % 8:
        raise ValueError("GX C4 dimensions must be multiples of 8")
    if len(indices) != width * height:
        raise ValueError("index buffer has wrong size")
    out = bytearray(width * height // 2)
    pos = 0
    for by in range(0, height, 8):
        for bx in range(0, width, 8):
            for y in range(8):
                row = (by + y) * width + bx
                for xpair in range(4):
                    hi = indices[row + xpair * 2]
                    lo = indices[row + xpair * 2 + 1]
                    if hi > 15 or lo > 15:
                        raise ValueError("C4 palette index outside 0..15")
                    out[pos] = (hi << 4) | lo
                    pos += 1
    return bytes(out)


def decode_wtmd(data: bytes, path: str = ""):
    h = parse_header(data, path)
    if h.gx_format != 0x08:
        raise NotImplementedError("this helper currently decodes GX C4 only")
    expected = h.width * h.height // 2
    payload = data[h.image_offset : h.image_offset + expected]
    indices = decode_c4_indices(payload, h.width, h.height)
    return h, read_palette(data, h), indices


def exact_noop(data: bytes, path: str = "") -> tuple[bytes, dict]:
    h, _, indices = decode_wtmd(data, path)
    expected = h.width * h.height // 2
    rebuilt = bytearray(data)
    rebuilt[h.image_offset : h.image_offset + expected] = encode_c4_indices(
        indices, h.width, h.height
    )
    result = bytes(rebuilt)
    return result, {
        "input_sha256": sha256(data),
        "output_sha256": sha256(result),
        "exact_match": result == data,
        "size": len(data),
    }


def indices_to_image(
    indices: Sequence[int],
    width: int,
    height: int,
    palette: Sequence[tuple[int, int, int, int]],
):
    if Image is None:
        raise RuntimeError("Pillow is required for PNG output")
    rgba = bytearray(width * height * 4)
    for i, palette_index in enumerate(indices):
        rgba[i * 4 : i * 4 + 4] = bytes(palette[palette_index])
    return Image.frombytes("RGBA", (width, height), bytes(rgba))


def tile_activity(indices: Sequence[int], width: int, height: int, tile: int) -> list[int]:
    if width % tile or height % tile:
        raise ValueError("dimensions are not divisible by tile size")
    counts = []
    for y0 in range(0, height, tile):
        for x0 in range(0, width, tile):
            counts.append(
                sum(
                    1
                    for y in range(y0, y0 + tile)
                    for x in range(x0, x0 + tile)
                    if indices[y * width + x] != 0
                )
            )
    return counts


def cmd_inspect(args) -> None:
    records = []
    for path in args.paths:
        data = path.read_bytes()
        h = parse_header(data, str(path))
        record = asdict(h)
        if h.palette_format == 2:
            record["palette_rgba"] = read_palette(data, h)
        if h.gx_format == 8:
            _, _, idx = decode_wtmd(data, str(path))
            record["used_palette_indices"] = sorted(set(idx))
            record["nonzero_pixels"] = sum(v != 0 for v in idx)
            record["tile_activity"] = {
                str(tile): {
                    "tiles": len(tile_activity(idx, h.width, h.height, tile)),
                    "nonempty": sum(v != 0 for v in tile_activity(idx, h.width, h.height, tile)),
                    "empty": sum(v == 0 for v in tile_activity(idx, h.width, h.height, tile)),
                }
                for tile in (16, 32)
                if h.width % tile == 0 and h.height % tile == 0
            }
        records.append(record)
    output = json.dumps(records, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


def cmd_decode(args) -> None:
    data = args.input.read_bytes()
    h, palette, indices = decode_wtmd(data, str(args.input))
    image = indices_to_image(indices, h.width, h.height, palette)
    if args.grid:
        draw = ImageDraw.Draw(image)
        for x in range(0, h.width, args.grid):
            draw.line((x, 0, x, h.height - 1), fill=(255, 0, 255, 96))
        for y in range(0, h.height, args.grid):
            draw.line((0, y, h.width - 1, y), fill=(255, 0, 255, 96))
    image.save(args.output)


def cmd_noop(args) -> None:
    data = args.input.read_bytes()
    rebuilt, result = exact_noop(data, str(args.input))
    if args.output:
        args.output.write_bytes(rebuilt)
        result["output_path"] = str(args.output)
    print(json.dumps(result, indent=2))
    if not result["exact_match"]:
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect")
    inspect.add_argument("paths", type=Path, nargs="+")
    inspect.add_argument("-o", "--output", type=Path)
    inspect.set_defaults(func=cmd_inspect)

    decode = sub.add_parser("decode")
    decode.add_argument("input", type=Path)
    decode.add_argument("output", type=Path)
    decode.add_argument("--grid", type=int, default=0)
    decode.set_defaults(func=cmd_decode)

    noop = sub.add_parser("noop")
    noop.add_argument("input", type=Path)
    noop.add_argument("-o", "--output", type=Path)
    noop.set_defaults(func=cmd_noop)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
