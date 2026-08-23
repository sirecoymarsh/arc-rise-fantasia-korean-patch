#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work/scratch/btl_usual_ui_png"
OUTPUT = ROOT / "work/battle_ui_raster_application"
FONT = Path(r"C:\Windows\Fonts\malgunbd.ttf")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fit_font(draw: ImageDraw.ImageDraw, text: str, box, max_size: int, stroke: int):
    left, top, right, bottom = box
    for size in range(max_size, 7, -1):
        font = ImageFont.truetype(str(FONT), size)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        if bbox[2] - bbox[0] <= right - left and bbox[3] - bbox[1] <= bottom - top:
            return font, bbox, size
    raise RuntimeError(f"text does not fit: {text}")


def draw_centered(image: Image.Image, text: str, box, *, fill, stroke_fill, stroke_width, max_size, glow=None):
    draw = ImageDraw.Draw(image)
    font, bbox, size = fit_font(draw, text, box, max_size, stroke_width)
    left, top, right, bottom = box
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = left + (right - left - width) // 2 - bbox[0]
    y = top + (bottom - top - height) // 2 - bbox[1]
    if glow:
        glow_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        gd.text((x, y), text, font=font, fill=glow, stroke_width=stroke_width + 2, stroke_fill=glow)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(3))
        image.alpha_composite(glow_layer)
    draw = ImageDraw.Draw(image)
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
    return {"text": text, "box": list(box), "bbox": list(draw.textbbox((x, y), text, font=font, stroke_width=stroke_width)), "font_size": size}


def small_asset(name: str, text: str, box, max_size: int) -> dict:
    source = SOURCE / (name + ".png")
    original = Image.open(source).convert("RGBA")
    image = Image.new("RGBA", original.size, (0, 0, 0, 0))
    render = draw_centered(image, text, box, fill=(180, 255, 255, 255), stroke_fill=(0, 44, 116, 255), stroke_width=1, max_size=max_size, glow=(0, 150, 255, 150))
    output = OUTPUT / "preview_png" / (name + ".png")
    image.save(output)
    return {"name": name, "source": str(source), "output": str(output), "source_sha256": sha256(source), "output_sha256": sha256(output), "render": render}


def banner_asset(name: str, text: str, color: str) -> dict:
    source = SOURCE / (name + ".png")
    original = Image.open(source).convert("RGBA")
    image = original.copy()
    draw = ImageDraw.Draw(image)
    width, height = image.size
    # The line art ends outside this center plate.  Clear only the original
    # Japanese/English lettering; leave the horizontal rays untouched.
    clear = (104, 0, width - 104, height)
    draw.rectangle((clear[0], clear[1], clear[2] - 1, clear[3] - 1), fill=(0, 0, 0, 0))
    if color == "blue":
        fill, stroke, glow = (238, 255, 255, 255), (0, 84, 170, 255), (0, 180, 255, 210)
    else:
        fill, stroke, glow = (255, 118, 45, 255), (132, 0, 0, 255), (255, 55, 0, 210)
    render = draw_centered(image, text, (96, 4, width - 96, height - 4), fill=fill, stroke_fill=stroke, stroke_width=2, max_size=36, glow=glow)
    output = OUTPUT / "preview_png" / (name + ".png")
    image.save(output)
    return {"name": name, "source": str(source), "output": str(output), "source_sha256": sha256(source), "output_sha256": sha256(output), "cleared_box": list(clear), "render": render}


def contact_sheet(rows: list[dict]) -> Path:
    images = [(row["name"], Image.open(row["output"]).convert("RGBA")) for row in rows]
    width = max(520, max(img.width for _, img in images) + 40)
    height = sum(img.height + 42 for _, img in images) + 20
    sheet = Image.new("RGBA", (width, height), (25, 27, 29, 255))
    draw = ImageDraw.Draw(sheet)
    label = ImageFont.truetype(str(Path(r"C:\Windows\Fonts\malgun.ttf")), 15)
    y = 12
    for name, img in images:
        draw.text((14, y), name, font=label, fill=(245, 245, 245, 255))
        y += 24
        sheet.alpha_composite(img, ((width - img.width) // 2, y))
        y += img.height + 18
    out = OUTPUT / "battle_ui_korean_preview_contact_sheet.png"
    sheet.convert("RGB").save(out)
    return out


def main() -> None:
    if not FONT.is_file():
        raise FileNotFoundError(FONT)
    (OUTPUT / "preview_png").mkdir(parents=True, exist_ok=True)
    rows = [
        small_asset("btl_comandlist_moji.wtm", "명령", (0, 0, 56, 24), 17),
        banner_asset("btl_renkei_moji_renkei.wtm", "연계", "blue"),
        banner_asset("btl_renkei_moji_renkei_enemy.wtm", "연계", "red"),
        banner_asset("btl_renkei_moji_syugeki.wtm", "선제공격", "blue"),
        banner_asset("btl_renkei_moji_tekisyu.wtm", "기습", "red"),
        small_asset("btl_tactics_moji.wtm", "작전 1 2 3", (0, 0, 88, 24), 16),
    ]
    sheet = contact_sheet(rows)
    report = {
        "schema": "arf-battle-raster-ui-preview-v1",
        "game_id": "RPJJ99",
        "translator_model": "Codex internal",
        "font": str(FONT),
        "font_sha256": sha256(FONT),
        "translations": {
            "コマンド": "명령",
            "連携": "연계",
            "襲撃 / First attack": "선제공격",
            "敵襲 / Back attack": "기습",
            "作戦 1 2 3": "작전 1 2 3"
        },
        "assets": rows,
        "contact_sheet": str(sheet),
        "contact_sheet_sha256": sha256(sheet),
        "valid": True
    }
    (OUTPUT / "preview_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"contact_sheet": str(sheet), "assets": len(rows), "valid": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
