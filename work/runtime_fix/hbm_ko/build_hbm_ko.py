#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageChops


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "work" / "runtime_fix" / "hbm_ko"
SRC = ROOT / "work" / "disc_extracted" / "DATA" / "files" / "Hbm"
PAYLOAD = BASE / "payloads" / "Hbm"
AUDIT = BASE / "audit"
FONT_PATH = Path(r"C:\Windows\Fonts\malgun.ttf")
FONT_BOLD_PATH = Path(r"C:\Windows\Fonts\malgunbd.ttf")


CSV_TRANSLATIONS = {
    "home.csv": [
        (
            "接続する順番に\r\n①ボタンと②ボタンを\r\n同時に押してください。",
            "연결할 순서대로\r\n① 버튼과 ② 버튼을\r\n동시에 눌러 주세요.",
        ),
        ("切断中・・・", "연결을 끊는 중..."),
        (
            "Wiiメニューにもどりますか？\r\n（保存していない内容は失われます）",
            "Wii 메뉴로 돌아가시겠습니까?\r\n(저장하지 않은 내용은 사라집니다.)",
        ),
        (
            "リセットしますか？\r\n（保存していない内容は失われます）",
            "리셋하시겠습니까?\r\n(저장하지 않은 내용은 사라집니다.)",
        ),
    ],
    "home_nosave.csv": [
        (
            "接続する順番に\r\n①ボタンと②ボタンを\r\n同時に押してください。",
            "연결할 순서대로\r\n① 버튼과 ② 버튼을\r\n동시에 눌러 주세요.",
        ),
        ("切断中・・・", "연결을 끊는 중..."),
        ("Wiiメニューにもどりますか？", "Wii 메뉴로 돌아가시겠습니까?"),
        ("リセットしますか？", "리셋하시겠습니까?"),
    ],
}


TPL_TRANSLATIONS = {
    "tx_btn_00.tpl": ("とじる", "닫기"),
    "tx_btn_L_00.tpl": ("Wiiメニューへ", "Wii 메뉴로"),
    "tx_btn_L_11.tpl": ("リセット", "리셋"),
    "tx_cntrl_00.tpl": ("Wiiリモコンの設定", "Wii 리모컨 설정"),
    "tx_cntrl_01.tpl": ("Wiiリモコンの設定をとじる", "Wii 리모컨 설정 닫기"),
    "tx_msgBtn_00.tpl": ("はい", "예"),
    "tx_msgBtn_01.tpl": ("いいえ", "아니요"),
    "tx_optnBtn_20.tpl": ("つなぎなおす", "다시 연결"),
    "tx_optn_00.tpl": ("音量", "음량"),
    "tx_optn_10.tpl": ("振動", "진동"),
    "tx_optn_20.tpl": ("接続", "연결"),
    "tx_ttl_wrd_a.tpl": ("HOMEボタンメニュー", "HOME 버튼 메뉴"),
}


NEUTRAL_LANGUAGE_TEXTURES = {
    "tx_optnBtn_10.tpl": "ON",
    "tx_optnBtn_11.tpl": "OFF",
    "tx_plyr_00.tpl": "1P",
    "tx_plyr_01.tpl": "2P",
    "tx_plyr_02.tpl": "3P",
    "tx_plyr_03.tpl": "4P",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def hx(n: int) -> str:
    return f"0x{n:X}"


@dataclass
class U8Node:
    index: int
    kind: int
    name: str
    offset: int
    size: int
    path: str = ""


def parse_u8(data: bytes) -> tuple[int, list[U8Node]]:
    if data[:4] != b"\x55\xAA\x38\x2D":
        raise ValueError("not a Nintendo U8 archive")
    root = struct.unpack_from(">I", data, 4)[0]
    count = struct.unpack_from(">I", data, root + 8)[0]
    strings = root + count * 12
    nodes: list[U8Node] = []
    for i in range(count):
        p = root + i * 12
        type_name, off, size = struct.unpack_from(">III", data, p)
        kind = type_name >> 24
        no = type_name & 0xFFFFFF
        end = data.index(0, strings + no)
        name = data[strings + no:end].decode("utf-8")
        nodes.append(U8Node(i, kind, name, off, size))
    stack: list[tuple[int, str]] = [(nodes[0].size, "")]
    for i in range(1, len(nodes)):
        while stack and i >= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else ""
        nodes[i].path = f"{parent + '/' if parent else ''}{nodes[i].name}"
        if nodes[i].kind == 1:
            stack.append((nodes[i].size, nodes[i].path))
    return root, nodes


def decode_i4(raw: bytes, width: int, height: int) -> Image.Image:
    expected = math.ceil(width / 8) * math.ceil(height / 8) * 32
    if len(raw) != expected:
        raise ValueError(("I4 size", len(raw), expected, width, height))
    pixels = [0] * (width * height)
    p = 0
    for by in range(0, height, 8):
        for bx in range(0, width, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    value = raw[p]
                    p += 1
                    for dx, nibble in ((0, value >> 4), (1, value & 0xF)):
                        xx, yy = bx + x + dx, by + y
                        if xx < width and yy < height:
                            pixels[yy * width + xx] = nibble * 17
    image = Image.new("L", (width, height))
    image.putdata(pixels)
    return image


def encode_i4(image: Image.Image) -> bytes:
    image = image.convert("L")
    width, height = image.size
    pix = image.load()
    out = bytearray()
    for by in range(0, height, 8):
        for bx in range(0, width, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    vals = []
                    for dx in (0, 1):
                        xx, yy = bx + x + dx, by + y
                        v = pix[xx, yy] if xx < width and yy < height else 0
                        vals.append(max(0, min(15, int(round(v / 17)))))
                    out.append((vals[0] << 4) | vals[1])
    return bytes(out)


def parse_tpl(data: bytes) -> dict:
    if data[:4] != b"\x00\x20\xAF\x30":
        raise ValueError("not TPL")
    if struct.unpack_from(">I", data, 4)[0] != 1:
        raise ValueError("only single-image TPL supported")
    image_header = struct.unpack_from(">I", data, 12)[0]
    height, width, fmt, image_offset = struct.unpack_from(">HHII", data, image_header)
    if fmt != 0:
        raise ValueError(f"expected I4 TPL, got {fmt}")
    data_size = math.ceil(width / 8) * math.ceil(height / 8) * 32
    if image_offset + data_size != len(data):
        raise ValueError((image_offset, data_size, len(data)))
    return {
        "image_header": image_header,
        "width": width,
        "height": height,
        "format": fmt,
        "image_offset": image_offset,
        "image_size": data_size,
    }


def decode_tpl(data: bytes) -> tuple[Image.Image, dict]:
    h = parse_tpl(data)
    return decode_i4(data[h["image_offset"]:], h["width"], h["height"]), h


def render_centered(text: str, size: tuple[int, int]) -> Image.Image:
    width, height = size
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    max_size = max(12, min(42, int(height * 0.90)))
    selected = None
    bbox = None
    for font_size in range(max_size, 11, -1):
        candidate = ImageFont.truetype(str(FONT_PATH), font_size)
        b = probe.textbbox((0, 0), text, font=candidate)
        if b[2] - b[0] <= width - 6 and b[3] - b[1] <= height - 4:
            selected, bbox = candidate, b
            break
    if selected is None or bbox is None:
        raise ValueError(f"cannot fit {text!r} in {size}")
    out = Image.new("L", size, 0)
    draw = ImageDraw.Draw(out)
    x = (width - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (height - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((x, y), text, font=selected, fill=255)
    return out


def encode_tpl_with_image(original: bytes, image: Image.Image) -> bytes:
    h = parse_tpl(original)
    if image.size != (h["width"], h["height"]):
        raise ValueError((image.size, h))
    raw = encode_i4(image)
    if len(raw) != h["image_size"]:
        raise AssertionError((len(raw), h["image_size"]))
    out = bytearray(original)
    out[h["image_offset"]:h["image_offset"] + len(raw)] = raw
    return bytes(out)


def parse_cmaps(font: bytes) -> list[dict]:
    out = []
    pos = 0
    while True:
        pos = font.find(b"CMAP", pos)
        if pos < 0:
            break
        size = struct.unpack_from(">I", font, pos + 4)[0]
        start, end, method = struct.unpack_from(">HHH", font, pos + 8)
        mapping: dict[int, int] = {}
        if method == 0:
            first = struct.unpack_from(">H", font, pos + 20)[0]
            mapping = {cp: first + cp - start for cp in range(start, end + 1)}
        elif method == 1:
            for cp in range(start, end + 1):
                glyph = struct.unpack_from(">H", font, pos + 20 + (cp - start) * 2)[0]
                if glyph != 0xFFFF:
                    mapping[cp] = glyph
        elif method == 2:
            count = struct.unpack_from(">H", font, pos + 20)[0]
            for i in range(count):
                cp, glyph = struct.unpack_from(">HH", font, pos + 22 + i * 4)
                mapping[cp] = glyph
        else:
            raise ValueError(f"unsupported CMAP method {method}")
        out.append({"offset": pos, "size": size, "start": start, "end": end, "method": method, "mapping": mapping})
        pos += size
    return out


def inject_hangul_brfnt(original: bytes, required_hangul: list[str]) -> tuple[bytes, dict]:
    out = bytearray(original)
    tglp = original.find(b"TGLP")
    cwdh = original.find(b"CWDH")
    cmaps = parse_cmaps(original)
    scan = next(c for c in cmaps if c["method"] == 2)
    if min(tglp, cwdh, scan["offset"]) < 0:
        raise ValueError("BRFNT section missing")

    cell_width, cell_height, baseline, max_width = struct.unpack_from(">BBBB", original, tglp + 8)
    sheet_size = struct.unpack_from(">I", original, tglp + 12)[0]
    sheet_count, sheet_format, sheet_rows, sheet_lines, sheet_width, sheet_height = struct.unpack_from(">HHHHHH", original, tglp + 16)
    sheet_image = struct.unpack_from(">I", original, tglp + 28)[0]
    if (sheet_format, cell_width, cell_height, sheet_rows, sheet_lines) != (0, 29, 31, 1, 8):
        raise ValueError("unexpected BRFNT TGLP geometry")
    if sheet_size != math.ceil(sheet_width / 8) * math.ceil(sheet_height / 8) * 32:
        raise ValueError("unexpected BRFNT sheet size")

    sheets = []
    for i in range(sheet_count):
        start = sheet_image + i * sheet_size
        sheets.append(decode_i4(original[start:start + sheet_size], sheet_width, sheet_height))

    original_scan = scan["mapping"]
    preserved_codes = [0x0020, 0x0022, 0x00BF, 0x00E1, 0x00E9, 0x00F3, 0x00FA, 0x00FC, 0x2460, 0x2461]
    preserved = [(cp, original_scan[cp]) for cp in preserved_codes]
    slots = list(range(57, 57 + len(required_hangul)))
    if len(slots) > 51:
        raise ValueError(f"Hangul corpus exceeds 51 reusable glyph slots: {len(slots)}")

    glyph_font = ImageFont.truetype(str(FONT_PATH), 28)
    assignments = []
    for char, glyph in zip(required_hangul, slots):
        sheet_index = glyph // (sheet_rows * sheet_lines)
        within = glyph % (sheet_rows * sheet_lines)
        cell_x = 0
        cell_y = within * (sheet_height // sheet_lines)
        # Clear the complete 32x32 storage cell, including pad pixels.
        sheets[sheet_index].paste(0, (cell_x, cell_y, cell_x + sheet_width, cell_y + sheet_height // sheet_lines))
        box = glyph_font.getbbox(char)
        bw, bh = box[2] - box[0], box[3] - box[1]
        if bw > cell_width or bh > cell_height:
            raise ValueError((char, box, cell_width, cell_height))
        glyph_image = Image.new("L", (cell_width, cell_height), 0)
        d = ImageDraw.Draw(glyph_image)
        x = (cell_width - bw) // 2 - box[0]
        y = (cell_height - bh) // 2 - box[1]
        d.text((x, y), char, font=glyph_font, fill=255)
        sheets[sheet_index].paste(glyph_image, (cell_x, cell_y))

        metric_pos = cwdh + 16 + glyph * 3
        struct.pack_into(">bBB", out, metric_pos, 1, min(28, bw), 30)
        assignments.append({
            "character": char,
            "codepoint": f"U+{ord(char):04X}",
            "glyph_index": glyph,
            "sheet_index": sheet_index,
            "cell_index": within,
            "cwdh": {"left": 1, "glyph_width": min(28, bw), "char_width": 30},
        })

    # Re-encode all sheets. Untouched sheets/cells round-trip byte-identically.
    for i, image in enumerate(sheets):
        raw = encode_i4(image)
        start = sheet_image + i * sheet_size
        out[start:start + sheet_size] = raw

    pairs = preserved + [(ord(char), glyph) for char, glyph in zip(required_hangul, slots)]
    pairs.sort()
    capacity = (scan["size"] - 22) // 4
    if len(pairs) > capacity:
        raise ValueError((len(pairs), capacity))
    start = scan["offset"] + 20
    out[start:scan["offset"] + scan["size"]] = b"\0" * (scan["size"] - 20)
    struct.pack_into(">H", out, start, len(pairs))
    for i, (cp, glyph) in enumerate(pairs):
        struct.pack_into(">HH", out, start + 2 + i * 4, cp, glyph)

    result = bytes(out)
    new_map = {}
    for cmap in parse_cmaps(result):
        new_map.update(cmap["mapping"])
    missing = [char for char in required_hangul if ord(char) not in new_map]
    if missing:
        raise AssertionError(missing)
    report = {
        "source_sha256": sha256(original),
        "output_sha256": sha256(result),
        "size_bytes": len(result),
        "header_unchanged": original[:0x60] == result[:0x60],
        "tglp": {
            "offset_hex": hx(tglp), "cell_width": cell_width, "cell_height": cell_height,
            "baseline": baseline, "max_width": max_width, "sheet_size": sheet_size,
            "sheet_count": sheet_count, "sheet_format": sheet_format, "sheet_rows": sheet_rows,
            "sheet_lines": sheet_lines, "sheet_width": sheet_width, "sheet_height": sheet_height,
            "sheet_image_offset_hex": hx(sheet_image),
        },
        "cwdh_offset_hex": hx(cwdh),
        "cmap_scan_offset_hex": hx(scan["offset"]),
        "cmap_capacity": capacity,
        "cmap_entry_count": len(pairs),
        "preserved_non_hangul_entries": [f"U+{cp:04X}" for cp, _ in preserved],
        "hangul_count": len(assignments),
        "assignments": assignments,
        "missing_required_codepoints": missing,
    }
    return result, report


def parse_tsv(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text, newline=""), delimiter="\t", quotechar='"'))


def build_csv(name: str, translations: list[tuple[str, str]]) -> dict:
    source_path = SRC / name
    source = source_path.read_bytes()
    if source[:2] != b"\xFE\xFF":
        raise ValueError(f"{name}: missing UTF-16BE BOM")
    source_text = source[2:].decode("utf-16-be")
    output_text = source_text
    for jp, ko in translations:
        needle = f'"{jp}"'
        replacement = f'"{ko}"'
        if output_text.count(needle) != 1:
            raise ValueError((name, jp, output_text.count(needle)))
        output_text = output_text.replace(needle, replacement, 1)
    output = b"\xFE\xFF" + output_text.encode("utf-16-be")
    output_path = PAYLOAD / name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output)

    src_rows, out_rows = parse_tsv(source_text), parse_tsv(output_text)
    if len(src_rows) != 4 or len(out_rows) != 4:
        raise AssertionError((len(src_rows), len(out_rows)))
    if any(len(row) != 7 for row in src_rows + out_rows):
        raise AssertionError("expected 7 language columns per row")
    if any(src[1:] != out[1:] for src, out in zip(src_rows, out_rows)):
        raise AssertionError("non-Japanese language columns changed")
    expected_ko = [ko for _, ko in translations]
    if [row[0] for row in out_rows] != expected_ko:
        raise AssertionError("Korean first column mismatch")
    return {
        "physical_path": f"Hbm/{name}",
        "source_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        "output_path": str(output_path.relative_to(ROOT)).replace("\\", "/"),
        "source_size": len(source),
        "output_size": len(output),
        "source_sha256": sha256(source),
        "output_sha256": sha256(output),
        "bom_preserved": output[:2] == b"\xFE\xFF",
        "encoding": "UTF-16BE",
        "row_count": len(out_rows),
        "columns_per_row": [len(row) for row in out_rows],
        "other_language_columns_unchanged": True,
        "first_column": [
            {"source_ja": jp, "translation_ko": ko, "provenance": "Codex internal model"}
            for jp, ko in translations
        ],
    }


def glyph_map(font: bytes) -> dict[int, int]:
    out: dict[int, int] = {}
    for cmap in parse_cmaps(font):
        out.update(cmap["mapping"])
    return out


def decode_brfnt_sheets(font: bytes) -> tuple[list[Image.Image], dict]:
    tglp = font.find(b"TGLP")
    cell_width, cell_height = struct.unpack_from(">BB", font, tglp + 8)
    sheet_size = struct.unpack_from(">I", font, tglp + 12)[0]
    sheet_count, _, rows, lines, width, height = struct.unpack_from(">HHHHHH", font, tglp + 16)
    image_offset = struct.unpack_from(">I", font, tglp + 28)[0]
    sheets = [decode_i4(font[image_offset + i * sheet_size:image_offset + (i + 1) * sheet_size], width, height) for i in range(sheet_count)]
    return sheets, {"cell_width": cell_width, "cell_height": cell_height, "rows": rows, "lines": lines, "width": width, "height": height}


def render_with_brfnt(font: bytes, text: str) -> Image.Image:
    cmap = glyph_map(font)
    cwdh = font.find(b"CWDH")
    sheets, h = decode_brfnt_sheets(font)
    lines = text.replace("\r", "").split("\n")
    missing = sorted({ch for ch in text if ch not in "\r\n" and ord(ch) not in cmap})
    if missing:
        raise ValueError(f"BRFNT preview missing: {missing}")
    widths = []
    for line in lines:
        widths.append(sum(font[cwdh + 16 + cmap[ord(ch)] * 3 + 2] for ch in line))
    canvas = Image.new("L", (max(widths) + 8, len(lines) * 34 + 4), 0)
    for li, line in enumerate(lines):
        x = 4
        for ch in line:
            glyph = cmap[ord(ch)]
            left, glyph_width, char_width = struct.unpack_from(">bBB", font, cwdh + 16 + glyph * 3)
            sheet = glyph // (h["rows"] * h["lines"])
            within = glyph % (h["rows"] * h["lines"])
            sx = (within % h["rows"]) * (h["width"] // h["rows"])
            sy = (within // h["rows"]) * (h["height"] // h["lines"])
            cell = sheets[sheet].crop((sx, sy, sx + h["cell_width"], sy + h["cell_height"]))
            layer = Image.new("L", canvas.size, 0)
            layer.paste(cell, (x + left, 2 + li * 34))
            canvas = ImageChops.lighter(canvas, layer)
            x += char_width
    return canvas


def make_contact_sheet(entries: list[dict], path: Path) -> None:
    font = ImageFont.truetype(str(FONT_PATH), 18)
    label_font = ImageFont.truetype(str(FONT_BOLD_PATH), 18)
    max_w = max(max(e["original_image"].width, e["korean_image"].width) for e in entries)
    row_h = [max(e["original_image"].height, e["korean_image"].height) * 2 + 38 for e in entries]
    width = 24 + max_w * 4 + 64
    height = 52 + sum(row_h)
    out = Image.new("RGB", (width, height), (25, 25, 25))
    d = ImageDraw.Draw(out)
    d.text((20, 10), "원본 JP", font=label_font, fill=(255, 220, 80))
    d.text((20 + max_w * 2 + 44, 10), "한국어", font=label_font, fill=(120, 230, 255))
    y = 50
    for entry, rh in zip(entries, row_h):
        d.text((20, y), entry["name"], font=font, fill=(210, 210, 210))
        y2 = y + 28
        for image, x in ((entry["original_image"], 20), (entry["korean_image"], 20 + max_w * 2 + 44)):
            show = image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST).convert("RGB")
            out.paste(show, (x, y2))
        y += rh
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)


def make_font_contact(font: bytes, assignments: list[dict], path: Path) -> None:
    sheets, h = decode_brfnt_sheets(font)
    label = ImageFont.truetype(str(FONT_PATH), 15)
    cols, cw, ch = 9, 116, 144
    rows = math.ceil(len(assignments) / cols)
    out = Image.new("RGB", (cols * cw, rows * ch), (28, 28, 28))
    d = ImageDraw.Draw(out)
    for i, a in enumerate(assignments):
        glyph = a["glyph_index"]
        sheet = glyph // (h["rows"] * h["lines"])
        within = glyph % (h["rows"] * h["lines"])
        sx = (within % h["rows"]) * (h["width"] // h["rows"])
        sy = (within // h["rows"]) * (h["height"] // h["lines"])
        crop = sheets[sheet].crop((sx, sy, sx + h["cell_width"], sy + h["cell_height"]))
        show = crop.resize((87, 93), Image.Resampling.NEAREST).convert("RGB")
        x, y = (i % cols) * cw, (i // cols) * ch
        d.text((4 + x, 3 + y), f"{a['character']} {a['codepoint']} g{glyph}", font=label, fill=(255, 225, 70))
        out.paste(show, (x + 14, y + 28))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)


def make_dynamic_text_contact(font: bytes, messages: list[str], path: Path) -> None:
    previews = [render_with_brfnt(font, s) for s in messages]
    label = ImageFont.truetype(str(FONT_PATH), 17)
    width = max(im.width for im in previews) * 2 + 40
    heights = [im.height * 2 + 42 for im in previews]
    out = Image.new("RGB", (width, sum(heights) + 10), (24, 24, 24))
    d = ImageDraw.Draw(out)
    y = 8
    for i, (message, preview, rh) in enumerate(zip(messages, previews, heights), 1):
        d.text((10, y), f"{i}. {message.replace(chr(13), '').replace(chr(10), ' / ')}", font=label, fill=(160, 220, 255))
        show = preview.resize((preview.width * 2, preview.height * 2), Image.Resampling.NEAREST).convert("RGB")
        out.paste(show, (10, y + 30))
        y += rh
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)


def main() -> None:
    PAYLOAD.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)

    csv_reports = [build_csv(name, translations) for name, translations in CSV_TRANSLATIONS.items()]
    all_ko_messages = []
    for translations in CSV_TRANSLATIONS.values():
        all_ko_messages.extend(ko for _, ko in translations)
    unique_messages = list(dict.fromkeys(all_ko_messages))
    hangul = sorted({ch for text in unique_messages for ch in text if "가" <= ch <= "힣"})

    source_arc_path = SRC / "homeBtn.arc"
    source_arc = source_arc_path.read_bytes()
    root_offset, nodes = parse_u8(source_arc)
    files = {n.name: n for n in nodes if n.kind == 0}
    patched = bytearray(source_arc)
    texture_reports = []
    contact_entries = []

    all_texture_names = set(TPL_TRANSLATIONS) | set(NEUTRAL_LANGUAGE_TEXTURES)
    for name in sorted(all_texture_names):
        node = files[name]
        member = source_arc[node.offset:node.offset + node.size]
        original_image, header = decode_tpl(member)
        if name in TPL_TRANSLATIONS:
            source_text, target_text = TPL_TRANSLATIONS[name]
            korean_image = render_centered(target_text, original_image.size)
            replacement = encode_tpl_with_image(member, korean_image)
            patched[node.offset:node.offset + node.size] = replacement
            changed = replacement != member
        else:
            source_text = NEUTRAL_LANGUAGE_TEXTURES[name]
            target_text = source_text
            korean_image = original_image.copy()
            replacement = member
            changed = False
        (AUDIT / "tpl_original").mkdir(exist_ok=True)
        (AUDIT / "tpl_korean").mkdir(exist_ok=True)
        original_image.save(AUDIT / "tpl_original" / f"{name}.png")
        korean_image.save(AUDIT / "tpl_korean" / f"{name}.png")
        contact_entries.append({"name": name, "original_image": original_image, "korean_image": korean_image})
        texture_reports.append({
            "member_path": node.path,
            "member_index": node.index,
            "archive_offset": node.offset,
            "archive_offset_hex": hx(node.offset),
            "size_bytes": node.size,
            "width": header["width"],
            "height": header["height"],
            "gx_format": "I4",
            "image_offset_hex": hx(header["image_offset"]),
            "source_text": source_text,
            "translation_ko": target_text,
            "translation_provenance": "Codex internal model" if name in TPL_TRANSLATIONS else "language-neutral retained",
            "changed": changed,
            "source_sha256": sha256(member),
            "output_sha256": sha256(replacement),
            "member_size_preserved": len(replacement) == len(member),
            "tpl_header_preserved": replacement[:header["image_offset"]] == member[:header["image_offset"]],
        })

    font_node = next(n for n in nodes if n.kind == 0 and n.name.endswith(".brfnt"))
    source_font = source_arc[font_node.offset:font_node.offset + font_node.size]
    korean_font, font_report = inject_hangul_brfnt(source_font, hangul)
    if len(korean_font) != font_node.size:
        raise AssertionError("BRFNT size changed")
    patched[font_node.offset:font_node.offset + font_node.size] = korean_font
    (AUDIT / "fonts").mkdir(exist_ok=True)
    (AUDIT / "fonts" / font_node.name).write_bytes(korean_font)

    output_arc = bytes(patched)
    output_arc_path = PAYLOAD / "homeBtn.arc"
    output_arc_path.write_bytes(output_arc)
    out_root, out_nodes = parse_u8(output_arc)
    if out_root != root_offset or [(n.kind, n.name, n.offset, n.size, n.path) for n in out_nodes] != [(n.kind, n.name, n.offset, n.size, n.path) for n in nodes]:
        raise AssertionError("U8 node table changed")

    target_paths = {r["member_path"] for r in texture_reports if r["changed"]} | {font_node.path}
    member_checks = []
    for src_node, dst_node in zip(nodes, out_nodes):
        if src_node.kind:
            continue
        src_member = source_arc[src_node.offset:src_node.offset + src_node.size]
        dst_member = output_arc[dst_node.offset:dst_node.offset + dst_node.size]
        member_checks.append({
            "member_path": src_node.path,
            "targeted": src_node.path in target_paths,
            "size_preserved": len(src_member) == len(dst_member),
            "changed": src_member != dst_member,
            "source_sha256": sha256(src_member),
            "output_sha256": sha256(dst_member),
        })
    unexpected = [x["member_path"] for x in member_checks if x["changed"] != x["targeted"]]
    if unexpected:
        raise AssertionError(("unexpected U8 member delta", unexpected))

    required_codepoints = {ord(ch) for text in unique_messages for ch in text if ch not in "\r\n"}
    final_map = glyph_map(korean_font)
    missing = sorted(required_codepoints - set(final_map))
    if missing:
        raise AssertionError([f"U+{cp:04X}" for cp in missing])

    tpl_contact_path = AUDIT / "homebtn_original_vs_korean.png"
    font_contact_path = AUDIT / "brfnt_korean_glyphs.png"
    dynamic_contact_path = AUDIT / "brfnt_dynamic_text_preview.png"
    make_contact_sheet(contact_entries, tpl_contact_path)
    make_font_contact(korean_font, font_report["assignments"], font_contact_path)
    make_dynamic_text_contact(korean_font, unique_messages, dynamic_contact_path)

    report = {
        "schema": "arf-hbm-korean-payload-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_services_used": [],
        "source_baseline_modified": False,
        "physical_payload_count": 3,
        "payload_root": str(PAYLOAD.relative_to(ROOT)).replace("\\", "/"),
        "csv_files": csv_reports,
        "home_button_archive": {
            "physical_path": "Hbm/homeBtn.arc",
            "source_path": str(source_arc_path.relative_to(ROOT)).replace("\\", "/"),
            "output_path": str(output_arc_path.relative_to(ROOT)).replace("\\", "/"),
            "source_size": len(source_arc),
            "output_size": len(output_arc),
            "source_sha256": sha256(source_arc),
            "output_sha256": sha256(output_arc),
            "format": "Nintendo U8",
            "root_offset_hex": hx(root_offset),
            "node_count": len(nodes),
            "node_table_and_member_offsets_preserved": True,
            "targeted_texture_count": sum(1 for r in texture_reports if r["changed"]),
            "language_neutral_texture_count": sum(1 for r in texture_reports if not r["changed"]),
            "textures": texture_reports,
            "font_member": {
                "member_path": font_node.path,
                "archive_offset": font_node.offset,
                "archive_offset_hex": hx(font_node.offset),
                "size_bytes": font_node.size,
                **font_report,
            },
            "member_validation": {
                "file_member_count": len(member_checks),
                "targeted_member_count": len(target_paths),
                "unexpected_changed_members": unexpected,
                "all_member_sizes_preserved": all(x["size_preserved"] for x in member_checks),
                "all_and_only_targeted_members_changed": not unexpected,
            },
        },
        "required_dynamic_font_corpus": {
            "unique_messages": unique_messages,
            "unique_hangul_count": len(hangul),
            "unique_hangul": "".join(hangul),
            "all_required_codepoints_mapped": not missing,
            "missing_codepoints": [f"U+{cp:04X}" for cp in missing],
        },
        "visual_evidence": {
            "tpl_original_vs_korean": {
                "path": str(tpl_contact_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(tpl_contact_path.read_bytes()),
            },
            "brfnt_korean_glyphs": {
                "path": str(font_contact_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(font_contact_path.read_bytes()),
            },
            "brfnt_dynamic_text_preview": {
                "path": str(dynamic_contact_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(dynamic_contact_path.read_bytes()),
            },
        },
        "static_validation": {
            "valid": True,
            "csv_bom_preserved": all(x["bom_preserved"] for x in csv_reports),
            "csv_other_language_columns_unchanged": all(x["other_language_columns_unchanged"] for x in csv_reports),
            "u8_size_preserved": len(source_arc) == len(output_arc),
            "u8_node_table_preserved": True,
            "all_target_tpl_sizes_and_headers_preserved": all(x["member_size_preserved"] and x["tpl_header_preserved"] for x in texture_reports if x["changed"]),
            "brfnt_size_and_header_preserved": len(source_font) == len(korean_font) and font_report["header_unchanged"],
            "all_required_dynamic_codepoints_mapped": not missing,
            "unexpected_changed_u8_members": unexpected,
        },
        "runtime_validation_required": [
            "Press HOME in a save-enabled scene and inspect every heading, button, controller-setting page and confirmation prompt.",
            "Press HOME in a no-save scene to exercise home_nosave.csv.",
            "Exercise reconnect/disconnect and verify ①/② glyphs, Hangul glyphs, line wrapping and clipping.",
        ],
    }
    report_path = BASE / "hbm_korean_payload_manifest.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Integration-ready Riivolution rules. CSV payloads grow, while the U8 archive is same-size.
    rules_path = BASE / "riivolution_hbm_rules.xml.fragment"
    rules_path.write_text(
        "\n".join([
            '<file disc="/Hbm/home.csv" external="Hbm/home.csv" resize="true" />',
            '<file disc="/Hbm/home_nosave.csv" external="Hbm/home_nosave.csv" resize="true" />',
            '<file disc="/Hbm/homeBtn.arc" external="Hbm/homeBtn.arc" resize="false" />',
            "",
        ]),
        encoding="utf-8",
    )

    md = [
        "# Wii HOME 메뉴 한국어 payload 보고서",
        "",
        "- 대상: Arc Rise Fantasia `RPJJ99`",
        "- 번역: Codex 내부 모델만 사용",
        "- 외부 번역 서비스/API: 사용하지 않음",
        "- 원본 추출물: 변경하지 않음",
        "- 정적 검증: **PASS**",
        "",
        "## 산출물",
        "",
        "| 물리 경로 | 출력 경로 | 크기 | SHA-256 |",
        "|---|---|---:|---|",
    ]
    for item in csv_reports:
        md.append(f"| `{item['physical_path']}` | `{item['output_path']}` | {item['output_size']} | `{item['output_sha256']}` |")
    md.append(f"| `Hbm/homeBtn.arc` | `{report['home_button_archive']['output_path']}` | {len(output_arc)} | `{sha256(output_arc)}` |")
    md += [
        "",
        "## CSV 번역",
        "",
        "| 파일 | 일본어 | 한국어 |",
        "|---|---|---|",
    ]
    for item in csv_reports:
        for row in item["first_column"]:
            jp = row["source_ja"].replace("\r\n", "<br>").replace("|", "\\|")
            ko = row["translation_ko"].replace("\r\n", "<br>").replace("|", "\\|")
            md.append(f"| `{item['physical_path']}` | {jp} | {ko} |")
    md += [
        "",
        "## homeBtn.arc 이미지",
        "",
        f"- Nintendo U8 크기와 {len(nodes)}개 node table/모든 member offset을 보존했다.",
        f"- 일본어 I4 TPL {sum(1 for x in texture_reports if x['changed'])}개를 같은 크기·같은 헤더·같은 캔버스로 교체했다.",
        f"- ON/OFF, 1P~4P 중립 표기 {sum(1 for x in texture_reports if not x['changed'])}개는 원본을 유지했다.",
        f"- 비교 이미지: `{tpl_contact_path.relative_to(ROOT).as_posix()}`",
        "",
        "| member | 원문 | 한국어 | 규격 |",
        "|---|---|---|---|",
    ]
    for item in texture_reports:
        if item["changed"]:
            md.append(f"| `{item['member_path']}` | {item['source_text']} | {item['translation_ko']} | {item['width']}×{item['height']} I4 |")
    md += [
        "",
        "## BRFNT 한글 주입",
        "",
        f"- member: `{font_node.path}` @ `{hx(font_node.offset)}`",
        f"- 크기 보존: {font_node.size} bytes",
        f"- 필요한 고유 한글 {len(hangul)}자를 기존 일본어 glyph slot 57~{56 + len(hangul)}에 주입했다.",
        f"- CMAP 용량 {font_report['cmap_capacity']}개 중 {font_report['cmap_entry_count']}개 사용.",
        "- ASCII, 유럽어 악센트, 공백, ①, ② 매핑은 보존했다.",
        "- 모든 CSV 코드포인트 매핑 확인: PASS",
        f"- glyph 시트: `{font_contact_path.relative_to(ROOT).as_posix()}`",
        f"- 실제 BRFNT 렌더 미리보기: `{dynamic_contact_path.relative_to(ROOT).as_posix()}`",
        "",
        "## 구조 검증",
        "",
    ]
    for key, value in report["static_validation"].items():
        md.append(f"- `{key}`: `{value}`")
    md += [
        "",
        "## 통합",
        "",
        f"- payload root: `{report['payload_root']}`",
        f"- Riivolution fragment: `{rules_path.relative_to(ROOT).as_posix()}`",
        "- CSV 두 파일은 크기가 바뀌므로 `resize=true`, homeBtn.arc는 같은 크기이므로 `resize=false`다.",
        "",
        "## 남은 런타임 검증",
        "",
        "- [ ] 저장 가능한 장면에서 HOME을 열어 모든 버튼/설정/확인 문구 확인",
        "- [ ] 저장 불가 장면에서 home_nosave.csv 경로 확인",
        "- [ ] 재연결/연결 해제 흐름에서 ①/②, 한글 glyph, 줄바꿈, clipping 확인",
        "",
    ]
    (BASE / "hbm_korean_payload_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({
        "valid": report["static_validation"]["valid"],
        "payload_root": report["payload_root"],
        "physical_payload_count": report["physical_payload_count"],
        "changed_tpl_members": report["home_button_archive"]["targeted_texture_count"],
        "hangul_glyph_count": len(hangul),
        "output_arc_sha256": report["home_button_archive"]["output_sha256"],
        "manifest": str(report_path.relative_to(ROOT)).replace("\\", "/"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
