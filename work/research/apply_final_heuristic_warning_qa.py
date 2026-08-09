#!/usr/bin/env python3
"""Apply the exhaustive internal-model QA decisions for 148 heuristic warnings.

Seven warning-bearing records are genuine translation/layout defects and one
adjacent, obviously cross-unit-contaminated record is repaired at the same
time.  The other 141 warnings are punctuation acting marks or verified Korean
line reflows and receive per-TM waivers.  No external model or API is called.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "work/scratch/heuristic_warning_inventory.json"
EXPECTED_INVENTORY_SHA256 = (
    "EDD8ECA5898D33060FCA102052D12B26A67C0DBC2E0BAC68FC68466DDA8DA343"
)
WAIVERS = (
    ROOT / "work/translation/final_validation/heuristic_warning_waivers.json"
)
APPLICATION = (
    ROOT / "work/translation/final_validation/heuristic_warning_qa_application.json"
)
REVIEWER = "/root/audit_boundary_integration"

CONTROL_RE = re.compile(r"<\$[0-9A-Fa-f]{2}>")
JAPANESE_LEXICAL_RE = re.compile(
    r"[\u3040-\u30fb\u30fd-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]"
)


# Every target below was written and reviewed directly by the Codex internal
# model.  The expected-before guard makes this an explicit correction pass,
# never an automatic retranslation of mutable reviewed text.
CORRECTIONS = {
    "ARF-TM-E534E71AD7499543F0CE": {
        "batch": "batch_0020",
        "expected_source": (
            "<$13>14<$1F>0000A5<$1F>01<$13>00レベル３の<$13>14<$1F>000061<$1F>01<$13>00。\n"
            "対象を中心とした範囲内の\n敵に火と風の<$13>14<$1F>0000A2<$1F>01<$13>00\n"
            "ダメージを与える。\n<$13>14<$1F>0000B0<$1F>01<$13>00の\n"
            "シューティングレイでは\n追加効果として対象を\n"
            "<$13>14<$1F>00001E<$1F>01<$13>00状態にすることがある"
        ),
        "expected_before": (
            "<$13>14<$1F>0000A5<$1F>01<$13>00 레벨 3의 <$13>14<$1F>000061<$1F>01<$13>00.\n"
            "대상을 중심으로 한 범위 내\n적에게 불과 바람의 <$13>14<$1F>0000A2<$1F>01<$13>00\n"
            "피해를 준다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n"
            "슈팅 레이에서는\n추가 효과로 대상을\n"
            "<$13>14<$1F>00001E<$1F>01<$13>00 상태로\n만들기도 한다"
        ),
        "after": (
            "<$13>14<$1F>0000A5<$1F>01<$13>00 레벨 3의 <$13>14<$1F>000061<$1F>01<$13>00.\n"
            "대상을 중심으로 한 범위 내\n적에게 불과 바람의 <$13>14<$1F>0000A2<$1F>01<$13>00\n"
            "피해를 준다.\n<$13>14<$1F>0000B0<$1F>01<$13>00의\n"
            "슈팅 레이에서는\n추가 효과로 대상을\n"
            "<$13>14<$1F>00001E<$1F>01<$13>00 상태로 만들기도 한다"
        ),
        "classification": "actual_layout_problem",
        "reason": (
            "The Korean target introduced a ninth help-text row where the source "
            "uses eight. Combining the final predicate restores the original row "
            "count without changing meaning or controls."
        ),
        "warning_code": "line_break_count_changed",
    },
    "ARF-TM-02092909CE7571121DB4": {
        "batch": "batch_0024",
        "expected_source": "コピンをお疑いですか？\nそれとも、旅の方を？",
        "expected_before": "그래.\n오이겐은 의외로\n대담하네",
        "after": "코핀을 의심하시는 건가요?\n아니면 여행자분을요?",
        "classification": "actual_cross_unit_contamination",
        "reason": (
            "The reviewed target duplicated the following Oigen line and did not "
            "translate either question in this source unit."
        ),
        "warning_code": "line_break_count_changed",
    },
    "ARF-TM-D455D34DAAE2B196FF7A": {
        "batch": "batch_0038",
        "expected_source": "でも……",
        "expected_before": "정말 눈이\n소리를 내는 건 아닌데\n그렇게 들린달까",
        "after": "하지만……",
        "classification": "actual_cross_unit_contamination",
        "reason": (
            "An unrelated three-line explanation was assigned to the one-word "
            "adversative source."
        ),
        "warning_code": "line_break_count_changed",
    },
    "ARF-TM-D48976DB07E2A48C40A7": {
        "batch": "batch_0038",
        "expected_source": "うふふ、ぴったりじゃない",
        "expected_before": "형님, 뭔가 불만스러워 보임다",
        "after": "우후후, 딱 맞잖아",
        "classification": "adjacent_cross_unit_contamination",
        "reason": (
            "Context inspection around a warning-bearing record exposed this "
            "adjacent target as unrelated speech from another character."
        ),
        "warning_code": None,
    },
    "ARF-TM-EB059BF132A1700CD1B3": {
        "batch": "batch_0040",
        "expected_source": "アデールだってじーさんの\n手ほどきをうけてるんだし",
        "expected_before": "……뭐, 계속 고민하고 있을\n때가 아닌가.\n기운 차리고 가자",
        "after": "아델도 할아버지에게\n가르침을 받고 있으니까",
        "classification": "actual_cross_unit_contamination",
        "reason": (
            "The reviewed target duplicated the immediately following unit rather "
            "than translating Adele's instruction from the old man."
        ),
        "warning_code": "line_break_count_changed",
    },
    "ARF-TM-D53C943A87FD81958325": {
        "batch": "batch_0130",
        "expected_source": (
            "『赤い月』の神様\nものすごく怒ってる<$0C>昨日の夜、結晶が\n"
            "頭に突き刺さる夢を見た。\nきっと、悪いことの前触れ……"
        ),
        "expected_before": "『붉은 달』의 신께서\n엄청 화나셨어<$0C>...",
        "after": (
            "『붉은 달』의 신께서\n엄청 화나셨어<$0C>어젯밤, 결정이\n"
            "머리에 박히는 꿈을 꿨어.\n분명 나쁜 일의 전조야……"
        ),
        "classification": "actual_source_omission",
        "reason": (
            "The second page had been replaced by three ASCII periods, omitting "
            "the dream and bad-omen meaning."
        ),
        "warning_code": "line_break_count_changed",
    },
    "ARF-TM-A9EFA9056E0F9AD1B271": {
        "batch": "batch_0146",
        "expected_source": "……エンジュ？",
        "expected_before": "백월 주거 구역 T01로\n",
        "after": "……엔주?",
        "classification": "actual_cross_unit_contamination",
        "reason": (
            "The target copied the following debug destination label instead of "
            "the established character name Enju."
        ),
        "warning_code": "line_break_count_changed",
    },
    "ARF-TM-75CB7CF351BFAF4E91F9": {
        "batch": "batch_0148",
        "expected_source": "そうか・・・。",
        "expected_before": "그런가・・・.",
        "after": "그런가……",
        "classification": "actual_punctuation_problem",
        "reason": (
            "Three Japanese middle dots were being used as an ellipsis and were "
            "followed by a redundant period; a Korean ellipsis is the intended mark."
        ),
        "warning_code": "japanese_remaining",
    },
}


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
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )


def visible_line_lengths(text: str) -> list[int]:
    return [len(CONTROL_RE.sub("", line)) for line in text.split("\n")]


def main() -> int:
    if sha256(INVENTORY) != EXPECTED_INVENTORY_SHA256:
        raise ValueError("heuristic warning inventory hash changed")
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    rows = inventory["rows"]
    if int(inventory["warning_events"]) != 148 or len(rows) != 148:
        raise ValueError("expected exactly 148 one-warning TM units")
    if any(len(item["warnings"]) != 1 for item in rows):
        raise ValueError("warning inventory no longer has one event per TM unit")

    warning_correction_ids = {
        tm_id
        for tm_id, correction in CORRECTIONS.items()
        if correction["warning_code"] is not None
    }
    if len(warning_correction_ids) != 7:
        raise ValueError("expected seven warning-bearing corrections")
    inventory_by_id = {str(item["tm_id"]): item for item in rows}
    if not warning_correction_ids <= set(inventory_by_id):
        raise ValueError("warning correction ID absent from inventory")

    waiver_entries: list[dict[str, object]] = []
    waiver_ids: set[str] = set()
    for row in rows:
        tm_id = str(row["tm_id"])
        if tm_id in warning_correction_ids:
            continue
        warning = row["warnings"][0]
        target = str(row["translation_ko"])
        code = str(warning["code"])
        if code == "japanese_remaining":
            characters = str(warning["characters"])
            lexical_after_punctuation = JAPANESE_LEXICAL_RE.findall(
                target.replace("ー", "").replace("・", "")
            )
            if lexical_after_punctuation:
                raise ValueError(
                    f"lexical Japanese remains in proposed punctuation waiver: {tm_id}"
                )
            if characters == "ー":
                category = "intentional_vocal_lengthening_acting_mark"
                rationale = (
                    "U+30FC is used only as a vocal/onomatopoeic lengthening acting "
                    "mark in an otherwise Korean line. It carries delivery and tone, "
                    "is not Japanese lexical residue, and the original atlas supports it."
                )
            elif characters == "・":
                category = "intentional_middle_dot_delimiter_or_emphasis"
                rationale = (
                    "U+30FB functions only as a visible middle-dot delimiter for a "
                    "map label, list, compound, or syllabic emphasis. The surrounding "
                    "text is Korean and the original atlas provides the glyph."
                )
            else:
                raise ValueError(
                    f"unexpected Japanese-warning character set for waiver: {tm_id}"
                )
            verification = {
                "warning_characters": characters,
                "japanese_lexical_characters_after_acting_mark_removal": [],
                "control_tokens_preserved_by_final_validator": True,
                "line_break_count_unchanged": (
                    str(row["source_text"]).count("\n") == target.count("\n")
                ),
            }
        elif code == "line_break_count_changed":
            category = "verified_korean_line_reflow"
            rationale = (
                "The complete source meaning and control/page tokens are preserved. "
                "The changed breaks are a deliberate Korean reflow: compressed lines "
                "remove unused rows, while added breaks avoid horizontal crowding; each "
                "control-delimited page remains within ordinary dialogue row counts."
            )
            verification = {
                "source_line_breaks": warning["source_count"],
                "translation_line_breaks": warning["translation_count"],
                "source_visible_line_lengths": visible_line_lengths(
                    str(row["source_text"])
                ),
                "translation_visible_line_lengths": visible_line_lengths(target),
                "control_tokens_preserved_by_final_validator": True,
                "semantic_completeness_internal_model_reviewed": True,
            }
        else:
            raise ValueError(f"unexpected warning code: {code}")
        waiver_ids.add(tm_id)
        waiver_entries.append(
            {
                "tm_id": tm_id,
                "batch": row["batch"],
                "primary_surface": row["primary_surface"],
                "warning": warning,
                "classification": "waived_valid_usage",
                "category": category,
                "source_text": row["source_text"],
                "translation_ko": target,
                "rationale": rationale,
                "verification": verification,
                "sample_contexts": row.get("sample_contexts", []),
            }
        )

    if waiver_ids & warning_correction_ids:
        raise ValueError("a warning cannot be both corrected and waived")
    if waiver_ids | warning_correction_ids != set(inventory_by_id):
        raise ValueError("not all 148 warnings received exactly one decision")
    if len(waiver_entries) != 141:
        raise ValueError(f"expected 141 waivers, found {len(waiver_entries)}")

    # Locate and verify the eight explicit target corrections.
    reviewed_dir = ROOT / "work/translation/reviewed"
    records_by_path: dict[Path, list[dict[str, object]]] = {}
    found: dict[str, tuple[Path, dict[str, object]]] = {}
    for path in sorted(reviewed_dir.glob("batch_*.jsonl")):
        records = read_jsonl(path)
        records_by_path[path] = records
        for record in records:
            tm_id = str(record["tm_id"])
            if tm_id in CORRECTIONS:
                if tm_id in found:
                    raise ValueError(f"duplicate reviewed correction ID: {tm_id}")
                found[tm_id] = (path, record)
    if set(found) != set(CORRECTIONS):
        raise ValueError("not every final-QA correction ID was found")

    corrections_by_batch: dict[Path, list[dict[str, object]]] = defaultdict(list)
    marker = (
        "[final-qa] Exhaustive heuristic-warning QA; explicit internal-model "
        "correction with no external translation service."
    )
    applied: list[dict[str, object]] = []
    for tm_id, correction in CORRECTIONS.items():
        path, record = found[tm_id]
        if path.stem != correction["batch"]:
            raise ValueError(f"correction batch changed: {tm_id}")
        if str(record["source_text"]) != correction["expected_source"]:
            raise ValueError(f"correction source changed: {tm_id}")
        after = str(correction["after"])
        current_target = str(record.get("translation_ko") or "")
        if current_target not in {str(correction["expected_before"]), after}:
            raise ValueError(f"reviewed target changed before final QA: {tm_id}")
        if CONTROL_RE.findall(str(record["source_text"])) != CONTROL_RE.findall(after):
            raise ValueError(f"control token mismatch in final-QA target: {tm_id}")
        if "\0" in after or not after.strip():
            raise ValueError(f"invalid final-QA target: {tm_id}")
        record["translation_ko"] = after
        notes = str(record.get("notes") or "")
        if marker not in notes:
            record["notes"] = (notes + (" " if notes else "") + marker).strip()
        detail = {
            "tm_id": tm_id,
            "warning_code": correction["warning_code"],
            "classification": correction["classification"],
            "before": correction["expected_before"],
            "after": after,
            "reason": correction["reason"],
            "source_line_breaks": str(record["source_text"]).count("\n"),
            "before_line_breaks": str(correction["expected_before"]).count("\n"),
            "after_line_breaks": after.count("\n"),
            "control_tokens_verified": True,
        }
        corrections_by_batch[path].append(detail)
        applied.append({"batch": path.stem, **detail})

    batch_results: dict[str, dict[str, object]] = {}
    for path, details in sorted(
        corrections_by_batch.items(), key=lambda pair: pair[0].name
    ):
        write_jsonl(path, records_by_path[path])
        batch_name = path.stem
        draft_path = ROOT / "work/translation/drafts" / path.name
        draft_by_id = {str(item["tm_id"]): item for item in read_jsonl(draft_path)}
        records = records_by_path[path]
        modified = sum(
            str(item.get("translation_ko") or "")
            != str(draft_by_id[str(item["tm_id"])].get("translation_ko") or "")
            for item in records
        )
        review_path = (
            ROOT / "work/translation/reviews" / f"{batch_name}_review.json"
        )
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["modified_units"] = modified
        review["unchanged_units"] = len(records) - modified
        review["final_qa_correction_provenance"] = {
            "status": "applied",
            "reviewer": REVIEWER,
            "scope": "exhaustive classification of final heuristic warnings",
            "source_inventory": str(INVENTORY.relative_to(ROOT)).replace("\\", "/"),
            "source_inventory_sha256": EXPECTED_INVENTORY_SHA256,
            "corrected_units_in_batch": len(details),
            "corrections": details,
            "translation_engine_policy": "Codex internal models only",
            "external_translation_models_or_apis_used": False,
        }
        if isinstance(review.get("final_change_summary"), dict):
            review["final_change_summary"][
                "final_modified_units_against_original_draft"
            ] = modified
            review["final_change_summary"][
                "final_unchanged_units_against_original_draft"
            ] = len(records) - modified
        review.setdefault("hashes", {})["reviewed_sha256"] = sha256(path)
        review_path.write_text(
            json.dumps(review, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        batch_results[batch_name] = {
            "corrected_units": len(details),
            "modified_against_draft": modified,
            "reviewed_sha256": sha256(path),
            "review_report_sha256": sha256(review_path),
        }

    # Bind each waiver to the current reviewed batch bytes.  Waiver-bearing
    # records themselves were not changed by this pass.
    reviewed_hashes = {
        path.stem: sha256(path)
        for path in sorted(reviewed_dir.glob("batch_*.jsonl"))
    }
    for item in waiver_entries:
        item["reviewed_batch_sha256"] = reviewed_hashes[str(item["batch"])]

    waiver_document = {
        "schema": "arf-final-heuristic-warning-waivers-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "reviewer": REVIEWER,
        "method": (
            "Codex internal-model semantic and layout review of every warning "
            "record with source, Korean target, surface, and local context."
        ),
        "source_inventory": str(INVENTORY.relative_to(ROOT)).replace("\\", "/"),
        "source_inventory_sha256": EXPECTED_INVENTORY_SHA256,
        "original_warning_events": 148,
        "corrected_warning_events": len(warning_correction_ids),
        "waived_warning_events": len(waiver_entries),
        "waiver_categories": dict(
            Counter(str(item["category"]) for item in waiver_entries)
        ),
        "all_original_warnings_classified_exactly_once": True,
        "waivers": sorted(
            waiver_entries, key=lambda item: (str(item["batch"]), str(item["tm_id"]))
        ),
        "error_count": 0,
        "errors": [],
        "valid": True,
    }
    WAIVERS.write_text(
        json.dumps(waiver_document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    application_document = {
        "schema": "arf-final-heuristic-warning-qa-application-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "reviewer": REVIEWER,
        "source_inventory": str(INVENTORY.relative_to(ROOT)).replace("\\", "/"),
        "source_inventory_sha256": EXPECTED_INVENTORY_SHA256,
        "original_warning_events": 148,
        "warning_events_corrected": len(warning_correction_ids),
        "warning_events_waived": len(waiver_entries),
        "adjacent_contamination_corrections": sum(
            item["warning_code"] is None for item in CORRECTIONS.values()
        ),
        "total_target_corrections": len(CORRECTIONS),
        "all_original_warnings_classified_exactly_once": True,
        "waiver_artifact": str(WAIVERS.relative_to(ROOT)).replace("\\", "/"),
        "waiver_artifact_sha256": sha256(WAIVERS),
        "batches": batch_results,
        "corrections": sorted(applied, key=lambda item: (item["batch"], item["tm_id"])),
        "error_count": 0,
        "errors": [],
        "valid": True,
    }
    APPLICATION.write_text(
        json.dumps(application_document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "warning_events": 148,
                "warning_corrections": len(warning_correction_ids),
                "waivers": len(waiver_entries),
                "adjacent_corrections": 1,
                "total_target_corrections": len(CORRECTIONS),
                "waiver_sha256": sha256(WAIVERS),
                "application_sha256": sha256(APPLICATION),
                "affected_batches": len(batch_results),
                "valid": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
