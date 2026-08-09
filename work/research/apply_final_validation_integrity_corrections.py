#!/usr/bin/env python3
"""Apply three hand-reviewed fixes found by final structural validation.

The affected review entries had accidentally received text from an unrelated
TM unit.  This script does not translate: it restores the already existing,
independently inspected draft text after pinning the TM ID, Japanese source,
bad reviewed value, and intended restored value.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "work/translation/reviews/final_validation_integrity_corrections.json"
REVIEWER = "/root/audit_boundary_integration"
CORRECTIONS = (
    {
        "batch": "batch_0023",
        "tm_id": "ARF-TM-85182D838A95053A2314",
        "source_text": "なんだと",
        "invalid_reviewed_translation": "대체 <$15>D4를 얼마나\n갖고 있슴까",
        "restored_translation": "뭐라고",
        "reason": (
            "Final control-token validation proved that an unrelated next-unit "
            "battle tutorial translation had been assigned to this TM ID."
        ),
    },
    {
        "batch": "batch_0083",
        "tm_id": "ARF-TM-1E9A93552C32759F440D",
        "source_text": "ええ。\nグラ慈恵教会のサージュよ",
        "invalid_reviewed_translation": (
            "어머, 도련님……\n누나한테 무슨 볼일이야?<$0C>나도 심심했으니까\n"
            "잠깐이라면\n놀아 줄 수도 있어♪"
        ),
        "restored_translation": "그래.\n그라 자혜교회의 사쥬야",
        "reason": (
            "Final control-token and source-meaning validation proved that text "
            "from batch_0082 had been copied into this unrelated TM ID."
        ),
    },
    {
        "batch": "batch_0116",
        "tm_id": "ARF-TM-9FD5DB54DC7DD5DC1DB0",
        "source_text": "……用がないなら\n話しかけないでもらおう",
        "invalid_reviewed_translation": (
            "원로원에서는 현재――\n많은 의원들로 인해\n회의가 난항을 겪고 있습니다"
            "<$0C>등원하시는 건 좋지만\n부디 주의하십시오"
        ),
        "restored_translation": "……용건이 없다면\n말 걸지 말아 주겠나",
        "reason": (
            "Final control-token and source-meaning validation proved that text "
            "from batch_0115 had been copied into this unrelated TM ID."
        ),
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
            for item in records
        ),
        encoding="utf-8",
    )


def main() -> int:
    results: list[dict[str, object]] = []
    for correction in CORRECTIONS:
        batch = str(correction["batch"])
        tm_id = str(correction["tm_id"])
        reviewed_path = ROOT / f"work/translation/reviewed/{batch}.jsonl"
        draft_path = ROOT / f"work/translation/drafts/{batch}.jsonl"
        review_path = ROOT / f"work/translation/reviews/{batch}_review.json"
        reviewed = read_jsonl(reviewed_path)
        drafts = read_jsonl(draft_path)
        reviewed_by_id = {str(item["tm_id"]): item for item in reviewed}
        draft_by_id = {str(item["tm_id"]): item for item in drafts}
        item = reviewed_by_id.get(tm_id)
        draft = draft_by_id.get(tm_id)
        if item is None or draft is None:
            raise ValueError(f"missing correction TM ID in {batch}: {tm_id}")
        if str(item.get("source_text")) != correction["source_text"]:
            raise ValueError(f"reviewed source mismatch for {tm_id}")
        if str(draft.get("source_text")) != correction["source_text"]:
            raise ValueError(f"draft source mismatch for {tm_id}")
        if str(item.get("translation_ko")) != correction["invalid_reviewed_translation"]:
            raise ValueError(f"unexpected reviewed value for {tm_id}")
        if str(draft.get("translation_ko")) != correction["restored_translation"]:
            raise ValueError(f"restored value is not the pinned draft for {tm_id}")

        before_hash = sha256(reviewed_path)
        item["translation_ko"] = correction["restored_translation"]
        marker = (
            "[final-validation] Restored the pinned draft after unrelated-unit "
            "review contamination was proven by structural and source checks."
        )
        notes = str(item.get("notes") or "")
        if marker not in notes:
            item["notes"] = (notes + (" " if notes else "") + marker).strip()
        write_jsonl(reviewed_path, reviewed)
        after_hash = sha256(reviewed_path)

        review = json.loads(review_path.read_text(encoding="utf-8"))
        modification_found = False
        for modification in review.get("modifications", []):
            if str(modification.get("tm_id")) != tm_id:
                continue
            modification_found = True
            modification["superseded_invalid_after"] = modification.get("after")
            modification["after"] = correction["restored_translation"]
            modification["category"] = "final_validation_integrity_correction"
            modification["reason"] = correction["reason"]
        if not modification_found:
            review.setdefault("modifications", []).append(
                {
                    "tm_id": tm_id,
                    "source_text": correction["source_text"],
                    "before": correction["invalid_reviewed_translation"],
                    "after": correction["restored_translation"],
                    "category": "final_validation_integrity_correction",
                    "reason": correction["reason"],
                }
            )
        modified_units = sum(
            str(current.get("translation_ko") or "")
            != str(draft_by_id[str(current["tm_id"])].get("translation_ko") or "")
            for current in reviewed
        )
        review["modified_units"] = modified_units
        review["unchanged_units"] = len(reviewed) - modified_units
        review["final_validation_corrections"] = {
            "schema": "arf-final-validation-integrity-correction-v1",
            "reviewer": REVIEWER,
            "independent_review": True,
            "translation_engine_policy": "Codex internal models only",
            "external_translation_services_used": [],
            "tm_ids": [tm_id],
            "reason": correction["reason"],
            "reviewed_sha256": after_hash,
        }
        review.setdefault("hashes", {})["reviewed_sha256"] = after_hash
        review_path.write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        results.append(
            {
                **correction,
                "reviewed_sha256_before": before_hash,
                "reviewed_sha256_after": after_hash,
                "review_report_sha256_after": sha256(review_path),
            }
        )

    report = {
        "schema": "arf-final-validation-integrity-corrections-v1",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "reviewer": REVIEWER,
        "correction_count": len(results),
        "corrections": results,
    }
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "correction_count": len(results),
                "output": str(OUTPUT),
                "sha256": sha256(OUTPUT),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
