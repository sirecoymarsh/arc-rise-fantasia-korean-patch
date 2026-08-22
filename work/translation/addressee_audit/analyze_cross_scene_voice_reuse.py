#!/usr/bin/env python3
"""Find fixed Korean voice/register reused across different speakers or scenes.

Read-only candidate generator.  Semantic verdicts and corrections are authored
by the active Codex model after scene review.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(r"P:\AI\Codex\projects\ArcRiseFantasia-Korean")
AUDIT = ROOT / "work/translation/addressee_audit"
CORPUS = AUDIT / "scene_register_corpus.json"
TM = ROOT / "work/translation/final/translation_memory_draft.json"
OUT = AUDIT / "cross_scene_voice_reuse_candidates.json"
MD = AUDIT / "cross_scene_voice_reuse_candidates.md"

VOICE_RE = re.compile(
    r"(?:당신|너희|너는|너를|너에게|너한테|너도|너와|너랑|넌|널|네가|네게|"
    r"자네|그대|네놈|형님|슴다|임다|전하|폐하|님|씨)"
)
NICOL_RE = re.compile(r"(?:슴다|임다|검다|함다|아님다|형님)")


def main() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    tm = json.loads(TM.read_text(encoding="utf-8"))
    tm_by_id = {str(row["tm_id"]): row for row in tm["units"]}
    occ: dict[str, list[dict]] = defaultdict(list)
    for scene in corpus["scenes"]:
        for row in scene["utterances"]:
            tm_id = row.get("tm_id")
            if not tm_id:
                continue
            occ[str(tm_id)].append(
                {
                    "locator": scene["locator"],
                    "line_index": row["line_index"],
                    "speaker_slot": row["speaker_slot"],
                    "source_text": row["source_text"],
                    "translation_ko": row["translation_ko"],
                }
            )

    candidates: list[dict] = []
    for tm_id, rows in occ.items():
        unit = tm_by_id[tm_id]
        ko = str(unit.get("translation_ko") or "")
        if not VOICE_RE.search(ko):
            continue
        slots = sorted({row["speaker_slot"] for row in rows})
        locators = sorted({row["locator"] for row in rows})
        reasons = []
        if len(slots) > 1:
            reasons.append("same_fixed_translation_used_by_multiple_speaker_slots")
        if len(locators) > 1 and re.search(r"당신|너희|너는|너를|너에게|너한테|너도|너와|너랑|넌|널|네가|네게|자네|그대|네놈", ko):
            reasons.append("fixed_second_person_reused_across_scenes")
        if NICOL_RE.search(ko) and any(slot != "08" for slot in slots):
            reasons.append("nicol_voice_marker_used_outside_slot_08")
        if not reasons:
            continue
        candidates.append(
            {
                "tm_id": tm_id,
                "source_text": unit["source_text"],
                "translation_ko": ko,
                "speaker_slots": slots,
                "scene_count": len(locators),
                "occurrence_count_in_corpus": len(rows),
                "reasons": reasons,
                "evidence": rows[:20],
            }
        )
    candidates.sort(
        key=lambda row: (
            0 if "nicol_voice_marker_used_outside_slot_08" in row["reasons"] else 1,
            0 if len(row["speaker_slots"]) > 1 else 1,
            -row["scene_count"],
            row["tm_id"],
        )
    )
    report = {
        "schema": "arf-ko-cross-scene-voice-reuse-audit-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "purpose": "Read-only candidates for scene-independent fixed voice/register reuse.",
        "counts": {
            "candidate_tm_ids": len(candidates),
            "multiple_speaker_slots": sum(len(row["speaker_slots"]) > 1 for row in candidates),
            "fixed_second_person_across_scenes": sum(
                "fixed_second_person_reused_across_scenes" in row["reasons"] for row in candidates
            ),
            "nicol_marker_outside_slot_08": sum(
                "nicol_voice_marker_used_outside_slot_08" in row["reasons"] for row in candidates
            ),
        },
        "candidates": candidates,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 장면 독립 말투 재사용 후보",
        "",
        "동일 TM 번역이 다른 화자 슬롯 또는 여러 장면에 고정 재사용된 곳을 찾는 읽기 전용 후보표다.",
        "후보는 자동 오역 판정이 아니며 장면별 Codex 검수가 필요하다.",
        "",
        f"- 후보 TM: {len(candidates)}",
        f"- 복수 화자 슬롯: {report['counts']['multiple_speaker_slots']}",
        f"- 복수 장면 고정 2인칭: {report['counts']['fixed_second_person_across_scenes']}",
        f"- 니콜 말투 표지의 타 슬롯 사용: {report['counts']['nicol_marker_outside_slot_08']}",
        "",
    ]
    for row in candidates:
        lines.extend(
            [
                f"## `{row['tm_id']}`",
                "",
                f"- slots: `{', '.join(row['speaker_slots'])}` / scenes: {row['scene_count']}",
                f"- reasons: `{', '.join(row['reasons'])}`",
                f"- JP: `{str(row['source_text']).replace(chr(10), ' / ')}`",
                f"- KO: `{str(row['translation_ko']).replace(chr(10), ' / ')}`",
                "",
            ]
        )
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
