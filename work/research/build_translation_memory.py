#!/usr/bin/env python3
"""Deduplicate the ARF source catalog into context-rich Codex translation units."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


CONTROL_RE = re.compile(r"<\$[0-9A-F]{2}>")
SURFACE_PRIORITY = {
    "system_database": 0,
    "battle_text": 1,
    "misc_text": 2,
    "event_script": 3,
    "map_dialogue": 4,
}


def tm_id(source_text: str) -> str:
    return "ARF-TM-" + hashlib.sha1(("ja-JP\0" + source_text).encode("utf-8")).hexdigest()[:20].upper()


def compact_context(record: dict[str, object]) -> dict[str, object]:
    return {
        "surface": record["surface"],
        "logical_locator": record["logical_locator"],
        "offset_hex": record["offset_hex"],
        "previous_source": record["previous_source"],
        "next_source": record["next_source"],
    }


def build_units(records: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        groups[str(record["source_text"])].append(record)

    units: list[dict[str, object]] = []
    for source_text, occurrences in groups.items():
        surfaces = Counter(str(item["surface"]) for item in occurrences)
        locators = {str(item["logical_locator"]) for item in occurrences}
        raw_forms = Counter(str(item["raw_hex"]) for item in occurrences)
        lengths = sorted({int(item["byte_length"]) for item in occurrences})
        contexts: list[dict[str, object]] = []
        seen_contexts: set[tuple[object, ...]] = set()
        for occurrence in occurrences:
            candidate = compact_context(occurrence)
            key = (
                candidate["surface"],
                candidate["previous_source"],
                candidate["next_source"],
            )
            if key in seen_contexts:
                continue
            seen_contexts.add(key)
            contexts.append(candidate)
            if len(contexts) >= 8:
                break

        controls = CONTROL_RE.findall(source_text)
        visible_without_controls = CONTROL_RE.sub("", source_text)
        primary_surface = min(surfaces, key=lambda name: (SURFACE_PRIORITY.get(name, 99), -surfaces[name], name))
        short = len(visible_without_controls.strip()) <= 8
        dialogue_surface = any(name in {"event_script", "map_dialogue"} for name in surfaces)
        context_sensitive = (short and len(locators) > 1) or (dialogue_surface and len(contexts) > 1)
        units.append(
            {
                "tm_id": tm_id(source_text),
                "source_language": "ja-JP",
                "target_language": "ko-KR",
                "source_text": source_text,
                "translation_ko": "",
                "status": "untranslated",
                "review_status": "pending",
                "primary_surface": primary_surface,
                "surface_counts": dict(sorted(surfaces.items())),
                "occurrence_count": len(occurrences),
                "logical_asset_count": len(locators),
                "byte_lengths": lengths,
                "control_tokens": controls,
                "context_sensitive": context_sensitive,
                "raw_form_count": len(raw_forms),
                "sample_contexts": contexts,
                "occurrence_ids": [str(item["id"]) for item in occurrences],
                "translator": "",
                "reviewer": "",
                "notes": "",
            }
        )

    units.sort(
        key=lambda unit: (
            SURFACE_PRIORITY.get(str(unit["primary_surface"]), 99),
            bool(unit["context_sensitive"]),
            -int(unit["occurrence_count"]),
            str(unit["tm_id"]),
        )
    )
    return units


def write_batches(units: list[dict[str, object]], batch_dir: Path, batch_size: int) -> list[dict[str, object]]:
    batch_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for start in range(0, len(units), batch_size):
        batch_number = start // batch_size + 1
        chunk = units[start : start + batch_size]
        filename = f"batch_{batch_number:04d}.jsonl"
        path = batch_dir / filename
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for unit in chunk:
                payload = {
                    "tm_id": unit["tm_id"],
                    "source_text": unit["source_text"],
                    "translation_ko": "",
                    "primary_surface": unit["primary_surface"],
                    "occurrence_count": unit["occurrence_count"],
                    "control_tokens": unit["control_tokens"],
                    "context_sensitive": unit["context_sensitive"],
                    "sample_contexts": unit["sample_contexts"],
                    "notes": "",
                }
                handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        manifest.append(
            {
                "batch": batch_number,
                "file": filename,
                "unit_count": len(chunk),
                "first_tm_id": chunk[0]["tm_id"],
                "last_tm_id": chunk[-1]["tm_id"],
                "surface_counts": dict(Counter(str(unit["primary_surface"]) for unit in chunk)),
                "status": "untranslated",
                "translator_policy": "Codex internal models only",
            }
        )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    records = catalog["records"]
    units = build_units(records)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    document = {
        "schema": "arf-translation-memory-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "unit_count": len(units),
        "source_record_count": len(records),
        "units": units,
    }
    (args.output_dir / "translation_memory.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    columns = [
        "tm_id",
        "primary_surface",
        "occurrence_count",
        "logical_asset_count",
        "context_sensitive",
        "source_text",
        "translation_ko",
        "status",
        "review_status",
        "notes",
    ]
    with (args.output_dir / "translation_memory.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(units)

    manifest = write_batches(units, args.output_dir / "batches" / "source", args.batch_size)
    summary = {
        "schema": "arf-translation-batch-manifest-v1",
        "translation_engine_policy": "Codex internal models only",
        "batch_size": args.batch_size,
        "batch_count": len(manifest),
        "unit_count": len(units),
        "context_sensitive_count": sum(bool(unit["context_sensitive"]) for unit in units),
        "surface_counts": dict(Counter(str(unit["primary_surface"]) for unit in units)),
        "batches": manifest,
    }
    (args.output_dir / "batch_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "TRANSLATION_RULES.md").write_text(
        """# Codex 내부 번역 배치 규칙

1. 번역·교정·윤문은 Codex 내부 모델과 Codex 하위 에이전트만 수행한다.
2. 외부 번역 API/모델(Gemini, DeepL, Google Translate, Papago 등)은 사용하지 않는다.
3. `source_text`의 `<$XX>` 제어 토큰은 개수·순서·철자를 그대로 보존한다.
4. 문맥은 `sample_contexts`의 앞뒤 문장과 표면 종류를 함께 읽는다.
5. 고유명사와 시스템 용어는 승인된 glossary/style guide를 따른다.
6. 번역문은 자연스러운 한국어 완성 문장으로 작성하며 일본어 어순을 기계적으로 복제하지 않는다.
7. `context_sensitive=true`인 짧은 표현은 일괄 확정하지 말고 발생 위치별 override 필요 여부를 기록한다.
8. 번역자와 별도의 Codex 검수자가 의미·문체·제어 토큰·길이를 교차 검수한다.
""",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "source_records": len(records),
                "unique_units": len(units),
                "batches": len(manifest),
                "output": str(args.output_dir.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
