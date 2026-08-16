#!/usr/bin/env python3
"""Build the append-only font v3 corpus, codebook, injected pages, and proofs."""

from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
OUT = W / "font" / "final_v3"
BASE = W / "font" / "final_v2"
SKILLS = W / "translation" / "battle_enemy" / "battle_enemy_skill_translations.json"
MAPPING = W / "research" / "font_agent" / "arf_euc28_mapping.py"
WTMD = W / "research" / "font_agent" / "wtmd_font_tool.py"
VERIFY_APPEND = W / "research" / "verify_append_only_codebook.py"
VERIFY_INJECTION = W / "research" / "verify_injected_fonts.py"
ENCODER = W / "research" / "encode_custom_euc28.py"
SOURCE_FONTS = W / "font" / "canonical_v1" / "source_original"
RESERVED = W / "font" / "original_reserved_pairs_v2.txt"
FONT = Path(r"C:\Windows\Fonts\malgunbd.ttf")


def run(*args: object) -> None:
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def main() -> int:
    for path in (SKILLS, BASE / "approved_units.jsonl", BASE / "codebook.json",
                 MAPPING, WTMD, VERIFY_APPEND, VERIFY_INJECTION, ENCODER,
                 RESERVED, FONT):
        if not path.is_file():
            raise SystemExit(f"missing font build input: {path}")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = json.loads(SKILLS.read_text(encoding="utf-8-sig"))["translations"]
    if len(rows) != 212 or len({row["source_text"] for row in rows}) != 212:
        raise SystemExit("battle text translation map must contain 212 unique sources")
    targets = [row["translation_ko"] for row in rows] + ["레이 스톤"]
    corpus = OUT / "battle_enemy_korean_corpus.txt"
    corpus.write_text("\n".join(targets) + "\n", encoding="utf-8")

    base_text = (BASE / "approved_units.jsonl").read_text(encoding="utf-8").rstrip("\n")
    appended = [
        json.dumps(
            {"tm_id": f"ARF-BTL-ENEMY-SKILL-{index:03d}", "translation_ko": row["translation_ko"]},
            ensure_ascii=False,
            separators=(", ", ": "),
        )
        for index, row in enumerate(rows)
    ]
    appended.append(json.dumps(
        {"tm_id": "ARF-BTL-ENEMY-NAME-269", "translation_ko": "레이 스톤"},
        ensure_ascii=False,
        separators=(", ", ": "),
    ))
    approved = OUT / "approved_units.jsonl"
    approved.write_text(base_text + "\n" + "\n".join(appended) + "\n", encoding="utf-8")

    run(sys.executable, MAPPING, "codebook", corpus, "-o", OUT / "codebook.json",
        "--existing", BASE / "codebook.json", "--reserve-hex", RESERVED)
    run(sys.executable, VERIFY_APPEND, BASE / "codebook.json", OUT / "codebook.json",
        corpus, RESERVED, OUT / "codebook_append_only_verification.json")
    run(sys.executable, MAPPING, "inject", "--source-dir", SOURCE_FONTS,
        "--output-dir", OUT / "injected", "--codebook", OUT / "codebook.json",
        "--font", FONT, "--font-size", "22", "--wtmd-tool", WTMD,
        "--manifest", OUT / "injection_manifest.json")
    run(sys.executable, VERIFY_INJECTION, "--source-dir", SOURCE_FONTS,
        "--injected-dir", OUT / "injected", "--codebook", OUT / "codebook.json",
        "--reserved-hex", RESERVED, "--approved-units", approved,
        "--manifest", OUT / "injection_manifest.json", "--mapping-tool", MAPPING,
        "--wtmd-tool", WTMD, "--encoder", ENCODER,
        "--output", OUT / "injection_verification.json")

    verification = json.loads((OUT / "injection_verification.json").read_text(encoding="utf-8"))
    if not verification.get("valid") or verification.get("approved_units_encoded") != 30915:
        raise SystemExit("font v3 verification failed")
    print(json.dumps({
        "battle_text_units": len(rows), "approved_units": verification["approved_units_encoded"],
        "assigned_characters": verification["assigned_characters"],
        "error_count": verification["error_count"], "valid": verification["valid"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
