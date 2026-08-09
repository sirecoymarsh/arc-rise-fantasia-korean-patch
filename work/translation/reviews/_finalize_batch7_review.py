import hashlib
import json
import re
from pathlib import Path


ROOT = Path(".")
SOURCE = Path("work/translation/tm_v2/batches/source/batch_0007.jsonl")
DRAFT = Path("work/translation/drafts/batch_0007.jsonl")
REVIEWED = Path("work/translation/reviewed/batch_0007.jsonl")
CHANGES = Path("work/translation/reviews/batch_0007_changes.json")
VALIDATION = Path("work/translation/validation/batch_0007_reviewed.json")
FIT = Path("work/translation/validation/batch_0007_fit_only.json")
UNMATCHED = Path("work/translation/validation/batch_0007_unmatched_analysis.json")
OUTPUT = Path("work/translation/reviews/batch_0007_review.json")
CONTROL_RE = re.compile(r"<\$[0-9A-F]{2}>")


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


source = read_jsonl(SOURCE)
draft = read_jsonl(DRAFT)
reviewed = read_jsonl(REVIEWED)
changes = json.loads(CHANGES.read_text(encoding="utf-8"))
validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
fit = json.loads(FIT.read_text(encoding="utf-8"))
unmatched = json.loads(UNMATCHED.read_text(encoding="utf-8"))

assert len(source) == len(draft) == len(reviewed) == 200
source_ids = [item["tm_id"] for item in source]
assert source_ids == [item["tm_id"] for item in draft] == [item["tm_id"] for item in reviewed]
metadata_preserved = all(
    {key: value for key, value in src.items() if key != "translation_ko"}
    == {key: value for key, value in item.items() if key != "translation_ko"}
    for src, item in zip(source, reviewed)
)
control_preserved = all(
    CONTROL_RE.findall(src["source_text"]) == CONTROL_RE.findall(item["translation_ko"])
    for src, item in zip(source, reviewed)
)
line_breaks_preserved = all(
    src["source_text"].count("\n") == item["translation_ko"].count("\n")
    for src, item in zip(source, reviewed)
)
assert metadata_preserved and control_preserved and line_breaks_preserved
assert validation["valid"] and validation["error_count"] == 0
assert fit["fixed_overflow_count"] == 0
assert fit["encoding_error_count"] == 0 and fit["global_encoding_error_count"] == 0

unmatched_ids = [item["tm_id"] for item in unmatched["units"]]
visibility_unconfirmed = [
    "ARF-TM-3E7F2F225BF2EAB42D0E",
    "ARF-TM-3FB03D2EB0EAD97E9FD3",
    "ARF-TM-3FCAF94240D18D12624F",
    "ARF-TM-403B84CFA83BDAB9640B",
    "ARF-TM-40ABF2594104D168F90D",
    "ARF-TM-449829AB0C86B28D1BED",
    "ARF-TM-44D2C8C67AD659357838",
    "ARF-TM-44DEC58083FAFCCB9114",
    "ARF-TM-45FD51BF4FAC736D6F03",
    "ARF-TM-462C6A462435A7107C9B",
    "ARF-TM-46307962C0CC6078669C",
    "ARF-TM-4668A1AB5FBD6DFEEABE",
    "ARF-TM-46B9B3C51EBD70DB7723",
    "ARF-TM-497390D5F2799A13E790",
    "ARF-TM-4A002634298ADEEC34E7",
    "ARF-TM-4B800E153A9A3A8E116C",
]

report = {
    "schema": "arf-translation-independent-review-v1",
    "batch_id": "batch_0007",
    "draft_author": "/root/translate_batch_0007",
    "reviewer": "/root/review_batch_0007",
    "independent_review": True,
    "translation_engine_policy": "Codex internal models only",
    "external_translation_services_used": [],
    "source": SOURCE.as_posix(),
    "draft": DRAFT.as_posix(),
    "reviewed_output": REVIEWED.as_posix(),
    "validation_report": VALIDATION.as_posix(),
    "fit_report": FIT.as_posix(),
    "unmatched_analysis": UNMATCHED.as_posix(),
    "reviewed_units": 200,
    "modified_units": changes["modified_units"],
    "unchanged_units": 200 - changes["modified_units"],
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
            "tm_ids": unmatched_ids,
            "severity": "structured_table_boundary_audit_required",
            "issue": (
                "29개는 NUL 스캐너가 도움말·채팅·메뉴 필드의 선두 구조 바이트를 포함하거나 첫 글자를 잃어 "
                "구조화 테이블과 정확히 일치하지 않는다. 로컬 카탈로그 대조에서 27개는 단일 부분문자열 후보, "
                "2개는 복수 후보를 찾았고 무후보는 0개다. ARF-TM-3F5CF01DF2981D97DA7A는 clean field "
                "‘光召術師範’을 근거로 번역 의미를 ‘광소술 사범’으로 복원했지만, 전체 29개 모두 별칭/경계 "
                "매핑 승인 전에는 자동 삽입하지 않는다. 나머지 구조 접두부는 보수적으로 보존했다."
            ),
        },
        {
            "tm_id": "ARF-TM-42D5F542D1C35A12A8CB",
            "severity": "resizable_quest_pool",
            "issue": (
                "퀘스트 의뢰인 ‘고양이 마니아’는 기존 11바이트 슬롯에 NUL 포함 14바이트가 필요하지만 "
                "quest.bin 가변 문자열 풀 재구축 대상이다. 고정 필드 오버플로로 집계되지 않으며 재빌드 단계에서 처리한다."
            ),
        },
        {
            "tm_ids": visibility_unconfirmed,
            "severity": "visibility_unconfirmed",
            "issue": (
                "명시적 더미·퀘스트 더미·※컷 개발 문자열은 의미와 구조를 검수했지만 플레이어 노출 여부는 "
                "확정되지 않았다. 런타임 노출 감사 전까지 일반 공개 텍스트와 분리한다."
            ),
        },
    ],
    "validation": {
        "expected_units": 200,
        "actual_units": len(reviewed),
        "unique_tm_ids": len(set(source_ids)),
        "blank_translations": sum(not str(item.get("translation_ko") or "").strip() for item in reviewed),
        "source_metadata_preserved": metadata_preserved,
        "control_tokens_preserved": control_preserved,
        "ids_and_order_preserved": True,
        "line_break_counts_preserved": line_breaks_preserved,
        "validator_error_count": validation["error_count"],
        "validator_warning_count": validation["warning_count"],
        "validator_warnings": validation["warnings"],
        "suspected_codepage_question_mark_corruption": False,
        "status": "passed",
    },
    "fit_validation": {
        "approved_units": fit["approved_tm_units"],
        "matched_unique_tm_units": fit["matched_unique_tm_units"],
        "matched_table_fields": fit["matched_table_fields"],
        "matched_fields_by_schema": fit["matched_fields_by_schema"],
        "fixed_overflow_count": fit["fixed_overflow_count"],
        "resizable_table_in_place_overflow_count": fit["resizable_table_in_place_overflow_count"],
        "resizable_overflows": [item for item in fit["overflow_fields"] if item.get("table_resizable")],
        "unmatched_system_tm_count": fit["unmatched_system_tm_count"],
        "encoding_error_count": fit["encoding_error_count"],
        "global_encoding_error_count": fit["global_encoding_error_count"],
        "known_fixed_fields_fit": fit["known_fixed_fields_fit"],
        "codebook_note": (
            "canonical_v1을 --existing으로 사용한 append-only 임시 코드북으로 본 배치만 감사했다. "
            "루트 병합 단계에서 최종 승인 코퍼스로 정식 코드북을 다시 확장해야 한다."
        ),
    },
    "boundary_audit_application": {
        "status": "not_yet_applied_for_batch_0007",
        "existing_audit_source": "work/translation/boundary_audit/batches_0001_0002.json",
        "matched_units_from_existing_audit": fit.get("boundary_audit_tm_units_matched", 0),
        "batch_0007_unmatched_units": unmatched["input_unmatched_count"],
        "single_candidate_units": unmatched["with_single_substring_candidate"],
        "multiple_candidate_units": unmatched["with_multiple_substring_candidates"],
        "no_candidate_units": unmatched["with_no_substring_candidate"],
    },
    "hashes": {
        "source_sha256": sha256(SOURCE),
        "draft_sha256": sha256(DRAFT),
        "reviewed_sha256": sha256(REVIEWED),
        "validation_sha256": sha256(VALIDATION),
        "fit_report_sha256": sha256(FIT),
        "unmatched_analysis_sha256": sha256(UNMATCHED),
        "temporary_codebook_sha256": sha256(Path("work/translation/validation/batch_0007_codebook_temp.json")),
    },
}

OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    json.dumps(
        {
            "reviewed_units": report["reviewed_units"],
            "modified_units": report["modified_units"],
            "validator_errors": report["validation"]["validator_error_count"],
            "fixed_overflows": report["fit_validation"]["fixed_overflow_count"],
            "encoding_errors": report["fit_validation"]["encoding_error_count"],
            "reviewed_sha256": report["hashes"]["reviewed_sha256"],
        },
        ensure_ascii=False,
    )
)
