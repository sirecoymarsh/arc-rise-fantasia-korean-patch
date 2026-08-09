#!/usr/bin/env python3
"""Build and validate the Korean Arc Rise Fantasia Wii opening banner.

The immutable extracted ``opening.bnr`` is never edited.  Only the Japanese
subtitle baked into the large banner logo is replaced; the extremely small
icon subtitle is removed.  All archive/container checks are performed on the
new payload before it is written.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "work" / "runtime_fix" / "opening_bnr_ko"
SOURCE = ROOT / "work" / "disc_extracted" / "DATA" / "files" / "opening.bnr"
PAYLOAD = BASE / "payloads" / "opening.bnr"
AUDIT = BASE / "audit"
FONT = Path(r"C:\Windows\Fonts\malgunbd.ttf")
SOURCE_SHA256 = "24EFADD02D6E3C489189F6F1DD6DFDB29D8C961E60A0B12ED03FF16CD101CD64"
U8_MAGIC = 0x55AA382D
TPL_MAGIC = 0x0020AF30


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def md5_bytes(data: bytes) -> bytes:
    return hashlib.md5(data).digest()


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def hx(value: int) -> str:
    return f"0x{value:X}"


@dataclass(frozen=True)
class U8Node:
    index: int
    kind: int
    name: str
    word1: int
    word2: int
    path: str


@dataclass(frozen=True)
class U8Archive:
    root_offset: int
    header_size: int
    data_offset: int
    nodes: tuple[U8Node, ...]


def parse_u8(data: bytes) -> U8Archive:
    if len(data) < 32 or struct.unpack_from(">I", data, 0)[0] != U8_MAGIC:
        raise ValueError("not a Nintendo U8 archive")
    root, header_size, data_offset = struct.unpack_from(">III", data, 4)
    if root + 12 > len(data):
        raise ValueError("invalid U8 root offset")
    count = struct.unpack_from(">I", data, root + 8)[0]
    strings = root + count * 12
    if count < 1 or strings > len(data):
        raise ValueError("invalid U8 node table")
    raw_nodes: list[tuple[int, str, int, int]] = []
    for i in range(count):
        p = root + i * 12
        type_name, word1, word2 = struct.unpack_from(">III", data, p)
        kind, name_offset = type_name >> 24, type_name & 0xFFFFFF
        end = data.find(b"\0", strings + name_offset)
        if end < 0:
            raise ValueError(f"unterminated U8 name at node {i}")
        name = data[strings + name_offset:end].decode("ascii")
        raw_nodes.append((kind, name, word1, word2))
    if raw_nodes[0][0] != 1 or raw_nodes[0][3] != count:
        raise ValueError("invalid U8 root node")
    nodes: list[U8Node] = []
    stack: list[tuple[int, str]] = [(count, "")]
    for i, (kind, name, word1, word2) in enumerate(raw_nodes):
        if i == 0:
            path = ""
        else:
            while stack and i >= stack[-1][0]:
                stack.pop()
            parent = stack[-1][1] if stack else ""
            path = f"{parent}/{name}" if parent else name
            if kind == 1:
                stack.append((word2, path))
        if kind not in (0, 1):
            raise ValueError(f"unknown U8 node type {kind}")
        if kind == 0 and word1 + word2 > len(data):
            raise ValueError(f"U8 member outside archive: {path}")
        nodes.append(U8Node(i, kind, name, word1, word2, path))
    return U8Archive(root, header_size, data_offset, tuple(nodes))


def u8_members(data: bytes, archive: U8Archive | None = None) -> dict[str, bytes]:
    a = archive or parse_u8(data)
    return {n.path: data[n.word1:n.word1 + n.word2] for n in a.nodes if n.kind == 0}


def u8_structure(a: U8Archive) -> list[dict]:
    return [
        {
            "index": n.index,
            "kind": "directory" if n.kind else "file",
            "path": n.path,
            "word1": n.word1,
            "word2": n.word2,
        }
        for n in a.nodes
    ]


def replace_same_size_member(data: bytes, member_path: str, replacement: bytes) -> bytes:
    archive = parse_u8(data)
    matches = [n for n in archive.nodes if n.kind == 0 and n.path == member_path]
    if len(matches) != 1:
        raise ValueError((member_path, len(matches)))
    node = matches[0]
    if len(replacement) != node.word2:
        raise ValueError(f"size change for inner U8 member {member_path}")
    out = bytearray(data)
    out[node.word1:node.word1 + node.word2] = replacement
    return bytes(out)


def repack_outer_u8(original: bytes, replacements: dict[str, bytes]) -> bytes:
    """Repack the tiny outer U8 while preserving its exact node/string table."""
    archive = parse_u8(original)
    original_members = u8_members(original, archive)
    unknown = set(replacements) - set(original_members)
    if unknown:
        raise ValueError(f"unknown outer U8 members: {sorted(unknown)}")
    out = bytearray(original[:archive.data_offset])
    cursor = archive.data_offset
    for node in archive.nodes:
        if node.kind != 0:
            continue
        cursor = align(cursor, 32)
        if len(out) < cursor:
            out.extend(b"\0" * (cursor - len(out)))
        member = replacements.get(node.path, original_members[node.path])
        p = archive.root_offset + node.index * 12
        struct.pack_into(">II", out, p + 4, cursor, len(member))
        out.extend(member)
        cursor += len(member)
    return bytes(out)


def lz77_decompress(data: bytes) -> bytes:
    if data[:4] == b"LZ77":
        data = data[4:]
    if len(data) < 4 or data[0] != 0x10:
        raise ValueError("not Nintendo LZ77 type 0x10")
    expected = int.from_bytes(data[1:4], "little")
    src = 4
    out = bytearray()
    while len(out) < expected:
        if src >= len(data):
            raise ValueError("truncated LZ77 flags")
        flags = data[src]
        src += 1
        for bit in range(7, -1, -1):
            if len(out) >= expected:
                break
            if flags & (1 << bit):
                if src + 2 > len(data):
                    raise ValueError("truncated LZ77 reference")
                b1, b2 = data[src], data[src + 1]
                src += 2
                length = (b1 >> 4) + 3
                displacement = ((b1 & 15) << 8) | b2
                back = len(out) - displacement - 1
                if back < 0:
                    raise ValueError("invalid LZ77 reference")
                for _ in range(length):
                    out.append(out[back])
                    back += 1
                    if len(out) >= expected:
                        break
            else:
                if src >= len(data):
                    raise ValueError("truncated LZ77 literal")
                out.append(data[src])
                src += 1
    return bytes(out)


def lz77_compress(raw: bytes) -> bytes:
    """Deterministic greedy Nintendo type-0x10 compressor."""
    if len(raw) >= 1 << 24:
        raise ValueError("type-0x10 input too large")
    chains: dict[bytes, deque[int]] = defaultdict(deque)
    body = bytearray()
    pos = 0

    def add_position(p: int) -> None:
        if p + 2 >= len(raw):
            return
        key = raw[p:p + 3]
        q = chains[key]
        cutoff = p - 4096
        while q and q[0] < cutoff:
            q.popleft()
        q.append(p)

    while pos < len(raw):
        flag_at = len(body)
        body.append(0)
        flags = 0
        for token in range(8):
            if pos >= len(raw):
                break
            best_length = 0
            best_displacement = 0
            if pos + 2 < len(raw):
                key = raw[pos:pos + 3]
                q = chains.get(key)
                if q:
                    cutoff = pos - 4096
                    while q and q[0] < cutoff:
                        q.popleft()
                    checked = 0
                    for candidate in reversed(q):
                        checked += 1
                        length = 3
                        maximum = min(18, len(raw) - pos)
                        while length < maximum and raw[candidate + length] == raw[pos + length]:
                            length += 1
                        if length > best_length:
                            best_length = length
                            best_displacement = pos - candidate - 1
                            if length == 18:
                                break
                        if checked >= 192:
                            break
            if best_length >= 3:
                flags |= 1 << (7 - token)
                body.extend((((best_length - 3) << 4) | (best_displacement >> 8),
                             best_displacement & 0xFF))
                consumed = best_length
            else:
                body.append(raw[pos])
                consumed = 1
            for p in range(pos, pos + consumed):
                add_position(p)
            pos += consumed
        body[flag_at] = flags
    return b"LZ77" + bytes((0x10,)) + len(raw).to_bytes(3, "little") + bytes(body)


def unwrap_imd5(data: bytes) -> tuple[bytes, dict]:
    if len(data) < 32 or data[:4] != b"IMD5":
        raise ValueError("missing IMD5")
    declared = struct.unpack_from(">I", data, 4)[0]
    payload = data[32:32 + declared]
    digest = data[16:32]
    return payload, {
        "declared_payload_size": declared,
        "actual_payload_size": len(payload),
        "stored_md5": digest.hex().upper(),
        "computed_md5": md5_bytes(payload).hex().upper(),
        "valid": len(payload) == declared and md5_bytes(payload) == digest,
    }


def wrap_imd5(payload: bytes) -> bytes:
    return b"IMD5" + struct.pack(">I", len(payload)) + b"\0" * 8 + md5_bytes(payload) + payload


def validate_imet(header: bytes) -> dict:
    if len(header) != 0x600 or header[0x40:0x44] != b"IMET":
        raise ValueError("invalid IMET header")
    stored = header[0x5F0:0x600]
    probe = bytearray(header)
    probe[0x5F0:0x600] = b"\0" * 16
    computed = md5_bytes(bytes(probe))
    names = []
    for i in range(10):
        raw = header[0x5C + i * 84:0x5C + (i + 1) * 84]
        names.append(raw.decode("utf-16-be", "replace").split("\0", 1)[0])
    return {
        "magic_offset": "0x40",
        "stored_md5": stored.hex().upper(),
        "computed_md5": computed.hex().upper(),
        "valid": stored == computed,
        "names": names,
    }


def rgb565(value: int) -> tuple[int, int, int, int]:
    r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4),
            (b << 3) | (b >> 2), 255)


def to_rgb565(color: tuple[int, int, int, int]) -> int:
    r, g, b, _ = color
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)


def rgb5a3(value: int) -> tuple[int, int, int, int]:
    if value & 0x8000:
        r, g, b = (value >> 10) & 31, (value >> 5) & 31, value & 31
        return ((r << 3) | (r >> 2), (g << 3) | (g >> 2),
                (b << 3) | (b >> 2), 255)
    a, r, g, b = (value >> 12) & 7, (value >> 8) & 15, (value >> 4) & 15, value & 15
    return ((r << 4) | r, (g << 4) | g, (b << 4) | b,
            (a << 5) | (a << 2) | (a >> 1))


def to_rgb5a3(color: tuple[int, int, int, int]) -> int:
    r, g, b, a = color
    if a >= 224:
        return 0x8000 | ((r * 31 + 127) // 255) << 10 | ((g * 31 + 127) // 255) << 5 | ((b * 31 + 127) // 255)
    return ((a * 7 + 127) // 255) << 12 | ((r * 15 + 127) // 255) << 8 | ((g * 15 + 127) // 255) << 4 | ((b * 15 + 127) // 255)


def parse_tpl(data: bytes) -> dict:
    if len(data) < 32 or struct.unpack_from(">I", data, 0)[0] != TPL_MAGIC:
        raise ValueError("not a TPL")
    count, table = struct.unpack_from(">II", data, 4)
    if count != 1:
        raise ValueError("only single-image TPL is supported")
    texture_header, palette_header = struct.unpack_from(">II", data, table)
    height, width, fmt, image_offset = struct.unpack_from(">HHII", data, texture_header)
    return {
        "count": count,
        "table_offset": table,
        "texture_header_offset": texture_header,
        "palette_header_offset": palette_header,
        "width": width,
        "height": height,
        "format": fmt,
        "image_offset": image_offset,
    }


def decode_tpl(data: bytes) -> tuple[Image.Image, dict]:
    h = parse_tpl(data)
    width, height, fmt, pos = h["width"], h["height"], h["format"], h["image_offset"]
    image = Image.new("RGBA", (width, height))
    pixels = image.load()
    if fmt == 5:
        for by in range(0, height, 4):
            for bx in range(0, width, 4):
                for yy in range(4):
                    for xx in range(4):
                        color = rgb5a3(struct.unpack_from(">H", data, pos)[0])
                        pos += 2
                        if bx + xx < width and by + yy < height:
                            pixels[bx + xx, by + yy] = color
    elif fmt == 14:
        for by in range(0, height, 8):
            for bx in range(0, width, 8):
                for sy in (0, 4):
                    for sx in (0, 4):
                        c0_value, c1_value, bits = struct.unpack_from(">HHI", data, pos)
                        pos += 8
                        c0, c1 = rgb565(c0_value), rgb565(c1_value)
                        if c0_value > c1_value:
                            c2 = tuple((2 * c0[i] + c1[i]) // 3 for i in range(3)) + (255,)
                            c3 = tuple((c0[i] + 2 * c1[i]) // 3 for i in range(3)) + (255,)
                        else:
                            c2 = tuple((c0[i] + c1[i]) // 2 for i in range(3)) + (255,)
                            c3 = (0, 0, 0, 0)
                        palette = (c0, c1, c2, c3)
                        for i in range(16):
                            x, y = bx + sx + i % 4, by + sy + i // 4
                            if x < width and y < height:
                                pixels[x, y] = palette[(bits >> (30 - i * 2)) & 3]
    else:
        raise ValueError(f"unsupported target TPL format {fmt}")
    return image, h


def rgb5a3_pixel_offset(header: dict, x: int, y: int) -> int:
    blocks_per_row = math.ceil(header["width"] / 4)
    block = (y // 4) * blocks_per_row + x // 4
    within = (y % 4) * 4 + x % 4
    return header["image_offset"] + block * 32 + within * 2


def patch_banner_title(tpl: bytes) -> tuple[bytes, Image.Image, Image.Image, dict]:
    before, header = decode_tpl(tpl)
    if (header["width"], header["height"], header["format"]) != (340, 200, 5):
        raise ValueError(f"unexpected title_base.tpl geometry: {header}")
    desired = before.copy()
    pixels = desired.load()
    # The final kana extend to x=156 even though the high-contrast body of the
    # subtitle visually appears to end earlier.  Keep a small verified margin
    # while stopping well before the unrelated grayscale sparkle at x=175.
    clean_box = (10, 114, 160, 126)
    cleaned = 0
    for y in range(clean_box[1], clean_box[3]):
        for x in range(clean_box[0], clean_box[2]):
            r, g, b, a = pixels[x, y]
            # The source subtitle is strictly grayscale.  Saturated cyan/blue
            # logo pixels underneath it are deliberately retained.
            if a and max(r, g, b) - min(r, g, b) <= 3:
                pixels[x, y] = (0, 0, 0, 0)
                cleaned += 1
    if cleaned < 450:
        raise AssertionError(f"subtitle cleanup mask unexpectedly small: {cleaned}")

    target_text = "아크 라이즈 판타지아"
    font = ImageFont.truetype(str(FONT), 10)
    probe = Image.new("RGBA", (256, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(probe)
    box = draw.textbbox((0, 0), target_text, font=font, stroke_width=1)
    draw.text((-box[0], -box[1]), target_text, font=font,
              fill=(255, 255, 255, 255), stroke_width=1,
              stroke_fill=(20, 20, 20, 255))
    glyphs = probe.crop((0, 0, box[2] - box[0], box[3] - box[1]))
    glyphs = glyphs.resize((120, glyphs.height), Image.Resampling.LANCZOS)
    text_xy = (12, 114)
    desired.alpha_composite(glyphs, text_xy)

    out = bytearray(tpl)
    changed_pixels = []
    for y in range(header["height"]):
        for x in range(header["width"]):
            if before.getpixel((x, y)) != desired.getpixel((x, y)):
                offset = rgb5a3_pixel_offset(header, x, y)
                struct.pack_into(">H", out, offset, to_rgb5a3(desired.getpixel((x, y))))
                changed_pixels.append((x, y))
    result = bytes(out)
    after, after_header = decode_tpl(result)
    if after_header != header:
        raise AssertionError("title_base.tpl header changed")
    # Quantization can change desired RGBA values, so scope is checked on the
    # final decoded texture rather than against the high precision canvas.
    final_diff = [(x, y) for y in range(header["height"]) for x in range(header["width"])
                  if before.getpixel((x, y)) != after.getpixel((x, y))]
    if not final_diff or any(not (clean_box[0] <= x < clean_box[2] and clean_box[1] <= y < clean_box[3]) for x, y in final_diff):
        raise AssertionError("title_base.tpl changed outside subtitle rectangle")
    diff_bbox = (min(x for x, _ in final_diff), min(y for _, y in final_diff),
                 max(x for x, _ in final_diff) + 1, max(y for _, y in final_diff) + 1)
    return result, before, after, {
        "source_text": "アークライズファンタジア",
        "translation_ko": target_text,
        "translation_provenance": "Codex internal model",
        "cleanup_box": list(clean_box),
        "cleaned_source_pixels": cleaned,
        "changed_decoded_pixels": len(final_diff),
        "changed_pixel_bbox": list(diff_bbox),
        "all_changes_within_subtitle_rectangle": True,
        "text_position": list(text_xy),
        "font": FONT.name,
        "font_size": 10,
        "horizontal_render_width": 120,
    }


def cmpr_block_offset(header: dict, block_x: int, block_y: int) -> int:
    macro_per_row = math.ceil(header["width"] / 8)
    macro = (block_y // 8) * macro_per_row + block_x // 8
    sub = (1 if block_y % 8 >= 4 else 0) * 2 + (1 if block_x % 8 >= 4 else 0)
    return header["image_offset"] + macro * 32 + sub * 8


def encode_transparent_dxt1_block(colors: list[tuple[int, int, int, int]]) -> bytes:
    opaque = [c for c in colors if c[3] >= 128]
    if not opaque:
        return struct.pack(">HHI", 0, 0, 0xFFFFFFFF)
    candidates = sorted({to_rgb565(c) for c in opaque})
    best = None
    best_error = None
    for a in candidates:
        for b in candidates:
            c0_value, c1_value = min(a, b), max(a, b)
            c0, c1 = rgb565(c0_value), rgb565(c1_value)
            c2 = tuple((c0[i] + c1[i]) // 2 for i in range(3)) + (255,)
            palette = (c0, c1, c2)
            bits = 0
            error = 0
            for i, color in enumerate(colors):
                if color[3] < 128:
                    index = 3
                else:
                    distances = [sum((color[k] - p[k]) ** 2 for k in range(3)) for p in palette]
                    index = min(range(3), key=lambda j: distances[j])
                    error += distances[index]
                bits |= index << (30 - i * 2)
            key = (error, c0_value, c1_value, bits)
            if best_error is None or key < best_error:
                best_error = key
                best = struct.pack(">HHI", c0_value, c1_value, bits)
    assert best is not None
    return best


def patch_icon_title(tpl: bytes) -> tuple[bytes, Image.Image, Image.Image, dict]:
    before, header = decode_tpl(tpl)
    if (header["width"], header["height"], header["format"]) != (120, 70, 14):
        raise ValueError(f"unexpected icon title.tpl geometry: {header}")
    # At 120x70 the subtitle is only three to four pixels high.  A Korean
    # rendering would be illegible, so the source line is cleanly removed.
    remove: set[tuple[int, int]] = set()
    for y in range(42, 46):
        for x in range(1, 57):
            r, g, b, a = before.getpixel((x, y))
            saturation = max(r, g, b) - min(r, g, b)
            if a and (x < 32 or saturation <= 105):
                remove.add((x, y))
    if len(remove) < 120:
        raise AssertionError(f"icon subtitle cleanup mask unexpectedly small: {len(remove)}")

    out = bytearray(tpl)
    blocks = sorted({(x // 4 * 4, y // 4 * 4) for x, y in remove}, key=lambda p: (p[1], p[0]))
    direct_index_blocks = 0
    reencoded_blocks = 0
    for bx, by in blocks:
        offset = cmpr_block_offset(header, bx, by)
        c0, c1, bits = struct.unpack_from(">HHI", out, offset)
        local_targets = {(x, y) for x, y in remove if bx <= x < bx + 4 and by <= y < by + 4}
        if c0 <= c1:
            for x, y in local_targets:
                i = (y - by) * 4 + (x - bx)
                bits &= ~(3 << (30 - i * 2))
                bits |= 3 << (30 - i * 2)
            struct.pack_into(">I", out, offset + 4, bits)
            direct_index_blocks += 1
        else:
            colors = []
            for yy in range(4):
                for xx in range(4):
                    x, y = bx + xx, by + yy
                    color = before.getpixel((x, y)) if x < header["width"] and y < header["height"] else (0, 0, 0, 0)
                    colors.append((0, 0, 0, 0) if (x, y) in local_targets else color)
            out[offset:offset + 8] = encode_transparent_dxt1_block(colors)
            reencoded_blocks += 1

    result = bytes(out)
    after, after_header = decode_tpl(result)
    if after_header != header:
        raise AssertionError("icon title.tpl header changed")
    not_removed = [(x, y) for x, y in remove if after.getpixel((x, y))[3] != 0]
    if not_removed:
        raise AssertionError(f"icon subtitle pixels survived: {not_removed[:10]}")
    final_diff = [(x, y) for y in range(header["height"]) for x in range(header["width"])
                  if before.getpixel((x, y)) != after.getpixel((x, y))]
    expanded = (min(x for x, _ in blocks), min(y for _, y in blocks),
                max(x for x, _ in blocks) + 4, max(y for _, y in blocks) + 4)
    outside = [(x, y) for x, y in final_diff if not (expanded[0] <= x < expanded[2] and expanded[1] <= y < expanded[3])]
    if outside:
        raise AssertionError("icon title changed outside touched CMPR blocks")
    diff_bbox = (min(x for x, _ in final_diff), min(y for _, y in final_diff),
                 max(x for x, _ in final_diff) + 1, max(y for _, y in final_diff) + 1)
    return result, before, after, {
        "source_text": "アークライズファンタジア",
        "translation_ko": None,
        "treatment": "removed because the 120x70 icon subtitle is too small for legible Hangul",
        "translation_provenance": "Codex internal model",
        "source_subtitle_box": [1, 42, 57, 46],
        "removed_source_pixels": len(remove),
        "touched_cmpr_blocks": len(blocks),
        "direct_index_only_blocks": direct_index_blocks,
        "reencoded_opaque_blocks": reencoded_blocks,
        "changed_decoded_pixels": len(final_diff),
        "changed_pixel_bbox": list(diff_bbox),
        "expanded_changed_block_bbox": list(expanded),
        "all_changes_within_expected_cmpr_blocks": True,
        "remaining_target_pixels": len(not_removed),
    }


def checker_composite(image: Image.Image, scale: int) -> Image.Image:
    image = image.convert("RGBA")
    checker = Image.new("RGBA", image.size, (230, 230, 230, 255))
    draw = ImageDraw.Draw(checker)
    for y in range(0, image.height, 8):
        for x in range(0, image.width, 8):
            if (x // 8 + y // 8) & 1:
                draw.rectangle((x, y, x + 7, y + 7), fill=(185, 185, 185, 255))
    checker.alpha_composite(image)
    return checker.convert("RGB").resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)


def make_contact_sheet(images: dict[str, Image.Image], path: Path) -> None:
    label_font = ImageFont.truetype(str(FONT), 22)
    # Full logo at 2x and icon at 5x, followed by a 5x subtitle close-up.
    title_before = checker_composite(images["banner_before"], 2)
    title_after = checker_composite(images["banner_after"], 2)
    icon_before = checker_composite(images["icon_before"], 5)
    icon_after = checker_composite(images["icon_after"], 5)
    crop_before = checker_composite(images["banner_before"].crop((8, 108, 150, 132)), 5)
    crop_after = checker_composite(images["banner_after"].crop((8, 108, 150, 132)), 5)
    margin, gap, label_h = 24, 26, 38
    width = margin * 2 + max(title_before.width * 2 + gap, crop_before.width * 2 + gap)
    height = margin + label_h + title_before.height + gap + label_h + icon_before.height + gap + label_h + crop_before.height + margin
    sheet = Image.new("RGB", (width, height), (28, 30, 35))
    draw = ImageDraw.Draw(sheet)
    y = margin
    for label, left, right in [
        ("배너 로고 — 원본 / 한국어", title_before, title_after),
        ("Wii 메뉴 아이콘 — 원본 / 일본어 부제 제거", icon_before, icon_after),
        ("부제 5배 확대 — 원본 / 한국어", crop_before, crop_after),
    ]:
        draw.text((margin, y), label, font=label_font, fill=(235, 240, 248))
        y += label_h
        sheet.paste(left, (margin, y))
        sheet.paste(right, (margin + left.width + gap, y))
        y += max(left.height, right.height) + gap
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, optimize=True)


def compare_u8(source: bytes, output: bytes, expected_changed: set[str]) -> dict:
    src_archive, out_archive = parse_u8(source), parse_u8(output)
    src_members, out_members = u8_members(source, src_archive), u8_members(output, out_archive)
    same_paths = list(src_members) == list(out_members)
    structural_fields = lambda a: [(n.index, n.kind, n.name, n.path) for n in a.nodes]
    same_structure = structural_fields(src_archive) == structural_fields(out_archive)
    same_offsets_sizes = all(
        s.index == o.index and s.kind == o.kind and s.word1 == o.word1 and s.word2 == o.word2
        for s, o in zip(src_archive.nodes, out_archive.nodes)
    )
    rows = []
    for path in src_members:
        changed = src_members[path] != out_members[path]
        rows.append({
            "path": path,
            "expected_changed": path in expected_changed,
            "changed": changed,
            "source_size": len(src_members[path]),
            "output_size": len(out_members[path]),
            "source_sha256": sha256_bytes(src_members[path]),
            "output_sha256": sha256_bytes(out_members[path]),
        })
    unexpected = [r["path"] for r in rows if r["changed"] != r["expected_changed"]]
    return {
        "source_size": len(source),
        "output_size": len(output),
        "root_offset_preserved": src_archive.root_offset == out_archive.root_offset,
        "header_size_preserved": src_archive.header_size == out_archive.header_size,
        "data_offset_preserved": src_archive.data_offset == out_archive.data_offset,
        "node_count": len(src_archive.nodes),
        "node_and_path_structure_preserved": same_structure,
        "node_offsets_and_sizes_preserved": same_offsets_sizes,
        "file_set_and_order_preserved": same_paths,
        "expected_changed_members": sorted(expected_changed),
        "unexpected_member_deltas": unexpected,
        "all_and_only_expected_members_changed": not unexpected,
        "members": rows,
    }


def build_once(source_bnr: bytes) -> tuple[bytes, dict, dict[str, Image.Image]]:
    imet = source_bnr[:0x600]
    outer = source_bnr[0x600:]
    outer_archive = parse_u8(outer)
    outer_members = u8_members(outer, outer_archive)
    if list(outer_members) != ["meta/banner.bin", "meta/icon.bin", "meta/sound.bin"]:
        raise ValueError(f"unexpected outer file set: {list(outer_members)}")

    nested = {}
    images: dict[str, Image.Image] = {}
    new_wrapped = {}
    for outer_path, inner_target, patcher, image_key in [
        ("meta/banner.bin", "arc/timg/title_base.tpl", patch_banner_title, "banner"),
        ("meta/icon.bin", "arc/timg/title.tpl", patch_icon_title, "icon"),
    ]:
        wrapped = outer_members[outer_path]
        compressed, source_imd5 = unwrap_imd5(wrapped)
        if not source_imd5["valid"]:
            raise AssertionError(f"source IMD5 invalid: {outer_path}")
        decompressed = lz77_decompress(compressed)
        members = u8_members(decompressed)
        replacement, before, after, treatment = patcher(members[inner_target])
        patched_inner = replace_same_size_member(decompressed, inner_target, replacement)
        compressed_new = lz77_compress(patched_inner)
        if lz77_decompress(compressed_new) != patched_inner:
            raise AssertionError(f"LZ77 round-trip failed: {outer_path}")
        wrapped_new = wrap_imd5(compressed_new)
        _, output_imd5 = unwrap_imd5(wrapped_new)
        if not output_imd5["valid"]:
            raise AssertionError(f"output IMD5 invalid: {outer_path}")
        new_wrapped[outer_path] = wrapped_new
        images[f"{image_key}_before"] = before
        images[f"{image_key}_after"] = after
        nested[outer_path] = {
            "target_member": inner_target,
            "source_imd5": source_imd5,
            "output_imd5": output_imd5,
            "source_wrapped_size": len(wrapped),
            "output_wrapped_size": len(wrapped_new),
            "source_wrapped_sha256": sha256_bytes(wrapped),
            "output_wrapped_sha256": sha256_bytes(wrapped_new),
            "source_compressed_size": len(compressed),
            "output_compressed_size": len(compressed_new),
            "source_decompressed_size": len(decompressed),
            "output_decompressed_size": len(patched_inner),
            "source_decompressed_sha256": sha256_bytes(decompressed),
            "output_decompressed_sha256": sha256_bytes(patched_inner),
            "lz77_roundtrip_valid": True,
            "inner_u8_validation": compare_u8(decompressed, patched_inner, {inner_target}),
            "texture_treatment": treatment,
            "target_tpl": {
                "source_size": len(members[inner_target]),
                "output_size": len(replacement),
                "source_sha256": sha256_bytes(members[inner_target]),
                "output_sha256": sha256_bytes(replacement),
                "source_header": parse_tpl(members[inner_target]),
                "output_header": parse_tpl(replacement),
                "same_size": len(members[inner_target]) == len(replacement),
                "same_gx_format_and_geometry": parse_tpl(members[inner_target]) == parse_tpl(replacement),
            },
        }

    new_outer = repack_outer_u8(outer, new_wrapped)
    output_bnr = imet + new_outer
    outer_validation = compare_u8(outer, new_outer, {"meta/banner.bin", "meta/icon.bin"})
    sound_preserved = outer_members["meta/sound.bin"] == u8_members(new_outer)["meta/sound.bin"]
    _, sound_imd5 = unwrap_imd5(outer_members["meta/sound.bin"])
    report = {
        "imet": validate_imet(imet),
        "nested": nested,
        "outer_u8_validation": outer_validation,
        "sound": {
            "source_sha256": sha256_bytes(outer_members["meta/sound.bin"]),
            "output_sha256": sha256_bytes(u8_members(new_outer)["meta/sound.bin"]),
            "size": len(outer_members["meta/sound.bin"]),
            "byte_identical": sound_preserved,
            "imd5": sound_imd5,
        },
    }
    return output_bnr, report, images


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> int:
    BASE.mkdir(parents=True, exist_ok=True)
    PAYLOAD.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    if not FONT.is_file():
        raise SystemExit(f"font missing: {FONT}")
    source = SOURCE.read_bytes()
    if sha256_bytes(source) != SOURCE_SHA256:
        raise SystemExit(f"source SHA-256 mismatch: {sha256_bytes(source)}")

    output1, detail1, images1 = build_once(source)
    output2, detail2, _ = build_once(source)
    if output1 != output2 or detail1 != detail2:
        raise AssertionError("opening.bnr build is not deterministic")
    if SOURCE.read_bytes() != source:
        raise AssertionError("immutable source opening.bnr was modified")

    PAYLOAD.write_bytes(output1)
    image_paths = {}
    for name, image in images1.items():
        path = AUDIT / f"{name}.png"
        image.save(path, optimize=True)
        image_paths[name] = {"path": relative(path), "sha256": sha256_file(path)}
    contact = AUDIT / "opening_bnr_original_vs_korean.png"
    make_contact_sheet(images1, contact)

    static_checks = {
        "source_sha256_anchor_valid": sha256_bytes(source) == SOURCE_SHA256,
        "source_baseline_unmodified": SOURCE.read_bytes() == source,
        "deterministic_rebuild_byte_identical": output1 == output2,
        "imet_header_byte_identical": output1[:0x600] == source[:0x600],
        "imet_md5_valid": detail1["imet"]["valid"],
        "outer_u8_file_set_order_and_structure_preserved": (
            detail1["outer_u8_validation"]["file_set_and_order_preserved"]
            and detail1["outer_u8_validation"]["node_and_path_structure_preserved"]
        ),
        "outer_u8_only_banner_and_icon_changed": detail1["outer_u8_validation"]["all_and_only_expected_members_changed"],
        "banner_inner_u8_only_title_base_changed": detail1["nested"]["meta/banner.bin"]["inner_u8_validation"]["all_and_only_expected_members_changed"],
        "icon_inner_u8_only_title_changed": detail1["nested"]["meta/icon.bin"]["inner_u8_validation"]["all_and_only_expected_members_changed"],
        "banner_inner_u8_offsets_and_sizes_preserved": detail1["nested"]["meta/banner.bin"]["inner_u8_validation"]["node_offsets_and_sizes_preserved"],
        "icon_inner_u8_offsets_and_sizes_preserved": detail1["nested"]["meta/icon.bin"]["inner_u8_validation"]["node_offsets_and_sizes_preserved"],
        "same_target_tpl_sizes_formats_and_geometry": all(v["target_tpl"]["same_size"] and v["target_tpl"]["same_gx_format_and_geometry"] for v in detail1["nested"].values()),
        "all_imd5_hashes_valid": all(v["output_imd5"]["valid"] for v in detail1["nested"].values()),
        "all_lz77_roundtrips_valid": all(v["lz77_roundtrip_valid"] for v in detail1["nested"].values()),
        "animation_layout_and_unrelated_textures_preserved": all(v["inner_u8_validation"]["all_and_only_expected_members_changed"] for v in detail1["nested"].values()),
        "sound_byte_identical": detail1["sound"]["byte_identical"],
        "sound_imd5_valid": detail1["sound"]["imd5"]["valid"],
        "banner_pixel_diff_scoped_to_subtitle": detail1["nested"]["meta/banner.bin"]["texture_treatment"]["all_changes_within_subtitle_rectangle"],
        "icon_pixel_diff_scoped_to_expected_blocks": detail1["nested"]["meta/icon.bin"]["texture_treatment"]["all_changes_within_expected_cmpr_blocks"],
    }
    valid = all(static_checks.values())
    if not valid:
        raise AssertionError({k: v for k, v in static_checks.items() if not v})

    manifest = {
        "schema": "arf-ko-opening-bnr-payload-v1",
        "valid": valid,
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_services_used": [],
        "source_baseline_modified": False,
        "physical_path": "opening.bnr",
        "source_path": relative(SOURCE),
        "output_path": relative(PAYLOAD),
        "source_size": len(source),
        "output_size": len(output1),
        "source_sha256": sha256_bytes(source),
        "output_sha256": sha256_bytes(output1),
        "riivolution_resize_required": len(source) != len(output1),
        "format_stack": ["IMET", "Nintendo U8", "IMD5", "LZ77 type 0x10", "Nintendo U8", "TPL"],
        "translations": [
            {
                "container": "meta/banner.bin",
                "member": "arc/timg/title_base.tpl",
                **detail1["nested"]["meta/banner.bin"]["texture_treatment"],
            },
            {
                "container": "meta/icon.bin",
                "member": "arc/timg/title.tpl",
                **detail1["nested"]["meta/icon.bin"]["texture_treatment"],
            },
        ],
        "container_validation": detail1,
        "visual_evidence": {
            "contact_sheet": {"path": relative(contact), "sha256": sha256_file(contact)},
            "individual_renders": image_paths,
        },
        "static_validation": {"valid": valid, "checks": static_checks},
        "integration": {
            "riivolution_rule": f'<file disc="/opening.bnr" external="opening.bnr" resize="{str(len(source) != len(output1)).lower()}" />',
        },
        "runtime_validation_required": [
            "Open the Disc Channel banner and verify the Korean subtitle is legible without clipping.",
            "Inspect the animated channel banner and confirm logo, clouds and Marvelous mark animate normally.",
            "Inspect the channel icon and confirm the tiny Japanese subtitle is absent.",
            "Confirm the original banner sound plays unchanged.",
        ],
    }
    manifest_path = BASE / "opening_bnr_korean_payload_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fragment = BASE / "riivolution_opening_bnr_rule.xml.fragment"
    fragment.write_text(manifest["integration"]["riivolution_rule"] + "\n", encoding="utf-8")

    report_lines = [
        "# opening.bnr 한국어 현지화 보고서",
        "",
        "- 대상: Arc Rise Fantasia (RPJJ99)",
        "- 번역: Codex 내부 모델 판단만 사용",
        "- 원본 추출물: 변경하지 않음",
        "- 정적 검증: **PASS**",
        "",
        "## 처리 내용",
        "",
        "- 배너 `title_base.tpl`: `アークライズファンタジア`를 `아크 라이즈 판타지아`로 교체했다.",
        "- 아이콘 `title.tpl`: 높이가 3~4픽셀뿐이라 한글을 넣지 않고 일본어 작은 부제만 제거했다.",
        "- 영문 메인 로고, 애니메이션 BRLAN/BRLYT, 나머지 텍스처와 `sound.bin`은 그대로 보존했다.",
        "",
        "## 산출물",
        "",
        f"- payload: `{relative(PAYLOAD)}`",
        f"- SHA-256: `{sha256_bytes(output1)}`",
        f"- 크기: {len(output1):,} bytes (원본 {len(source):,} bytes)",
        f"- 전후 비교: `{relative(contact)}`",
        f"- manifest: `{relative(manifest_path)}`",
        "",
        "## 검증",
        "",
    ]
    for key, value in static_checks.items():
        report_lines.append(f"- {'PASS' if value else 'FAIL'} — `{key}`")
    report_lines += [
        "",
        "IMET 헤더/MD5, 양쪽 IMD5, LZ77 왕복, outer/inner U8 파일 집합과 노드 구조, TPL 크기·GX 포맷·캔버스를 모두 검증했다. 동일 입력을 두 번 빌드한 결과도 바이트 단위로 일치했다.",
        "",
    ]
    report_path = BASE / "opening_bnr_korean_payload_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(json.dumps({
        "valid": valid,
        "payload": str(PAYLOAD),
        "payload_size": len(output1),
        "payload_sha256": sha256_bytes(output1),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "contact_sheet": str(contact),
        "contact_sheet_sha256": sha256_file(contact),
        "source_unchanged": sha256_file(SOURCE) == SOURCE_SHA256,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
