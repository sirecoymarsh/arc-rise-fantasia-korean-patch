#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "work" / "runtime_fix" / "endroll_ui"
SOURCE_DIR = ROOT / "work" / "disc_extracted" / "DATA" / "files" / "Event" / "endroll"
PAYLOAD_DIR = BASE / "payloads" / "Event" / "endroll"
BEFORE_DIR = BASE / "before_png"
AFTER_DIR = BASE / "after_png"
FONT_PATH = Path(r"C:\Windows\Fonts\malgunbd.ttf")
PIPELINE_PATH = ROOT / "work" / "image_ui_final" / "tools" / "wtmd_pipeline.py"

spec = importlib.util.spec_from_file_location("wtmd_pipeline", PIPELINE_PATH)
wtmd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(wtmd)


TRANSLATIONS = [
    ("やっほー!!\nラルク、起きる時間だよー!!", "야호~!!\n라르크, 일어날 시간이야~!!"),
    ("起きろってば、おきろー!!", "일어나라니까, 일어나~!!"),
    ("……ん", "……응"),
    ("お前が目覚める時に合わせて\n我々のメッセージを残しておく", "네가 깨어날 때에 맞춰\n우리의 메시지를 남겨 두마"),
    ("お前が寂しがるといけないんでな。\n気の利いたモーニングコールだろ？", "네가 외로워하면 안 되니까.\n센스 있는 모닝콜이지?"),
    ("ソニアの計算だと\nあなたが目覚めるのはおよそ５００年後よ", "소니아의 계산대로라면\n네가 깨어나는 건 약 500년 뒤야"),
    ("お前が眠ってから大変だったぜ。\nま、アルス坊やが頑張ってくれてな", "네가 잠든 뒤로 참 힘들었지.\n뭐, 알스 꼬마가 애써 준 덕에"),
    ("今度はましな皇帝になれそうだぜ", "이번엔 제법 괜찮은 황제가 되겠어"),
    ("我らも全力でサポートするつもりだ", "우리도 전력으로 도울 생각이다"),
    ("私は５年たったら\n眠りについてちゃうけどね", "난 5년 뒤면\n잠들어 버리겠지만"),
    ("希望がある限り、人は前に向かって\n歩いて行くことが出来る", "희망이 있는 한, 사람은 앞을 향해\n걸어갈 수 있어"),
    ("あなたが目覚める約束の日まで\n私たちは必死で生き抜いてみせる", "네가 깨어나기로 한 약속의 날까지\n우린 필사적으로 살아남을게"),
    ("みんな……", "다들……"),
    ("だから、安心していいよ", "그러니 안심해도 돼"),
    ("ラルクが目覚めたとき\nラルクは独りぼっちじゃないよ", "라르크가 깨어날 때\n라르크는 혼자가 아닐 거야"),
    ("私たちの心を受け継いだ誰かが\n必ずラルクを迎えてくれるわ", "우리 마음을 이어받은 누군가가\n반드시 라르크를 맞아 줄 거야"),
    ("約束する。この人の世を\n５００年後のお前に託すことを", "약속하지. 이 인간 세상을\n500년 뒤의 네게 맡기겠다"),
    ("――そろそろ時間だ", "――슬슬 시간이군"),
    ("じゃあな、ラルク。\nお前は最高の相棒だったぜ", "잘 있어라, 라르크.\n넌 최고의 파트너였다"),
    ("ばいば～い！　また未来でね！", "바이바~이! 미래에서 또 봐!"),
    ("お姉さんのこと\n忘れちゃダ・メ・ヨ", "누나를\n잊으면 안·돼·요"),
    ("さらばだ。\nお前と共に在れたことを誇りに思う", "잘 있어라.\n너와 함께했음을 자랑스럽게 여긴다"),
    ("……リフィアは……\nリフィアはどうしたんだ……", "……리피아는……\n리피아는 어떻게 된 거야……"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, stroke: int, spacing: int):
    return draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center", stroke_width=stroke)


def fit_font(text: str, width: int, height: int):
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    max_size = 22 if "\n" not in text else 20
    for size in range(max_size, 13, -1):
        font = ImageFont.truetype(str(FONT_PATH), size)
        bbox = text_bbox(probe, text, font, 2, 0)
        if bbox[2] - bbox[0] <= width - 10 and bbox[3] - bbox[1] <= height - 4:
            return font, size, bbox
    raise ValueError(f"text cannot fit canvas: {text!r}")


def render_text(text: str, width: int, height: int):
    # Four-times supersampling keeps the original subtitle-like rounded edge;
    # C4 quantization later maps the edge to the source alpha ramp.
    scale = 4
    font, size, _ = fit_font(text, width, height)
    font_hi = ImageFont.truetype(str(FONT_PATH), size * scale)
    spacing_hi = 0
    canvas = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    bbox = draw.multiline_textbbox(
        (0, 0), text, font=font_hi, spacing=spacing_hi, align="center", stroke_width=2 * scale
    )
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width * scale - tw) // 2 - bbox[0]
    y = (height * scale - th) // 2 - bbox[1]
    draw.multiline_text(
        (x, y), text, font=font_hi, spacing=spacing_hi, align="center",
        fill=(247, 247, 247, 255), stroke_width=2 * scale, stroke_fill=(0, 0, 17, 255),
    )
    out = canvas.resize((width, height), Image.Resampling.LANCZOS)
    return out, size


def contact_sheet(images: list[tuple[str, Image.Image]], output: Path):
    cols = 2
    cell_w = 330
    cell_h = 82
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows), (28, 28, 28))
    draw = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype(str(FONT_PATH), 11)
    for i, (label, image) in enumerate(images):
        col, row = i % cols, i // cols
        x, y = col * cell_w, row * cell_h
        draw.text((5 + x, 3 + y), label, font=label_font, fill=(255, 226, 0))
        checker = Image.new("RGBA", image.size, (36, 36, 36, 255))
        checker.alpha_composite(image)
        sheet.paste(checker.convert("RGB"), (x + (cell_w - image.width) // 2, y + 26))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def main():
    for directory in (PAYLOAD_DIR, BEFORE_DIR, AFTER_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    translation_entries = []
    validation_rows = []
    manifest_files = []
    before_images = []
    after_images = []

    for index, (source_jp, translation_ko) in enumerate(TRANSLATIONS):
        name = f"EV09_18_0200C_{index:02d}.wtm"
        source_path = SOURCE_DIR / name
        output_path = PAYLOAD_DIR / name
        source_bytes = source_path.read_bytes()
        before, source_header = wtmd.decode_wtmd(source_bytes)
        rendered, font_size = render_text(translation_ko, source_header["width"], source_header["height"])
        output_bytes, output_header = wtmd.encode_wtmd(source_bytes, rendered)
        second_build_bytes, _ = wtmd.encode_wtmd(source_bytes, rendered)
        output_path.write_bytes(output_bytes)

        before_path = BEFORE_DIR / f"{Path(name).stem}.png"
        after_path = AFTER_DIR / f"{Path(name).stem}.png"
        before.save(before_path)
        decoded_after, decoded_header = wtmd.decode_wtmd(output_bytes)
        decoded_after.save(after_path)

        # Exact round-trip through the decoded palette colors proves stable C4
        # indexing and catches palette-nearest-neighbour ambiguity.
        roundtrip_bytes, _ = wtmd.encode_wtmd(output_bytes, decoded_after)
        header_palette_equal = source_bytes[:source_header["image_pos"]] == output_bytes[:output_header["image_pos"]]
        decoded_bbox = decoded_after.getbbox()
        clipping_clear = decoded_bbox is not None and decoded_bbox[0] >= 2 and decoded_bbox[1] >= 1 and decoded_bbox[2] <= decoded_after.width - 2 and decoded_bbox[3] <= decoded_after.height - 1
        row_valid = all([
            len(source_bytes) == len(output_bytes),
            source_header["width"] == decoded_header["width"],
            source_header["height"] == decoded_header["height"],
            source_header["gx"] == decoded_header["gx"] == 8,
            source_header["pal"] == decoded_header["pal"],
            source_header["image_pos"] == decoded_header["image_pos"],
            header_palette_equal,
            second_build_bytes == output_bytes,
            roundtrip_bytes == output_bytes,
            clipping_clear,
        ])

        translation_entries.append({
            "index": index,
            "physical_path": f"Event/endroll/{name}",
            "source_text_jp": source_jp,
            "translation_ko": translation_ko,
            "line_count": translation_ko.count("\n") + 1,
            "font": str(FONT_PATH),
            "font_size_px": font_size,
            "canvas": [source_header["width"], source_header["height"]],
            "provenance": "Codex internal model",
            "external_translation_used": False,
        })
        validation_rows.append({
            "physical_path": f"Event/endroll/{name}",
            "valid": row_valid,
            "source_size": len(source_bytes),
            "output_size": len(output_bytes),
            "size_equal": len(source_bytes) == len(output_bytes),
            "source_sha256": sha256(source_bytes),
            "output_sha256": sha256(output_bytes),
            "dimensions": [decoded_header["width"], decoded_header["height"]],
            "gx_format": decoded_header["gx_name"],
            "palette_format": decoded_header["pal_name"],
            "image_data_offset": decoded_header["image_pos"],
            "header_palette_preserved": header_palette_equal,
            "deterministic_second_build_equal": second_build_bytes == output_bytes,
            "byte_exact_decode_reencode": roundtrip_bytes == output_bytes,
            "nontransparent_bbox": list(decoded_bbox) if decoded_bbox else None,
            "clipping_clear": clipping_clear,
            "before_png_sha256": sha256(before_path.read_bytes()),
            "after_png_sha256": sha256(after_path.read_bytes()),
        })
        manifest_files.append({
            "physical_path": f"Event/endroll/{name}",
            "payload_path": f"payloads/Event/endroll/{name}",
            "source_sha256": sha256(source_bytes),
            "payload_sha256": sha256(output_bytes),
            "size_bytes": len(output_bytes),
        })
        before_images.append((f"{index:02d} {name}", before))
        after_images.append((f"{index:02d} {name}", decoded_after))

    contact_sheet(before_images, BASE / "before_contact_sheet.png")
    contact_sheet(after_images, BASE / "after_contact_sheet.png")

    payload_aggregate = hashlib.sha256()
    for payload in sorted(PAYLOAD_DIR.glob("*.wtm"), key=lambda p: p.name):
        payload_aggregate.update(payload.name.encode("utf-8"))
        payload_aggregate.update(payload.read_bytes())
    payload_aggregate_sha256 = payload_aggregate.hexdigest().upper()

    (BASE / "translation_map.json").write_text(json.dumps({
        "schema": "arf-endroll-baked-dialogue-ko-v1",
        "translation_policy": "Codex internal model only",
        "external_translation_services_used": [],
        "entry_count": len(translation_entries),
        "entries": translation_entries,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errors = [r["physical_path"] for r in validation_rows if not r["valid"]]
    (BASE / "structural_validation.json").write_text(json.dumps({
        "schema": "arf-endroll-wtm-structural-validation-v1",
        "valid": not errors,
        "checked_count": len(validation_rows),
        "passed_count": len(validation_rows) - len(errors),
        "failed_count": len(errors),
        "errors": errors,
        "deterministic_rebuild_passed": all(r["deterministic_second_build_equal"] for r in validation_rows),
        "payload_aggregate_sha256": payload_aggregate_sha256,
        "invariants": [
            "source/output byte size equality",
            "312x48 or 320x48 dimensions preserved",
            "GX C4 preserved",
            "source palette format and image-data offset preserved",
            "header and palette bytes preserved byte-for-byte",
            "independent second encode from the same source and rendered RGBA is byte-exact",
            "decoded output re-encodes byte-exactly",
            "nontransparent text bounding box remains inside canvas margins",
        ],
        "files": validation_rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (BASE / "manifest.json").write_text(json.dumps({
        "schema": "arf-endroll-wtm-payload-manifest-v1",
        "game_id": "RPJJ99",
        "file_count": len(manifest_files),
        "payload_aggregate_sha256": payload_aggregate_sha256,
        "source_root": "work/disc_extracted/DATA/files",
        "payload_root": "work/runtime_fix/endroll_ui/payloads",
        "staging_or_release_modified": False,
        "before_contact_sheet": "before_contact_sheet.png",
        "after_contact_sheet": "after_contact_sheet.png",
        "translation_map": "translation_map.json",
        "structural_validation": "structural_validation.json",
        "files": manifest_files,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "file_count": len(manifest_files),
        "passed": len(manifest_files) - len(errors),
        "failed": len(errors),
        "payload_root": str(PAYLOAD_DIR.relative_to(ROOT)).replace("\\", "/"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
