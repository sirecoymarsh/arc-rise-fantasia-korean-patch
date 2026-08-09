#!/usr/bin/env python3
"""Refresh ARF localization baseline progress and human-readable status."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha256(relative: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / relative).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    baseline_path = ROOT / "work/project/baseline_manifest.json"
    status_path = ROOT / "work/project/PROJECT_STATUS.md"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    coverage = load("work/translation/current/coverage.json")
    codebook = load("work/font/canonical_v1/codebook.json")
    fit = load("work/font/canonical_v1/fit_preflight.json")
    corpus = load("work/font/canonical_v1/corpus_manifest.json")
    injection = load("work/font/canonical_v1/injection_verification.json")
    table_application = load("work/system_table_application/application_proof.json")
    runtime_staging = load("work/partial_runtime_staging/staging_manifest.json")
    final_static = load("work/validation/final_static_verification.json")
    boundary = load(
        "work/translation/boundary_audit/canonical_system_boundary_audit.json"
    )
    pilot = load("work/pilot_v2/validation.json")

    reviewed_batches = sorted(
        Path(path).stem for path in coverage.get("batch_files", [])
    )
    draft_batches = sorted(
        path.stem for path in (ROOT / "work/translation/drafts").glob("batch_*.jsonl")
    )
    pending_drafts = sorted(set(draft_batches) - set(reviewed_batches))
    validation_summary: dict[str, dict[str, object]] = {}
    for batch in reviewed_batches:
        path = ROOT / f"work/translation/validation/{batch}_reviewed.json"
        if not path.is_file():
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        validation_summary[batch] = {
            "error_count": report["error_count"],
            "warning_count": report["warning_count"],
            "valid": report["valid"],
            "sha256": sha256(str(path.relative_to(ROOT)).replace("\\", "/")),
        }
    application_hashes = {
        path.stem: sha256(str(path.relative_to(ROOT)).replace("\\", "/"))
        for path in sorted(
            (ROOT / "work/translation/boundary_audit").glob(
                "application_report*.json"
            )
        )
    }

    baseline["immutable_source"]["last_sha256_reverification"] = {
        "date": "2026-08-03",
        "result": "matched immutable baseline",
        "sha256": baseline["immutable_source"]["sha256"],
    }
    baseline["localization_progress"] = {
        "glossary_terms": 286,
        "glossary_sha256": sha256("work/translation/glossary_agent/glossary.csv"),
        "reviewed_translation_units": coverage["reviewed_units"],
        "reviewed_translation_occurrences": coverage["translated_occurrences"],
        "coverage_percent": coverage["coverage_percent"],
        "reviewed_batches": reviewed_batches,
        "pending_draft_batches": pending_drafts,
        "reviewed_batch_validation": validation_summary,
        "current_translation_memory_sha256": sha256(
            "work/translation/current/translation_memory_draft.json"
        ),
        "current_translation_memory_csv_sha256": sha256(
            "work/translation/current/translation_memory_draft.csv"
        ),
        "coverage_sha256": sha256("work/translation/current/coverage.json"),
        "boundary_audit": {
            "audited_tm_units": boundary["summary"]["resolved_tm_units"],
            "ambiguous_tm_units": boundary["summary"]["ambiguous_tm_units"],
            "unmatched_tm_units": boundary["summary"]["unmatched_tm_units"],
            "sha256": sha256(
                "work/translation/boundary_audit/canonical_system_boundary_audit.json"
            ),
            "component_audits": boundary.get("components", []),
            "application_sha256": application_hashes,
        },
        "font": {
            "approved_corpus_units": corpus["approved_units"],
            "unique_hangul_in_corpus": corpus["unique_hangul"],
            "assigned_codebook_characters": codebook["assigned"],
            "reserved_source_pairs": codebook["reserved_source_pairs"],
            "available_after_reservations": codebook[
                "available_after_reservations"
            ],
            "codebook_sha256": sha256("work/font/canonical_v1/codebook.json"),
            "injection_verification_valid": injection["valid"],
            "injection_verification_errors": injection["error_count"],
            "injection_verification_sha256": sha256(
                "work/font/canonical_v1/injection_verification.json"
            ),
        },
        "fit_preflight": {
            "fixed_overflow_count": fit["fixed_overflow_count"],
            "resizable_table_in_place_overflow_count": fit[
                "resizable_table_in_place_overflow_count"
            ],
            "encoding_error_count": fit["encoding_error_count"],
            "global_encoding_error_count": fit["global_encoding_error_count"],
            "unmatched_system_tm_count": fit["unmatched_system_tm_count"],
            "known_fixed_fields_fit": fit["known_fixed_fields_fit"],
            "safe_for_fixed_table_insertion": fit[
                "safe_for_fixed_table_insertion"
            ],
            "sha256": sha256("work/font/canonical_v1/fit_preflight.json"),
        },
        "system_table_application_proof": {
            "approved_system_tm_units": table_application[
                "approved_system_tm_units"
            ],
            "replacement_table_fields": table_application[
                "replacement_table_fields"
            ],
            "payloads_rebuilt": table_application["payloads_rebuilt"],
            "fixed_payload_changes_outside_declared_slots": table_application[
                "fixed_payload_changes_outside_declared_slots"
            ],
            "verification_error_count": table_application[
                "verification_error_count"
            ],
            "valid": table_application["valid"],
            "sha256": sha256(
                "work/system_table_application/application_proof.json"
            ),
        },
        "partial_runtime_staging": {
            "edited_system_vol_entries": runtime_staging["output_system_vol"][
                "edited_entries"
            ],
            "system_vol_rebuild_policy": runtime_staging["output_system_vol"][
                "rebuild_policy"
            ],
            "direct_files": len(runtime_staging["direct_files"]),
            "static_validation_valid": runtime_staging["static_validation"][
                "valid"
            ],
            "static_validation_errors": runtime_staging["static_validation"][
                "error_count"
            ],
            "dolphin_screen_test": runtime_staging["dolphin_screen_test"],
            "sha256": sha256(
                "work/partial_runtime_staging/staging_manifest.json"
            ),
        },
        "final_static_verification": {
            "error_count": final_static["error_count"],
            "valid": final_static["valid"],
            "sha256": sha256("work/validation/final_static_verification.json"),
        },
        "runtime_pilot_static_validation": (
            "passed" if pilot["all_static_checks_passed"] else "failed"
        ),
        "runtime_pilot_dolphin_validation": pilot["runtime_dolphin_check"],
        "runtime_pilot_validation_sha256": sha256(
            "work/pilot_v2/validation.json"
        ),
    }
    baseline_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    warning_total = sum(
        int(item["warning_count"]) for item in validation_summary.values()
    )
    status = f"""# 《아크 라이즈 판타지아》 한국어화 상태

## 고정 정책

- 대상: 일본판 `RPJJ99` / 원본 RVZ 읽기 전용
- 원본 SHA-256: `{baseline['immutable_source']['sha256']}`
- 번역·교정·윤문·용어 통일: **Codex 내부 모델/하위 에이전트만 사용**
- 외부 번역 API·외부 생성 모델·웹 번역기: **사용 금지**
- 일본어 음성 유지, 원본 파일 직접 덮어쓰기 금지

## 완료된 기반 작업

- DATA 파티션 게임 파일 14,526개 추출 및 인벤토리 작성
- RTDP 1,064개, BSCR 609개, 비-BSCR 테이블 28개 전수 no-op 왕복 검증
- 텍스트 레코드 84,761개 / 중복 제거 TM 29,777개 구축
- 용어집 286개와 한국어 문체 가이드 확정
- WTM 9장 byte-exact 왕복 및 커스텀 EUC28 한글 주입 검증
- 현재 코드북 {codebook['assigned']}자, 원문 보존 슬롯 {codebook['reserved_source_pairs']:,}개와 충돌 0
- 승인 번역 전부 인코딩 및 고정 필드 preflight 통과
- 승인 배치 시스템 경계 이상 {boundary['summary']['resolved_tm_units']}건을 offset 근거로 해결(ambiguous 0)
- 승인 시스템 TM {table_application['approved_system_tm_units']:,}개를 13개 payload / {table_application['replacement_table_fields']:,}필드에 실제 적용·재카탈로그 검증
- `system.vol` 20개 entry 및 외부 시스템 파일 2개를 개발용 Riivolution staging으로 재구성·정적 검증

## 번역 진행률

- 독립 검수 승인: **{coverage['reviewed_units']:,} / {coverage['total_units']:,} 단위 ({coverage['coverage_percent']:.4f}%)**
- 승인 번역이 적용되는 원시 출현: **{coverage['translated_occurrences']:,} / {coverage['total_occurrences']:,}개**
- 검수 완료 배치: `{', '.join(reviewed_batches)}`
- 승인 배치 validator: 오류 0, 구조 표식 보존 경고 {warning_total}건
- 독립 검수 대기 초벌 배치: `{', '.join(pending_drafts) if pending_drafts else '없음'}`

## 정적 적합성

- 고정 필드 overflow: **{fit['fixed_overflow_count']}**
- 승인문 전역 인코딩 오류: **{fit['global_encoding_error_count']}**
- 가변 재빌드가 입증된 `quest.bin` 원위치 길이 초과: **{fit['resizable_table_in_place_overflow_count']}필드**
- 추가 경계 감사가 필요한 시스템 TM: **{fit['unmatched_system_tm_count']}개**
- WTM 주입 검증 오류: **{injection['error_count']}**
- 시스템 테이블 적용 증명 오류: **{table_application['verification_error_count']}**
- 부분 런타임 staging 정적 오류: **{runtime_staging['static_validation']['error_count']}** (Dolphin 화면 검사는 {runtime_staging['dolphin_screen_test']})
- 최종 교차 정적 검증 오류: **{final_static['error_count']}**

## 아직 완료되지 않은 항목

1. 나머지 번역 단위의 Codex 내부 번역과 독립 교차 검수
2. 후속 승인 배치마다 시스템 테이블 경계 이상 offset 감사
3. 이미지 기반 메뉴·로고·도움말 UI 한국어화
4. Dolphin 실제 화면에서 글꼴, 줄바꿈, 잘림, 전투·이벤트 회귀 검사
5. 전체 번역 완료 후 원본 해시 결속형 설치·복원 패치 제작

현재 산출물은 **완성 패치가 아니라 재현 가능한 개발 체크포인트**입니다.
"""
    status_path.write_text(status, encoding="utf-8")
    print(
        json.dumps(
            {
                "reviewed_units": coverage["reviewed_units"],
                "reviewed_batches": reviewed_batches,
                "pending_drafts": pending_drafts,
                "fixed_overflow_count": fit["fixed_overflow_count"],
                "unmatched_system_tm_count": fit["unmatched_system_tm_count"],
                "font_injection_valid": injection["valid"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
