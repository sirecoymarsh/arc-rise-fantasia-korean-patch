# -*- coding: utf-8 -*-
"""Build the independent-review provenance report for translation batch 0006."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from apply_batch_0006_review import CHANGES


SOURCE = Path("work/translation/tm_v2/batches/source/batch_0006.jsonl")
DRAFT = Path("work/translation/drafts/batch_0006.jsonl")
REVIEWED = Path("work/translation/reviewed/batch_0006.jsonl")
VALIDATION = Path("work/translation/validation/batch_0006_reviewed.json")
FIT = Path("work/translation/validation/batch_0006_fit_only.json")
TEMP_CODEBOOK = Path("work/translation/validation/batch_0006_codebook_temp.json")
CANONICAL_CODEBOOK = Path("work/font/canonical_v1/codebook.json")
REPORT = Path("work/translation/reviews/batch_0006_review.json")


CHANGE_META = {
    "ARF-TM-325FAEE50CA3F412DE0A": (
        "meaning_naturalness",
        "「背後を突く」를 직역한 ‘배후를 찌르다’ 대신 시야 밖에서 뒤를 노린다는 전투 의미가 자연스럽게 드러나도록 고쳤다.",
    ),
    "ARF-TM-32D1CA3C8220D71A23BF": (
        "glossary_terminology",
        "능력치 감소 용어를 고정안인 ‘하락’으로 통일했다.",
    ),
    "ARF-TM-334214F2C356E9118021": (
        "system_probability_naturalness",
        "확률성 추가 효과의 「することがある」를 시스템 문장 ‘만들기도 한다’로 다듬었다.",
    ),
    "ARF-TM-3343DCA46796947A85D0": (
        "mechanics_nuance",
        "원문의 ‘석화를 막으려 작용한다’는 성격을 복원해 확률 방지를 절대 면역처럼 단정하지 않게 했다.",
    ),
    "ARF-TM-34518E656C2B9FC05389": (
        "system_terminology_fixed_field",
        "「発動可能」를 ‘발동 가능’으로 맞추고 대상·회복량을 유지한 채 특수기 설명 고정 필드에 맞췄다.",
    ),
    "ARF-TM-345B5EC239691C153C04": (
        "terminology_fixed_field",
        "장비 설명의 보유자를 ‘소지자’로 통일하고, 애용·수호·광소술 무효 의미를 보존하면서 81바이트 필드에 맞췄다.",
    ),
    "ARF-TM-34B22DDAF70C38FD78BD": (
        "terminology_naturalness",
        "「有翼生物」를 앞선 독립 검수의 ‘날개 달린 생물’ 표기와 맞추고 어색한 ‘생물계에게’를 정리했다.",
    ),
    "ARF-TM-34F6BF9FCE2AE67F7EDC": (
        "meaning_grammar",
        "새 법이 사람으로 하여금 다른 사람을 잉여 존재로 여겨 배척하게 한다는 원문의 주어·서술 관계를 복원했다.",
    ),
    "ARF-TM-3521F2F9CB31DC6114DD": (
        "naturalness_fixed_field",
        "보기 드문 선명한 꽃과 발밑의 행운이라는 이미지를 자연스럽게 유지하면서 81바이트 설명 필드에 맞췄다.",
    ),
    "ARF-TM-364FDC37BCDF81E4FDE6": (
        "system_template",
        "MP 회복 아이템 계열의 확정 템플릿 ‘레벨 2 MP 완전 회복’으로 통일했다.",
    ),
    "ARF-TM-364AE0F702E20DEA38C0": (
        "fixed_field_capacity",
        "‘수수께끼의’ 의미를 ‘의문의’으로 간결하게 옮겨 이름 고정 필드의 NUL 포함 17바이트 한도에 맞췄다.",
    ),
    "ARF-TM-373C31B9539E2B8F6F57": (
        "system_probability_naturalness",
        "확률성 추가 효과의 표현을 ‘만들기도 한다’로 다듬었다.",
    ),
    "ARF-TM-375CFA3B661F431A2B6B": (
        "system_probability_naturalness",
        "확률성 추가 효과의 표현을 ‘만들기도 한다’로 다듬었다.",
    ),
    "ARF-TM-382B1220143304D3EC82": (
        "glossary_skill_name",
        "마법명 고정안 ‘선더볼트’의 붙여쓰기를 적용하고 선두 구조 문자 G는 보존했다.",
    ),
    "ARF-TM-386768A1EA571E36700C": (
        "terminology_naturalness",
        "「水棲生物」를 읽기 쉬운 ‘수생 생물’로 정리하고 어색한 계열 조사 표현을 바로잡았다.",
    ),
    "ARF-TM-386BB7193FF058B24CC1": (
        "meaning_accuracy",
        "「独自の色彩が強い文化」를 단순히 다채로운 문화로 넓히지 않고 ‘독자적인 색채가 짙은 문화’로 복원했다.",
    ),
    "ARF-TM-391A739C3A358546845C": (
        "quest_voice_naturalness",
        "의뢰인의 노년 말투와 새가 비정상적으로 불어났다는 상황을 자연스러운 한국어로 다듬었다.",
    ),
    "ARF-TM-3903C64837C93CD29802": (
        "meaning_fixed_field",
        "「勇者像」를 ‘용사상’, 「具現化」를 ‘본뜨다’로 압축해 의미를 선명하게 하고 81바이트 필드에 맞췄다.",
    ),
    "ARF-TM-39C1821CBF56DC7A890E": (
        "meaning_naturalness",
        "빠졌던 어두운 밤의 이미지를 ‘밤을 닮은 칠흑’으로 복원하고 장식 관계를 간결하게 정리했다.",
    ),
    "ARF-TM-3A13C08F93F275ACBE90": (
        "terminology_consistency",
        "관련 설명과 동일하게 「水棲生物」를 ‘수생 생물’로 통일했다.",
    ),
    "ARF-TM-3B2AC3F87D60F0DF4FAB": (
        "naturalness",
        "‘행운을 얻기 쉬워진다’보다 원문의 ‘행운이 찾아오다’ 뉘앙스가 자연스러운 표현으로 다듬었다.",
    ),
    "ARF-TM-3B2BC778DC7B5423DCB4": (
        "system_naturalness",
        "연계가 확률적으로 생길 수 있다는 문장을 ‘발생하기도 한다’로 자연스럽게 다듬었다.",
    ),
    "ARF-TM-3C0DBE3765380F4368E5": (
        "naturalness_fixed_field",
        "중복 조사를 덜어 내고 햇빛·유리·눈동자 이미지를 보존하면서 81바이트 필드에 맞췄다.",
    ),
    "ARF-TM-3B3830DC2BFD9A6358C6": (
        "system_template_grammar",
        "상태 변화 도움말의 ‘중 하나’와 타동 표현 ‘약화시키거나’를 앞선 검수 템플릿에 맞췄다.",
    ),
    "ARF-TM-3CD2B8EE90FA5A874CC0": (
        "system_template",
        "상태 이상 도움말의 반복 문구를 ‘중 하나’로 통일했다.",
    ),
    "ARF-TM-3D2C466FAD9E7AC84B2B": (
        "tense_naturalness",
        "원문의 현재적 의문을 과거형 ‘숨겼을까’가 아니라 ‘숨기고 있을까’로 바로잡았다.",
    ),
    "ARF-TM-3D5D563C549BB8B1DE7A": (
        "naturalness_fixed_field",
        "‘광소술 대항전’이라는 어색한 표현을 광소술전용 장비라는 의미가 자연스러운 문장으로 다듬었다.",
    ),
    "ARF-TM-3D69577BA80C3D0C12A7": (
        "glossary_terminology",
        "능력치 감소 용어를 고정안인 ‘하락’으로 통일했다.",
    ),
    "ARF-TM-3E29CFE95FD277A612E0": (
        "title_punctuation_consistency",
        "같은 채팅·퀘스트 제목군과 맞도록 원문의 물결표 〜를 유지했다.",
    ),
    "ARF-TM-3E3CEB48CC3D7E287709": (
        "religious_terminology_naturalness",
        "한국어에서 죄수와 혼동하기 쉬운 ‘교도’ 대신 오르키나교의 신도라는 관계를 분명히 했다.",
    ),
}


SUSPECTED_PREFIX_IDS = [
    "ARF-TM-32B4ABA5065E736DF5EA",
    "ARF-TM-33A83791915059E3109F",
    "ARF-TM-37E2DA258C93BF2E9719",
    "ARF-TM-3889642517F14710DAE2",
    "ARF-TM-38CEE3A4022B9F164D7B",
    "ARF-TM-3910AC5EAF5899F317CD",
    "ARF-TM-39940E80C9DE07F8CCC9",
    "ARF-TM-3C1CFE57F12E382BC107",
    "ARF-TM-3D15EBDE0CDB47D792C6",
    "ARF-TM-3E3DD991BE4FF31BB5E2",
]

SPLIT_BOUNDARY_IDS = [
    "ARF-TM-3A150DC3799C616082D6",
    "ARF-TM-3CFB213E3A0103861239",
]

VISIBILITY_UNCONFIRMED_IDS = [
    "ARF-TM-32DE70BACB3714C26837",
    "ARF-TM-32E76F1ABB1B04611F65",
    "ARF-TM-3307CAC2CBC00116E8B1",
    "ARF-TM-33A74C2E25B95348E3D1",
    "ARF-TM-3763C62816EC1EED56DA",
    "ARF-TM-37E2DA258C93BF2E9719",
    "ARF-TM-38AEC7F4C8C69E7970A9",
    "ARF-TM-3AE967790A2565BB4220",
    "ARF-TM-3B1ABD4E22DE0D038865",
    "ARF-TM-3B6D8A091A00EA603974",
    "ARF-TM-3CFCE1249C5BDD088126",
    "ARF-TM-3D46BC1732ABAA22F2B2",
]


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> None:
    source = load_jsonl(SOURCE)
    draft = load_jsonl(DRAFT)
    reviewed = load_jsonl(REVIEWED)
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    fit = json.loads(FIT.read_text(encoding="utf-8"))
    canonical = json.loads(CANONICAL_CODEBOOK.read_text(encoding="utf-8"))
    temporary = json.loads(TEMP_CODEBOOK.read_text(encoding="utf-8"))

    assert len(source) == len(draft) == len(reviewed) == 200
    assert set(CHANGES) == set(CHANGE_META)
    assert validation["error_count"] == 0 and validation["valid"] is True
    assert fit["fixed_overflow_count"] == 0
    assert fit["encoding_error_count"] == 0
    assert fit["global_encoding_error_count"] == 0

    draft_by_id = {str(unit["tm_id"]): unit for unit in draft}
    reviewed_by_id = {str(unit["tm_id"]): unit for unit in reviewed}
    source_by_id = {str(unit["tm_id"]): unit for unit in source}
    changed_ids = [
        str(after["tm_id"])
        for before, after in zip(draft, reviewed)
        if before["translation_ko"] != after["translation_ko"]
    ]
    assert set(changed_ids) == set(CHANGES)

    modifications = []
    for tm_id in changed_ids:
        category, reason = CHANGE_META[tm_id]
        modifications.append(
            {
                "tm_id": tm_id,
                "source_text": source_by_id[tm_id]["source_text"],
                "before": draft_by_id[tm_id]["translation_ko"],
                "after": reviewed_by_id[tm_id]["translation_ko"],
                "category": category,
                "reason": reason,
            }
        )

    old_characters = canonical["characters"]
    new_characters = temporary["characters"]
    old_unchanged = all(
        char in new_characters and new_characters[char] == record
        for char, record in old_characters.items()
    )
    unmatched_ids = [str(item["tm_id"]) for item in fit["unmatched_system_units"]]
    resizable = [item for item in fit["overflow_fields"] if item["table_resizable"]]

    report = {
        "schema": "arf-translation-independent-review-v1",
        "batch_id": "batch_0006",
        "draft_author": "/root/translate_batch_0006",
        "reviewer": "/root/review_batch_0006",
        "independent_review": True,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_services_used": [],
        "source": str(SOURCE).replace("\\", "/"),
        "draft": str(DRAFT).replace("\\", "/"),
        "reviewed_output": str(REVIEWED).replace("\\", "/"),
        "validation_report": str(VALIDATION).replace("\\", "/"),
        "fit_report": str(FIT).replace("\\", "/"),
        "reviewed_units": 200,
        "modified_units": len(modifications),
        "unchanged_units": 200 - len(modifications),
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
        "modifications": modifications,
        "residual_issues": [
            {
                "tm_id": "ARF-TM-3B355F864488A6485706",
                "severity": "source_structure_marker",
                "issue": "<$0F> 뒤의 座는 도움말 명령 매개변수로 보이므로 자연어로 번역하지 않고 보존했다. 이 때문에 일본어 잔존 경고 1건이 의도적으로 남는다.",
            },
            {
                "tm_ids": SUSPECTED_PREFIX_IDS,
                "severity": "suspected_inline_structure_prefix",
                "issue": "선두의 9, 2, B, C, M6h, 6, 작은따옴표, 큰따옴표, X는 채팅·마법·도움말 구조 바이트일 가능성이 있어 제거하지 않았다. 구조화된 경계 감사 뒤 정확한 표시 문자열에만 번역을 적용해야 한다.",
            },
            {
                "tm_ids": SPLIT_BOUNDARY_IDS,
                "severity": "source_catalog_split_boundary",
                "issue": "‘らないリフィア’와 ‘の間’은 선두가 잘린 자연어 조각으로 보인다. 현재 TM에서는 조각의 의미만 보존했으며, 실제 chat.bin 필드 경계를 확인하기 전 자동 삽입하지 않는다.",
            },
            {
                "tm_ids": VISIBILITY_UNCONFIRMED_IDS,
                "severity": "visibility_unconfirmed",
                "issue": "더미·테스트·※컷·번호형 개발 문자열은 의미를 검수했지만 플레이어 노출 여부가 확정되지 않았다.",
            },
            {
                "tm_ids": unmatched_ids,
                "severity": "structured_table_boundary_audit_required",
                "issue": "200개 중 37개는 구조화된 테이블 카탈로그와 정확히 일치하지 않았다. NUL 스캐너 경계·선두 구조 표식·개발 필드 가능성이 있으므로 별칭/경계 매핑 없이 자동 삽입하지 않는다.",
            },
            {
                "tm_ids": [str(item["tm_id"]) for item in resizable],
                "severity": "resizable_quest_in_place_overflow",
                "issue": "퀘스트 필드 3개는 원래 자리 용량을 넘지만 quest.bin 테이블 재빌더가 가변 풀 재배치를 지원한다. 고정 필드 초과는 0건이다.",
            },
        ],
        "validation": {
            "expected_units": 200,
            "actual_units": len(reviewed),
            "unique_tm_ids": len({str(unit["tm_id"]) for unit in reviewed}),
            "blank_translations": sum(
                not str(unit.get("translation_ko", "")).strip() for unit in reviewed
            ),
            "source_metadata_preserved": all(
                {key: value for key, value in src.items() if key != "translation_ko"}
                == {key: value for key, value in out.items() if key != "translation_ko"}
                for src, out in zip(source, reviewed)
            ),
            "control_tokens_preserved": True,
            "ids_and_order_preserved": [unit["tm_id"] for unit in source]
            == [unit["tm_id"] for unit in reviewed],
            "line_break_counts_preserved": all(
                str(src["source_text"]).count("\n")
                == str(out["translation_ko"]).count("\n")
                for src, out in zip(source, reviewed)
            ),
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
            "resizable_table_in_place_overflow_count": fit[
                "resizable_table_in_place_overflow_count"
            ],
            "resizable_overflows": resizable,
            "unmatched_system_tm_count": fit["unmatched_system_tm_count"],
            "encoding_error_count": fit["encoding_error_count"],
            "global_encoding_error_count": fit["global_encoding_error_count"],
            "known_fixed_fields_fit": fit["known_fixed_fields_fit"],
            "canonical_codebook_assigned": canonical["assigned"],
            "temporary_codebook_assigned": temporary["assigned"],
            "new_temporary_glyphs": temporary["assigned"] - canonical["assigned"],
            "canonical_assignments_unchanged": old_unchanged,
            "codebook_note": "현행 canonical_v1을 기존 매핑으로 사용한 append-only 임시 확장이다. 루트 병합 단계에서 최종 승인 코퍼스로 canonical codebook을 다시 확장해야 한다.",
        },
        "hashes": {
            "source_sha256": sha256(SOURCE),
            "draft_sha256": sha256(DRAFT),
            "reviewed_sha256": sha256(REVIEWED),
            "validation_sha256": sha256(VALIDATION),
            "fit_report_sha256": sha256(FIT),
            "temporary_codebook_sha256": sha256(TEMP_CODEBOOK),
        },
        "boundary_audit_application": {
            "status": "not_yet_available_for_batch_0006",
            "translation_engine_policy": "Codex internal models only",
            "external_translation_models_or_apis_used": False,
            "insertion_contract": "구조 경계가 확인된 clean_source_text와 exact table_unit_ids에만 삽입한다. NUL 스캐너의 손상된 바이트 범위를 직접 치환하지 않는다.",
        },
    }

    assert report["validation"]["source_metadata_preserved"] is True
    assert report["validation"]["line_break_counts_preserved"] is True
    assert old_unchanged is True
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "reviewed_units": 200,
                "modified_units": len(modifications),
                "fixed_overflow_count": fit["fixed_overflow_count"],
                "validator_error_count": validation["error_count"],
            }
        )
    )


if __name__ == "__main__":
    main()
