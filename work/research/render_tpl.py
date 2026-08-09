#!/usr/bin/env python3
"""Decode the GX texture formats used by Arc Rise Fantasia Wii TPL files."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MAGIC = 0x0020AF30


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def be16(b: bytes, o: int) -> int:
    return struct.unpack_from(">H", b, o)[0]


def be32(b: bytes, o: int) -> int:
    return struct.unpack_from(">I", b, o)[0]


def rgb565(v: int) -> tuple[int, int, int, int]:
    r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4),
            (b << 3) | (b >> 2), 255)


def rgb5a3(v: int) -> tuple[int, int, int, int]:
    if v & 0x8000:
        r, g, b = (v >> 10) & 31, (v >> 5) & 31, v & 31
        return ((r << 3) | (r >> 2), (g << 3) | (g >> 2),
                (b << 3) | (b >> 2), 255)
    a, r, g, b = (v >> 12) & 7, (v >> 8) & 15, (v >> 4) & 15, v & 15
    return ((r << 4) | r, (g << 4) | g, (b << 4) | b,
            (a << 5) | (a << 2) | (a >> 1))


def put(px, w: int, h: int, x: int, y: int, c) -> None:
    if x < w and y < h:
        px[x, y] = c


def palette(data: bytes, off: int) -> tuple[list[tuple[int, int, int, int]], dict]:
    count = be16(data, off)
    fmt = be32(data, off + 4)
    payload = be32(data, off + 8)
    colors = []
    for i in range(count):
        v = be16(data, payload + i * 2)
        if fmt == 0:  # IA8
            a, inten = v >> 8, v & 0xFF
            colors.append((inten, inten, inten, a))
        elif fmt == 1:
            colors.append(rgb565(v))
        elif fmt == 2:
            colors.append(rgb5a3(v))
        else:
            raise ValueError(f"unsupported palette format {fmt}")
    return colors, {"palette_count": count, "palette_format": fmt,
                    "palette_data_offset": payload}


def decode(data: bytes, texture_off: int, palette_off: int) -> tuple[Image.Image, dict]:
    h, w = be16(data, texture_off), be16(data, texture_off + 2)
    fmt, pos = be32(data, texture_off + 4), be32(data, texture_off + 8)
    im = Image.new("RGBA", (w, h))
    px = im.load()
    pal, pal_meta = (palette(data, palette_off) if palette_off else ([], {}))
    if fmt == 1:  # I8, 8x4 blocks
        for by in range(0, h, 4):
            for bx in range(0, w, 8):
                for yy in range(4):
                    for xx in range(8):
                        v = data[pos]; pos += 1
                        put(px, w, h, bx + xx, by + yy, (v, v, v, 255))
    elif fmt == 5:  # RGB5A3, 4x4 blocks
        for by in range(0, h, 4):
            for bx in range(0, w, 4):
                for yy in range(4):
                    for xx in range(4):
                        put(px, w, h, bx + xx, by + yy, rgb5a3(be16(data, pos)))
                        pos += 2
    elif fmt == 6:  # RGBA8, tiled 4x4 AR then GB planes
        for by in range(0, h, 4):
            for bx in range(0, w, 4):
                ar = data[pos:pos + 32]
                gb = data[pos + 32:pos + 64]
                pos += 64
                for i in range(16):
                    a, r = ar[i * 2], ar[i * 2 + 1]
                    g, b = gb[i * 2], gb[i * 2 + 1]
                    put(px, w, h, bx + (i % 4), by + (i // 4), (r, g, b, a))
    elif fmt == 9:  # C8, 8x4 blocks
        for by in range(0, h, 4):
            for bx in range(0, w, 8):
                for yy in range(4):
                    for xx in range(8):
                        idx = data[pos]; pos += 1
                        put(px, w, h, bx + xx, by + yy,
                            pal[idx] if idx < len(pal) else (255, 0, 255, 255))
    elif fmt == 14:  # CMPR, 8x8 macroblocks made of four DXT1 blocks
        for by in range(0, h, 8):
            for bx in range(0, w, 8):
                for sy in (0, 4):
                    for sx in (0, 4):
                        c0v, c1v = be16(data, pos), be16(data, pos + 2)
                        bits = be32(data, pos + 4)
                        pos += 8
                        c0, c1 = rgb565(c0v), rgb565(c1v)
                        if c0v > c1v:
                            c2 = tuple((2 * c0[i] + c1[i]) // 3 for i in range(3)) + (255,)
                            c3 = tuple((c0[i] + 2 * c1[i]) // 3 for i in range(3)) + (255,)
                        else:
                            c2 = tuple((c0[i] + c1[i]) // 2 for i in range(3)) + (255,)
                            c3 = (0, 0, 0, 0)
                        colors = (c0, c1, c2, c3)
                        for i in range(16):
                            idx = (bits >> (30 - i * 2)) & 3
                            put(px, w, h, bx + sx + (i % 4), by + sy + (i // 4), colors[idx])
    else:
        raise ValueError(f"unsupported GX texture format {fmt}")
    return im, {"width": w, "height": h, "format": fmt,
                "texture_data_offset": be32(data, texture_off + 8), **pal_meta}


def font(size: int) -> ImageFont.ImageFont:
    p = Path("C:/Windows/Fonts/malgun.ttf")
    return ImageFont.truetype(str(p), size) if p.exists() else ImageFont.load_default()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(args.inputs, key=lambda p: str(p).lower()):
        data = path.read_bytes()
        if be32(data, 0) != MAGIC:
            raise ValueError(f"bad TPL magic: {path}")
        count, table = be32(data, 4), be32(data, 8)
        for i in range(count):
            th, ph = struct.unpack_from(">II", data, table + i * 8)
            image, meta = decode(data, th, ph)
            out = args.output / f"{path.parent.parent.parent.name}_{path.stem}_{i}.png"
            image.save(out)
            rows.append({"source": str(path), "source_sha256": sha256(path),
                         "image_index": i, **meta, "render": str(out),
                         "render_sha256": sha256(out)})
    # Transparent textures are composed over a checkerboard for the visual sheet.
    cell_w, cell_h, label_h, cols = 360, 250, 42, 4
    rows_per = 3
    pages = []
    for page in range(math.ceil(len(rows) / (cols * rows_per))):
        group = rows[page * cols * rows_per:(page + 1) * cols * rows_per]
        sheet = Image.new("RGB", (cell_w * cols, (cell_h + label_h) * rows_per), "white")
        draw = ImageDraw.Draw(sheet)
        for i, row in enumerate(group):
            x, y = (i % cols) * cell_w, (i // cols) * (cell_h + label_h)
            bg = Image.new("RGBA", (cell_w, cell_h), (224, 224, 224, 255))
            bd = ImageDraw.Draw(bg)
            for cy in range(0, cell_h, 16):
                for cx in range(0, cell_w, 16):
                    if (cx // 16 + cy // 16) & 1:
                        bd.rectangle((cx, cy, cx + 15, cy + 15), fill=(180, 180, 180, 255))
            with Image.open(row["render"]) as im:
                im = im.convert("RGBA")
                im.thumbnail((cell_w, cell_h), Image.Resampling.NEAREST)
                bg.alpha_composite(im, ((cell_w - im.width) // 2, (cell_h - im.height) // 2))
            sheet.paste(bg.convert("RGB"), (x, y))
            draw.text((x + 5, y + cell_h + 2),
                      f"{Path(row['source']).name} {row['width']}x{row['height']} fmt={row['format']}",
                      fill="black", font=font(15))
        sp = args.output / f"opening_bnr_tpl_contact_p{page+1:02d}.png"
        sheet.save(sp, optimize=True)
        pages.append({"path": str(sp), "sha256": sha256(sp), "items": len(group)})
    report = {"schema": "arf-ko-tpl-render-v1", "valid": True,
              "texture_count": len(rows), "textures": rows,
              "contact_sheets": pages}
    rp = args.output / "opening_bnr_tpl_render_report.json"
    rp.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"textures": len(rows), "sheets": len(pages),
                      "report": str(rp), "report_sha256": sha256(rp)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
