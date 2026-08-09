#!/usr/bin/env python3
"""Build a deterministic Korean glyph corpus from approved ARF TM units."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("translation_memory", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--extra-text", type=Path, action="append", default=[])
    args = parser.parse_args()

    memory = json.loads(args.translation_memory.read_text(encoding="utf-8"))
    units = [
        {
            "tm_id": str(unit["tm_id"]),
            "translation_ko": str(unit["translation_ko"]),
        }
        for unit in memory["units"]
        if unit.get("review_status") == "approved"
        and str(unit.get("translation_ko", "")).strip()
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    units_path = args.output_dir / "approved_units.jsonl"
    corpus_path = args.output_dir / "approved_korean_corpus.txt"
    manifest_path = args.output_dir / "corpus_manifest.json"

    units_path.write_text(
        "".join(
            json.dumps(unit, ensure_ascii=False, separators=(",", ":")) + "\n"
            for unit in units
        ),
        encoding="utf-8",
    )
    corpus_parts = [unit["translation_ko"] for unit in units]
    for path in args.extra_text:
        text = path.read_text(encoding="utf-8").rstrip("\r\n")
        if text:
            corpus_parts.append(text)
    corpus_path.write_text("\n".join(corpus_parts) + "\n", encoding="utf-8")

    corpus = corpus_path.read_text(encoding="utf-8")
    hangul = sorted(
        {
            char
            for char in corpus
            if ("가" <= char <= "힣")
            or ("㄰" <= char <= "㆏")
            or ("ᄀ" <= char <= "ᇿ")
        },
        key=ord,
    )
    manifest = {
        "schema": "arf-approved-korean-corpus-v1",
        "translation_memory": str(args.translation_memory.resolve()),
        "translation_memory_sha256": sha256(args.translation_memory),
        "translation_engine_policy": "Codex internal models only",
        "approved_units": len(units),
        "extra_text_files": [str(path.resolve()) for path in args.extra_text],
        "extra_text_artifacts": [
            {
                "path": str(path.resolve()),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in args.extra_text
        ],
        "unique_hangul": len(hangul),
        "hangul_characters": "".join(hangul),
        "approved_units_jsonl_sha256": sha256(units_path),
        "corpus_sha256": sha256(corpus_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
