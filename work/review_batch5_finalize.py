import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parent.parent
source_path = root / "work/translation/tm_v2/batches/source/batch_0005.jsonl"
draft_path = root / "work/translation/drafts/batch_0005.jsonl"
reviewed_path = root / "work/translation/reviewed/batch_0005.jsonl"
validation_path = root / "work/translation/validation/batch_0005_reviewed.json"
changes_path = root / "work/translation/reviews/batch_0005_changes.json"
fit_path = root / "work/translation/validation/batch_0005_fit_only.json"
report_path = root / "work/translation/reviews/batch_0005_review.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


source_rows = read_jsonl(source_path)
draft_rows = read_jsonl(draft_path)
reviewed_rows = read_jsonl(reviewed_path)
validation = json.loads(validation_path.read_text(encoding="utf-8"))
changes = json.loads(changes_path.read_text(encoding="utf-8"))
fit = json.loads(fit_path.read_text(encoding="utf-8"))

assert len(source_rows) == len(draft_rows) == len(reviewed_rows) == 200
assert [row["tm_id"] for row in source_rows] == [row["tm_id"] for row in reviewed_rows]
assert all(src["source_text"] == rev["source_text"] for src, rev in zip(source_rows, reviewed_rows))
assert validation["error_count"] == 0 and validation["valid"] is True
assert fit["fixed_overflow_count"] == 0
assert fit["encoding_error_count"] == 0
assert fit["global_encoding_error_count"] == 0

suspicious_prefix_ids = [
    "ARF-TM-2986D8B401D04351C299",
    "ARF-TM-2B989385931925687400",
    "ARF-TM-2CA673A3AC438AEDC3C8",
    "ARF-TM-2D58FB2F2F74257CD00E",
    "ARF-TM-2E1A9634D60A48117846",
    "ARF-TM-3023F15EFFDAC5989442",
    "ARF-TM-3126A9FFF4ABDD2906EC",
]
unmatched_ids = [item["tm_id"] for item in fit["unmatched_system_units"]]
dummy_or_developer_ids = [
    "ARF-TM-26EF3F47C15CB1F8F34E",
    "ARF-TM-293E48FAFF8F8281CC6A",
    "ARF-TM-2A48D007F9BE1F84F16D",
    "ARF-TM-2A5244AEDB5A256B5C31",
    "ARF-TM-2B9C228CADC7D1B35307",
    "ARF-TM-2BB6DEB13D3D48A5D4AD",
    "ARF-TM-2C3D48E4C9B071E648FC",
    "ARF-TM-2F05C3EAF58513DE9A27",
    "ARF-TM-301F2CA758C542295E78",
    "ARF-TM-3084E6892E8C01209F16",
    "ARF-TM-3190BAD8A88A1D645A1D",
]

report = {
    "schema": "arf-translation-independent-review-v1",
    "batch_id": "batch_0005",
    "draft_author": "/root/translate_batch_0005",
    "reviewer": "/root/review_batch_0005",
    "independent_review": True,
    "translation_engine_policy": "Codex internal models only",
    "external_translation_services_used": [],
    "source": "work/translation/tm_v2/batches/source/batch_0005.jsonl",
    "draft": "work/translation/drafts/batch_0005.jsonl",
    "reviewed_output": "work/translation/reviewed/batch_0005.jsonl",
    "validation_report": "work/translation/validation/batch_0005_reviewed.json",
    "fit_report": "work/translation/validation/batch_0005_fit_only.json",
    "reviewed_units": 200,
    "modified_units": len(changes["modifications"]),
    "unchanged_units": 200 - len(changes["modifications"]),
    "review_dimensions": [
        "meaning_omission_addition",
        "proper_nouns_and_glossary",
        "system_function_accuracy",
        "linked_term_particles_and_spacing",
        "natural_korean",
        "dummy_and_developer_strings",
        "control_tokens",
        "line_breaks",
        "source_structure_prefixes",
        "codepage_corruption",
        "fixed_field_capacity",
        "canonical_codebook_encoding",
    ],
    "modifications": changes["modifications"],
    "residual_issues": [
        {
            "tm_id": "ARF-TM-2A3C4940C525EC9DAF66",
            "severity": "source_structure_marker",
            "issue": "<$0F> 뒤의 紅은 도움말 명령 매개변수로 보이므로 원문 그대로 보존했다. help.bin 구조 인젝터가 <$0F>와 후속 2바이트를 한 명령으로 처리하는지 확인해야 한다.",
        },
        {
            "tm_id": "ARF-TM-312E68C0778E492B0128",
            "severity": "source_structure_marker",
            "issue": "<$0F> 뒤의 座는 자연어가 아닌 도움말 명령 매개변수로 보이므로 원문 그대로 보존했다. 이 때문에 일본어 잔존 경고가 의도적으로 남는다.",
        },
        {
            "tm_id": "ARF-TM-310B902FAED0ACC6A29C",
            "severity": "source_catalog_split_boundary",
            "issue": "직전 스캔 문자열이 ‘…向かうた’에서 끝나고 본 문자열이 ‘め、…’로 시작해 원문의 ‘ため’가 NUL 스캐너 경계에서 갈라졌다. 번역은 ‘위해,’로 복원했지만 실제 todo.dat 필드 결합 규칙을 확인한 뒤 인젝션해야 한다.",
        },
        {
            "tm_ids": suspicious_prefix_ids,
            "severity": "suspected_inline_structure_prefix",
            "issue": "선두의 ', 7, C, ?, A, @0, $는 채팅/도움말 구조 표식 가능성이 있어 제거하거나 번역하지 않고 그대로 보존했다. 구조화된 레코드 경계 감사 전에는 자연어 일부로 확정하지 않는다.",
        },
        {
            "tm_ids": dummy_or_developer_ids,
            "severity": "visibility_unconfirmed",
            "issue": "더미·테스트·※컷·※이식·미정 문자열은 의미를 검수했지만 플레이어 노출 여부가 확정되지 않았다. 런타임 노출 감사 전까지 본문 공개 범위와 분리한다.",
        },
        {
            "tm_ids": unmatched_ids,
            "severity": "structured_table_boundary_audit_required",
            "issue": "200개 중 28개는 구조화된 테이블 카탈로그와 정확히 일치하지 않았다. 제어 헤더·선두 표식·NUL 스캔 경계가 주원인으로 보이며 별칭/경계 매핑 없이 자동 삽입하지 않는다.",
        },
    ],
    "validation": {
        "expected_units": 200,
        "actual_units": 200,
        "unique_tm_ids": len({row["tm_id"] for row in reviewed_rows}),
        "blank_translations": sum(not row["translation_ko"].strip() for row in reviewed_rows),
        "source_metadata_preserved": True,
        "control_tokens_preserved": True,
        "ids_and_order_preserved": True,
        "line_break_counts_preserved": all(
            src["source_text"].count("\n") == rev["translation_ko"].count("\n")
            for src, rev in zip(source_rows, reviewed_rows)
        ),
        "validator_error_count": validation["error_count"],
        "validator_warning_count": validation["warning_count"],
        "validator_warnings": validation["warnings"],
        "suspected_codepage_question_mark_corruption": any(
            item.get("code") == "suspected_codepage_question_mark_corruption"
            for item in validation["errors"] + validation["warnings"]
        ),
        "status": "passed",
    },
    "fit_validation": {
        "approved_units": fit["approved_tm_units"],
        "matched_unique_tm_units": fit["matched_unique_tm_units"],
        "matched_table_fields": fit["matched_table_fields"],
        "matched_fields_by_schema": fit["matched_fields_by_schema"],
        "fixed_overflow_count": fit["fixed_overflow_count"],
        "resizable_table_in_place_overflow_count": fit["resizable_table_in_place_overflow_count"],
        "resizable_overflows": fit["overflow_fields"],
        "unmatched_system_tm_count": fit["unmatched_system_tm_count"],
        "encoding_error_count": fit["encoding_error_count"],
        "global_encoding_error_count": fit["global_encoding_error_count"],
        "known_fixed_fields_fit": fit["known_fixed_fields_fit"],
        "codebook_note": "Append-only temporary extension of canonical_v1 was used only for this batch fit audit; the root merge must extend the canonical codebook after all reviewed batches are merged.",
    },
    "hashes": {
        "source_sha256": sha256(source_path),
        "draft_sha256": sha256(draft_path),
        "reviewed_sha256": sha256(reviewed_path),
        "validation_sha256": sha256(validation_path),
        "fit_report_sha256": sha256(fit_path),
    },
}

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"report": str(report_path), "modified_units": report["modified_units"], "hashes": report["hashes"]}, ensure_ascii=False))
