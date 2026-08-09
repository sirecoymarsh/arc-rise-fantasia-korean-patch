#!/usr/bin/env python3
"""Arc Rise Fantasia EUC28 glyph addressing and Korean codebook helper.

The original renderer uses EUC-JP-like two-byte values as glyph IDs.  The
font atlases are a virtual stream of 828 cells per file (23 x 36 cells), with
each cell measuring 22 x 28 pixels.  Two-byte ranges are padded to 96 slots.

This script does not translate text.  It creates a deterministic custom
two-byte codebook for already-translated Korean text and can inject those
glyphs into copies of the nine original WTMD atlases.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


CELL_WIDTH = 22
CELL_HEIGHT = 28
ATLAS_COLUMNS = 23
ATLAS_ROWS = 36
SLOTS_PER_ATLAS = ATLAS_COLUMNS * ATLAS_ROWS  # 828


def pair_to_global_slot(lead: int, trail: int) -> int:
    """Map the font's supported two-byte ranges to its virtual glyph slot."""
    if not (0xA1 <= trail <= 0xFE):
        raise ValueError("trail byte must be A1..FE")
    if 0xA1 <= lead <= 0xA8:
        # Symbols, full-width Latin, kana, Greek, Cyrillic, box drawing.
        return 1 + (lead - 0xA1) * 96 + (trail - 0xA1)
    if 0xB0 <= lead <= 0xF4:
        # Kanji / vendor-extension area.  A9..AF are not represented.
        return 721 + (lead - 0xB0) * 96 + (trail - 0xA1)
    raise ValueError("lead byte must be A1..A8 or B0..F4")


def global_slot_to_location(slot: int) -> dict:
    if not (0 <= slot < 9 * SLOTS_PER_ATLAS):
        raise ValueError("slot outside nine EUC28 atlases")
    page, local = divmod(slot, SLOTS_PER_ATLAS)
    row, column = divmod(local, ATLAS_COLUMNS)
    return {
        "global_slot": slot,
        "page": page,
        "local_slot": local,
        "column": column,
        "row": row,
        "x": column * CELL_WIDTH,
        "y": row * CELL_HEIGHT,
    }


def allocatable_pairs(reserved_hex: set[str] | None = None) -> Iterable[bytes]:
    """Yield non-reserved cells in the 6,486-code B0..F4 range."""
    reserved_hex = reserved_hex or set()
    for lead in range(0xB0, 0xF5):
        for trail in range(0xA1, 0xFF):
            pair = bytes((lead, trail))
            if pair.hex().upper() not in reserved_hex:
                yield pair


def iter_mapping_entries() -> Iterable[dict]:
    for first, last in ((0xA1, 0xA8), (0xB0, 0xF4)):
        for lead in range(first, last + 1):
            for trail in range(0xA1, 0xFF):
                encoded = bytes((lead, trail))
                try:
                    char = encoded.decode("euc_jp")
                except UnicodeDecodeError:
                    char = None
                entry = {
                    "bytes_hex": encoded.hex().upper(),
                    "euc_jp_character": char,
                }
                entry.update(global_slot_to_location(pair_to_global_slot(lead, trail)))
                yield entry


def extract_hangul(text: str) -> list[str]:
    # Modern syllables plus compatibility/modern jamo frequently used in UI.
    chars = {
        ch
        for ch in text
        if ("\uac00" <= ch <= "\ud7a3")
        or ("\u3130" <= ch <= "\u318f")
        or ("\u1100" <= ch <= "\u11ff")
    }
    return sorted(chars, key=ord)


def extract_custom_glyphs(text: str) -> list[str]:
    """Return every character that needs a custom atlas assignment.

    Hangul always uses the custom mapping.  A reviewed translation can also
    contain intentional Unicode punctuation with no EUC-JP representation
    (currently U+00B7 and U+FF5E); mapping those characters preserves the
    approved text exactly instead of silently normalizing it at insertion.
    """

    required = set(extract_hangul(text))
    for char in set(text):
        try:
            char.encode("euc_jp")
        except UnicodeEncodeError:
            required.add(char)
    return sorted(required, key=ord)


def load_text_inputs(paths: list[Path]) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in paths)


def create_or_extend_codebook(
    required: list[str],
    existing: dict | None = None,
    reserved_hex: set[str] | None = None,
) -> dict:
    """Create an append-only mapping; existing assignments never move."""
    reserved_hex = {h.upper() for h in (reserved_hex or set())}
    mapping = {} if existing is None else dict(existing.get("characters", {}))
    used = {str(v["bytes_hex"]).upper() for v in mapping.values()}
    collision = used & reserved_hex
    if collision:
        raise ValueError(
            "existing codebook collides with newly reserved source pairs: "
            + ", ".join(sorted(collision)[:16])
        )
    pair_iter = (
        p for p in allocatable_pairs(reserved_hex) if p.hex().upper() not in used
    )
    for char in required:
        if char in mapping:
            continue
        try:
            pair = next(pair_iter)
        except StopIteration as exc:
            raise ValueError("Korean glyph set exceeds 6,486 allocatable cells") from exc
        slot = pair_to_global_slot(pair[0], pair[1])
        mapping[char] = {
            "unicode": f"U+{ord(char):04X}",
            "bytes_hex": pair.hex().upper(),
            **global_slot_to_location(slot),
        }
    # Preserve insertion order for old entries; new characters were appended in
    # Unicode order by extract_custom_glyphs().
    return {
        "format": "arc-rise-fantasia-korean-codebook-v1",
        "encoding_contract": (
            "Custom two-byte glyph IDs using B0A1..F4FE; not standard EUC-JP. "
            "A1..A8 symbol/kana area and post-F4 atlas tail remain untouched."
        ),
        "cell": {"width": CELL_WIDTH, "height": CELL_HEIGHT},
        "atlas": {
            "columns": ATLAS_COLUMNS,
            "rows": ATLAS_ROWS,
            "slots_per_file": SLOTS_PER_ATLAS,
            "files": 9,
        },
        "capacity": 6486,
        "reserved_source_pairs": len(reserved_hex),
        "available_after_reservations": 6486 - len(reserved_hex),
        "assigned": len(mapping),
        "characters": mapping,
    }


def reserve_pairs_from_text(text: str) -> set[str]:
    """Reserve double-byte cells needed to keep untranslated EUC-JP readable."""
    result: set[str] = set()
    for char in set(text):
        try:
            encoded = char.encode("euc_jp")
        except UnicodeEncodeError:
            continue
        if (
            len(encoded) == 2
            and 0xB0 <= encoded[0] <= 0xF4
            and 0xA1 <= encoded[1] <= 0xFE
        ):
            result.add(encoded.hex().upper())
    return result


def load_reserved_hex(paths: list[Path]) -> set[str]:
    result: set[str] = set()
    for path in paths:
        # Accept whitespace/comma-separated values, one-pair-per-line files, or
        # catalog snippets containing raw two-byte hex tokens.
        raw = path.read_text(encoding="utf-8")
        for token in raw.replace(",", " ").split():
            token = token.strip().upper().removeprefix("0X")
            if (
                len(token) == 4
                and all(c in "0123456789ABCDEF" for c in token)
                and 0xB0 <= int(token[:2], 16) <= 0xF4
                and 0xA1 <= int(token[2:], 16) <= 0xFE
            ):
                result.add(token)
    return result


def load_wtmd_tool(path: Path):
    spec = importlib.util.spec_from_file_location("arf_wtmd_font_tool", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def render_glyph_indices(
    char: str,
    font,
    palette: list[tuple[int, int, int, int]],
    supersample: int = 4,
) -> bytearray:
    """Rasterize one Korean glyph into a 22x28 C4 palette-index cell.

    The original palette stores an opaque grayscale fill (indices 8..15) and
    black alpha steps (indices 1..7) suitable for a one-pixel outline.  We
    create fill and outline coverage masks, then select the closest original
    palette RGBA value.  No palette entry is modified.
    """
    if Image is None:
        raise RuntimeError("Pillow is required for glyph injection")
    w, h = CELL_WIDTH * supersample, CELL_HEIGHT * supersample
    fill = Image.new("L", (w, h), 0)
    outline = Image.new("L", (w, h), 0)
    df = ImageDraw.Draw(fill)
    do = ImageDraw.Draw(outline)
    # Anchor on the typographic center.  Korean fonts can have asymmetric bbox
    # bearings, so use textbbox to center the actual ink rather than advance.
    bbox = df.textbbox((0, 0), char, font=font, stroke_width=0)
    ink_w, ink_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - ink_w) // 2 - bbox[0]
    y = (h - ink_h) // 2 - bbox[1]
    stroke = supersample
    do.text((x, y), char, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
    df.text((x, y), char, font=font, fill=255)
    fill = fill.resize((CELL_WIDTH, CELL_HEIGHT), Image.Resampling.LANCZOS)
    outline = outline.resize((CELL_WIDTH, CELL_HEIGHT), Image.Resampling.LANCZOS)

    opaque_gray = [i for i, (r, g, b, a) in enumerate(palette) if a == 255]
    alpha_black = [i for i, (r, g, b, a) in enumerate(palette) if r == g == b == 0]

    def nearest_fill(value: int) -> int:
        if value <= 2:
            return 0
        target = int(round(value * 222 / 255))
        return min(opaque_gray, key=lambda i: abs(palette[i][0] - target))

    def nearest_outline(value: int) -> int:
        if value <= 2:
            return 0
        return min(alpha_black, key=lambda i: abs(palette[i][3] - value))

    result = bytearray(CELL_WIDTH * CELL_HEIGHT)
    fp = fill.load()
    op = outline.load()
    for yy in range(CELL_HEIGHT):
        for xx in range(CELL_WIDTH):
            f = fp[xx, yy]
            o = op[xx, yy]
            # Fill wins; outline is the excess silhouette around it.
            idx = nearest_fill(f) if f > 8 else nearest_outline(max(0, o - f))
            result[yy * CELL_WIDTH + xx] = idx
    return result


def inject_fonts(
    source_dir: Path,
    output_dir: Path,
    codebook: dict,
    font_path: Path,
    font_size: int,
    wtmd_tool_path: Path,
) -> dict:
    if ImageFont is None:
        raise RuntimeError("Pillow is required for glyph injection")
    tool = load_wtmd_tool(wtmd_tool_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    for page in range(9):
        source = source_dir / f"EUC28-{page}.wtm"
        data = source.read_bytes()
        h, palette, indices = tool.decode_wtmd(data, str(source))
        pages.append([source, data, h, palette, indices])

    # Pillow expects size in pixels.  Render at supersampled font size so the
    # final 22x28 cell retains smooth edges.
    font = ImageFont.truetype(str(font_path), font_size * 4)
    changed_pages: set[int] = set()
    for char, record in codebook["characters"].items():
        page = int(record["page"])
        x, y = int(record["x"]), int(record["y"])
        _, _, h, palette, indices = pages[page]
        cell = render_glyph_indices(char, font, palette, supersample=4)
        for dy in range(CELL_HEIGHT):
            start = (y + dy) * h.width + x
            indices[start : start + CELL_WIDTH] = cell[
                dy * CELL_WIDTH : (dy + 1) * CELL_WIDTH
            ]
        changed_pages.add(page)

    font_bytes = font_path.read_bytes()
    manifest = {
        "font": str(font_path),
        "font_sha256": hashlib.sha256(font_bytes).hexdigest(),
        "font_size": font_size,
        "files": [],
    }
    for page, (source, data, h, _, indices) in enumerate(pages):
        rebuilt = bytearray(data)
        expected = h.width * h.height // 2
        rebuilt[h.image_offset : h.image_offset + expected] = tool.encode_c4_indices(
            indices, h.width, h.height
        )
        output = output_dir / source.name
        output.write_bytes(rebuilt)
        manifest["files"].append(
            {
                "page": page,
                "source": str(source),
                "output": str(output),
                "source_sha256": tool.sha256(data),
                "output_sha256": tool.sha256(bytes(rebuilt)),
                "changed": page in changed_pages,
                "size_preserved": len(rebuilt) == len(data),
                "header_palette_preserved": rebuilt[: h.image_offset]
                == data[: h.image_offset],
            }
        )
        # Decode the newly encoded file again: this catches tiling/packing bugs.
        h2, _, idx2 = tool.decode_wtmd(bytes(rebuilt), str(output))
        manifest["files"][-1]["redecode_indices_exact"] = idx2 == indices
    return manifest


def cmd_map(args) -> None:
    payload = {
        "format": "arc-rise-fantasia-euc28-slot-map-v1",
        "rules": {
            "A1_A8": "1 + (lead-A1)*96 + (trail-A1)",
            "B0_F4": "721 + (lead-B0)*96 + (trail-A1)",
            "page": "global_slot // 828",
            "local_slot": "global_slot % 828",
            "x": "(local_slot % 23) * 22",
            "y": "(local_slot // 23) * 28",
        },
        "entries": list(iter_mapping_entries()),
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def cmd_codebook(args) -> None:
    text = load_text_inputs(args.inputs)
    required = extract_custom_glyphs(text)
    existing = None
    if args.existing and args.existing.exists():
        existing = json.loads(args.existing.read_text(encoding="utf-8"))
    reserved: set[str] = set()
    if args.reserve_text:
        reserved |= reserve_pairs_from_text(load_text_inputs(args.reserve_text))
    if args.reserve_hex:
        reserved |= load_reserved_hex(args.reserve_hex)
    result = create_or_extend_codebook(required, existing, reserved)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def cmd_inject(args) -> None:
    codebook = json.loads(args.codebook.read_text(encoding="utf-8"))
    manifest = inject_fonts(
        args.source_dir,
        args.output_dir,
        codebook,
        args.font,
        args.font_size,
        args.wtmd_tool,
    )
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    m = sub.add_parser("map")
    m.add_argument("output", type=Path)
    m.set_defaults(func=cmd_map)

    c = sub.add_parser("codebook")
    c.add_argument("inputs", type=Path, nargs="+")
    c.add_argument("-o", "--output", type=Path, required=True)
    c.add_argument("--existing", type=Path)
    c.add_argument(
        "--reserve-text",
        type=Path,
        nargs="*",
        help="UTF-8 source text whose original Japanese glyphs must remain intact",
    )
    c.add_argument(
        "--reserve-hex",
        type=Path,
        nargs="*",
        help="files containing raw B0A1..F4FE pairs to keep intact",
    )
    c.set_defaults(func=cmd_codebook)

    i = sub.add_parser("inject")
    i.add_argument("--source-dir", type=Path, required=True)
    i.add_argument("--output-dir", type=Path, required=True)
    i.add_argument("--codebook", type=Path, required=True)
    i.add_argument("--font", type=Path, required=True)
    i.add_argument("--font-size", type=int, default=22)
    i.add_argument("--wtmd-tool", type=Path, required=True)
    i.add_argument("--manifest", type=Path, required=True)
    i.set_defaults(func=cmd_inject)
    return p


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
