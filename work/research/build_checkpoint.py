#!/usr/bin/env python3
"""Build a source-free, user-facing Arc Rise Fantasia localization checkpoint."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "outputs"
PACKAGE_NAME = "Arc_Rise_Fantasia_KO_Checkpoint_2026-08-03"
DEST = OUTPUTS / PACKAGE_NAME
ZIP_PATH = OUTPUTS / f"{PACKAGE_NAME}.zip"
PINNED_BOUNDARY_AUDIT_SHA256 = (
    "131DBA7684CA37C974FA0AF30654A71F53886A129B7258E978DF2C24BEB71920"
)
PINNED_FINAL_INTEGRATION_AUDIT_SHA256 = (
    "7E39315CDFE6F8A726BF1C5DBBF2D5C3BF83CB89718D3FB6872712A56B295D8D"
)


FILES: dict[str, str] = {
    "project/baseline_manifest.json": "work/project/baseline_manifest.json",
    "project/language_contract.json": "work/project/language_contract.json",
    "project/translation_policy.md": "work/project/translation_policy.md",
    "project/PROJECT_STATUS.md": "work/project/PROJECT_STATUS.md",
    "catalog/text_catalog_summary.json": "work/catalog/text_v2/text_catalog_summary.json",
    "catalog/disc_inventory_summary.json": "work/catalog/disc_inventory_summary.json",
    "localization/glossary.csv": "work/translation/glossary_agent/glossary.csv",
    "localization/style_guide.md": "work/translation/glossary_agent/style_guide.md",
    "localization/evidence.md": "work/translation/glossary_agent/evidence.md",
    "localization/frequency.json": "work/translation/glossary_agent/frequency.json",
    "translation/TRANSLATION_RULES.md": "work/translation/tm_v2/TRANSLATION_RULES.md",
    "translation/batch_manifest.json": "work/translation/tm_v2/batch_manifest.json",
    "translation/translation_memory_draft.csv": "work/translation/current/translation_memory_draft.csv",
    "translation/translation_memory_draft.json": "work/translation/current/translation_memory_draft.json",
    "translation/approved_units.jsonl": "work/font/canonical_v1/approved_units.jsonl",
    "translation/coverage.json": "work/translation/current/coverage.json",
    "translation/layout_adjustments/batch_0001_fit_proposals.json": "work/translation/layout_adjustments/batch_0001_fit_proposals.json",
    "translation/layout_adjustments/batch_0002_fit_proposals.json": "work/translation/layout_adjustments/batch_0002_fit_proposals.json",
    "translation/boundary_audit/REPORT.md": "work/translation/boundary_audit/REPORT.md",
    "translation/boundary_audit/batches_0001_0002.json": "work/translation/boundary_audit/batches_0001_0002.json",
    "translation/boundary_audit/application_report.json": "work/translation/boundary_audit/application_report.json",
    "translation/boundary_audit/REPORT_0003_0004.md": "work/translation/boundary_audit/REPORT_0003_0004.md",
    "translation/boundary_audit/batches_0003_0004.json": "work/translation/boundary_audit/batches_0003_0004.json",
    "translation/boundary_audit/application_report_0003_0004.json": "work/translation/boundary_audit/application_report_0003_0004.json",
    "translation/boundary_audit/REPORT_0005.md": "work/translation/boundary_audit/REPORT_0005.md",
    "translation/boundary_audit/batch_0005.json": "work/translation/boundary_audit/batch_0005.json",
    "translation/boundary_audit/application_report_0005.json": "work/translation/boundary_audit/application_report_0005.json",
    "translation/boundary_audit/canonical_system_boundary_audit.json": "work/translation/boundary_audit/canonical_system_boundary_audit.json",
    "translation/boundary_audit/REPORT_0006.md": "work/translation/boundary_audit/REPORT_0006.md",
    "translation/boundary_audit/batch_0006.json": "work/translation/boundary_audit/batch_0006.json",
    "translation/boundary_audit/application_report_0006.json": "work/translation/boundary_audit/application_report_0006.json",
    "translation/boundary_audit/REPORT_0007.md": "work/translation/boundary_audit/REPORT_0007.md",
    "translation/boundary_audit/batch_0007.json": "work/translation/boundary_audit/batch_0007.json",
    "translation/boundary_audit/application_report_0007.json": "work/translation/boundary_audit/application_report_0007.json",
    "translation/boundary_audit/INTEGRATION_AUDIT.md": "work/translation/boundary_audit/INTEGRATION_AUDIT.md",
    "translation/boundary_audit/integration_audit.json": "work/translation/boundary_audit/integration_audit.json",
    "translation/boundary_audit/FINAL_INTEGRATION_AUDIT.md": "work/translation/boundary_audit/FINAL_INTEGRATION_AUDIT.md",
    "translation/boundary_audit/final_integration_audit.json": "work/translation/boundary_audit/final_integration_audit.json",
    "translation/reviewed/batch_0001.jsonl": "work/translation/reviewed/batch_0001.jsonl",
    "translation/reviews/batch_0001_review.json": "work/translation/reviews/batch_0001_review.json",
    "translation/validation/batch_0001_reviewed.json": "work/translation/validation/batch_0001_reviewed.json",
    "technical/rtdp/RESEARCH_REPORT.md": "work/research/rtdp_agent/RESEARCH_REPORT.md",
    "technical/rtdp/roundtrip_proof.json": "work/research/rtdp_agent/roundtrip_proof.json",
    "technical/bscr/RESEARCH_REPORT.md": "work/research/bscr_agent/RESEARCH_REPORT.md",
    "technical/bscr/full_audit.json": "work/research/bscr_agent/full_audit.json",
    "technical/tables/RESEARCH_REPORT.md": "work/research/table_agent/RESEARCH_REPORT.md",
    "technical/tables/roundtrip_proof.json": "work/research/table_agent/roundtrip_proof.json",
    "technical/tables/approved_application_proof.json": "work/system_table_application/application_proof.json",
    "technical/font/report.md": "work/research/font_agent/report.md",
    "technical/font/validation.json": "work/research/font_agent/validation.json",
    "technical/font/original_reserved_pairs_v2_stats.json": "work/font/original_reserved_pairs_v2_stats.json",
    "technical/font/approved_codebook.json": "work/font/canonical_v1/codebook.json",
    "technical/font/corpus_manifest.json": "work/font/canonical_v1/corpus_manifest.json",
    "technical/font/fit_preflight.json": "work/font/canonical_v1/fit_preflight.json",
    "technical/font/unmatched_analysis.json": "work/font/canonical_v1/unmatched_analysis.json",
    "technical/font/injection_manifest.json": "work/font/canonical_v1/injection_manifest.json",
    "technical/font/injection_verification.json": "work/font/canonical_v1/injection_verification.json",
    "technical/container/RESEARCH_REPORT.md": "work/research/container_agent/RESEARCH_REPORT.md",
    "technical/container/README.md": "work/research/container_agent/README.md",
    "technical/container/verification.json": "work/research/container_agent/verification.json",
    "technical/container/reproduction.json": "work/research/container_agent/reproduction.json",
    "technical/container/container_tool.js": "work/research/container_agent/container_tool.js",
    "technical/container/verify_container_tool.js": "work/research/container_agent/verify_container_tool.js",
    "technical/runtime/staging_manifest.json": "work/partial_runtime_staging/staging_manifest.json",
    "technical/runtime/system_vol_rebuild_report.json": "work/partial_runtime_staging/system_vol_rebuild_report.json",
    "technical/runtime/system_vol_edits.json": "work/partial_runtime_staging/system_vol_edits.json",
    "technical/tools/validate_translation_batch.py": "work/research/validate_translation_batch.py",
    "technical/tools/merge_translation_batches.py": "work/research/merge_translation_batches.py",
    "technical/tools/encode_custom_euc28.py": "work/research/encode_custom_euc28.py",
    "technical/tools/check_translation_fit.py": "work/research/check_translation_fit.py",
    "technical/tools/analyze_unmatched_fit.py": "work/research/analyze_unmatched_fit.py",
    "technical/tools/apply_boundary_audit.py": "work/research/apply_boundary_audit.py",
    "technical/tools/apply_boundary_audit_0003_0004.py": "work/research/apply_boundary_audit_0003_0004.py",
    "technical/tools/apply_boundary_audit_0005.py": "work/research/apply_boundary_audit_0005.py",
    "technical/tools/apply_boundary_audit_0006.py": "work/research/apply_boundary_audit_0006.py",
    "technical/tools/apply_boundary_audit_0007.py": "work/research/apply_boundary_audit_0007.py",
    "technical/tools/build_canonical_boundary_audit.py": "work/research/build_canonical_boundary_audit.py",
    "technical/tools/build_approved_corpus.py": "work/research/build_approved_corpus.py",
    "technical/tools/verify_injected_fonts.py": "work/research/verify_injected_fonts.py",
    "technical/tools/validate_checkpoint.py": "work/research/validate_checkpoint.py",
    "technical/tools/update_project_metadata.py": "work/research/update_project_metadata.py",
    "technical/tools/build_system_table_application_proof.py": "work/research/build_system_table_application_proof.py",
    "technical/tools/build_partial_runtime_staging.py": "work/research/build_partial_runtime_staging.py",
    "technical/tools/build_final_static_verification.py": "work/research/build_final_static_verification.py",
    "technical/final_static_verification.json": "work/validation/final_static_verification.json",
    "pilot/PILOT_STATUS.md": "work/pilot_v2/PILOT_STATUS.md",
    "pilot/validation.json": "work/pilot_v2/validation.json",
    "pilot/package_manifest.json": "work/pilot_v2/package_manifest.json",
    "pilot/README-PILOT.md": "work/pilot_v2/riivolution_sd/README-PILOT.md",
    "pilot/arc_rise_fantasia_ko_pilot.xml": "work/pilot_v2/riivolution_sd/riivolution/arc_rise_fantasia_ko_pilot.xml",
    "pilot/arc_rise_fantasia_ko_dev.xml": "work/partial_runtime_staging/riivolution_sd/riivolution/arc_rise_fantasia_ko_dev.xml",
}

GLOBS: dict[str, str] = {
    "translation/reviewed": "work/translation/reviewed/batch_*.jsonl",
    "translation/reviews": "work/translation/reviews/batch_*_review.json",
    "translation/validation": "work/translation/validation/batch_*_reviewed.json",
    "translation/draft_history": "work/translation/drafts/batch_*.jsonl",
    "translation/draft_validation_history": "work/translation/validation/batch_*_draft.json",
    "translation/layout_adjustments": "work/translation/layout_adjustments/*.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def copy_files() -> list[str]:
    missing: list[str] = []
    for destination, source in FILES.items():
        source_path = ROOT / source
        if not source_path.is_file():
            missing.append(source)
            continue
        destination_path = DEST / destination
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
    for destination_dir, pattern in GLOBS.items():
        for source_path in sorted(ROOT.glob(pattern)):
            destination_path = DEST / destination_dir / source_path.name
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
    return missing


def write_readme() -> None:
    coverage = json.loads((ROOT / "work/translation/current/coverage.json").read_text(encoding="utf-8"))
    baseline = json.loads((ROOT / "work/project/baseline_manifest.json").read_text(encoding="utf-8"))
    pilot = json.loads((ROOT / "work/pilot_v2/validation.json").read_text(encoding="utf-8"))
    codebook = json.loads((ROOT / "work/font/canonical_v1/codebook.json").read_text(encoding="utf-8"))
    fit = json.loads((ROOT / "work/font/canonical_v1/fit_preflight.json").read_text(encoding="utf-8"))
    font_verify = json.loads((ROOT / "work/font/canonical_v1/injection_verification.json").read_text(encoding="utf-8"))
    boundary = json.loads((ROOT / "work/translation/boundary_audit/canonical_system_boundary_audit.json").read_text(encoding="utf-8"))
    table_application = json.loads((ROOT / "work/system_table_application/application_proof.json").read_text(encoding="utf-8"))
    runtime_staging = json.loads((ROOT / "work/partial_runtime_staging/staging_manifest.json").read_text(encoding="utf-8"))
    final_audit = json.loads((ROOT / "work/translation/boundary_audit/final_integration_audit.json").read_text(encoding="utf-8"))
    source = baseline["immutable_source"]
    text = f"""# 《아크 라이즈 판타지아》 한국어화 기술 체크포인트

## 중요

이 파일은 **완성 패치가 아니라 재현 가능한 개발 체크포인트**입니다. 원본 게임 데이터와 수정된 게임 바이너리는 포함하지 않습니다. 정식 패치는 전체 번역·독립 검수·Dolphin 화면 검증이 끝난 뒤 별도로 만듭니다.

## 번역 계약

- 일본어 → 한국어 직접 번역
- 번역·교정·윤문·용어 통일은 **Codex 내부 모델/하위 에이전트만 사용**
- 외부 번역 API·외부 생성 모델은 사용 금지
- 일본어 음성 유지
- 제어 코드와 바이너리 구조 보존

## 기준 원본

- 게임 ID: `{baseline['game']['game_id']}`
- 원본 크기: `{source['size_bytes']:,}` bytes
- 원본 SHA-256: `{source['sha256']}`
- 원본은 읽기 전용으로 보존됨

## 이 체크포인트의 상태

- 텍스트 레코드: **84,761개**
- 중복 제거 번역 단위: **29,777개**
- 독립 검수 승인: **{coverage['reviewed_units']}개** ({coverage['coverage_percent']:.4f}%)
- 해당 번역이 적용되는 원시 출현: **{coverage['translated_occurrences']}개**
- 용어집: **286개**
- 한글 코드북: **{codebook['assigned']}자** (원문 보존 슬롯 {codebook['reserved_source_pairs']:,}개와 충돌 0)
- 현재 승인문 전체 인코딩 및 WTM 주입 검증: **{'통과' if font_verify['valid'] else '실패'}**
- 구조화 고정 필드 overflow/인코딩 오류: **{fit['fixed_overflow_count']} / {fit['global_encoding_error_count']}**
- 추가 경계 감사 대기 시스템 TM: **{fit['unmatched_system_tm_count']}개**
- offset 근거로 해결한 시스템 경계 이상: **{boundary['summary']['resolved_tm_units']}개** (ambiguous 0)
- 승인 시스템 TM 실제 적용 증명: **{table_application['approved_system_tm_units']:,}개 / {table_application['replacement_table_fields']:,}필드 / 오류 {table_application['verification_error_count']}**
- 부분 Riivolution staging 정적 검증: **{'통과' if runtime_staging['static_validation']['valid'] else '실패'}** (바이너리는 체크포인트에 미포함)
- 독립 최종 통합 감사: **{final_audit['checks']['passed']}/{final_audit['checks']['total']} 통과**, 실패 {final_audit['checks']['failed']} (`{final_audit['status']}`)
- RTDP 1,064개 및 BSCR 609개 전수 no-op 왕복 검증 완료
- WTM 글꼴 9장 byte-exact 왕복 및 한글 샘플 주입 검증 완료
- 한 줄 런타임 파일럿 정적 검사: **{'통과' if pilot['all_static_checks_passed'] else '실패'}**
- Dolphin 실제 화면 검사: **대기 중**

## 폴더 안내

- `project/`: 원본 기준, 언어 계약, 진행 상태
- `catalog/`: 텍스트 카탈로그 요약
- `localization/`: 용어집, 문체 가이드, 근거와 빈도
- `translation/`: 현재 TM JSON/CSV, 검수 완료 배치, 검수·검증 보고서
- `translation/draft_history/`: 독립 검수 전 초벌 번역 보존본
- `technical/`: RTDP/BSCR/테이블/글꼴/컨테이너 분석 및 재현 도구
- `pilot/`: 바이너리를 제외한 실험용 Riivolution XML과 정적 검증 기록

## 재개 기준

다음 단계는 번역 배치를 Codex 내부 모델로 계속 작성하고 다른 Codex 에이전트가 독립 검수한 뒤, 남은 경계 이상을 감사하고 Dolphin 화면 회귀 검증을 수행하는 것입니다.
"""
    (DEST / "README.md").write_text(text, encoding="utf-8")


def write_manifest(missing: list[str]) -> None:
    entries = []
    for path in sorted(p for p in DEST.rglob("*") if p.is_file() and p.name != "MANIFEST.json"):
        entries.append(
            {
                "path": path.relative_to(DEST).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    manifest = {
        "schema": "arf-ko-development-checkpoint-v1",
        "package": PACKAGE_NAME,
        "created": "2026-08-03",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "independent_static_audit_status": "PASS_STATIC_RUNTIME_PENDING",
        "contains_original_game_data": False,
        "runtime_ready_release": False,
        "missing_optional_sources": missing,
        "file_count_excluding_manifest": len(entries),
        "files": entries,
    }
    (DEST / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def make_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in DEST.rglob("*") if p.is_file()):
            archive.write(path, (Path(PACKAGE_NAME) / path.relative_to(DEST)).as_posix())
    checksum_path = OUTPUTS / f"{PACKAGE_NAME}.zip.sha256"
    checksum_path.write_text(f"{sha256(ZIP_PATH)}  {ZIP_PATH.name}\n", encoding="ascii")


def main() -> int:
    audit_path = (
        ROOT
        / "work/translation/boundary_audit/canonical_system_boundary_audit.json"
    )
    audit_hash = sha256(audit_path)
    if audit_hash != PINNED_BOUNDARY_AUDIT_SHA256:
        raise RuntimeError(
            f"refusing unpinned boundary audit: {audit_hash} != "
            f"{PINNED_BOUNDARY_AUDIT_SHA256}"
        )
    final_audit_path = (
        ROOT
        / "work/translation/boundary_audit/final_integration_audit.json"
    )
    final_audit_hash = sha256(final_audit_path)
    if final_audit_hash != PINNED_FINAL_INTEGRATION_AUDIT_SHA256:
        raise RuntimeError(
            f"refusing unpinned final integration audit: {final_audit_hash} != "
            f"{PINNED_FINAL_INTEGRATION_AUDIT_SHA256}"
        )
    final_audit = json.loads(final_audit_path.read_text(encoding="utf-8"))
    if (
        final_audit.get("status") != "PASS_STATIC_RUNTIME_PENDING"
        or final_audit.get("checks", {}).get("failed") != 0
    ):
        raise RuntimeError("final integration audit is not a clean static pass")
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        resolved = DEST.resolve()
        if resolved.parent != OUTPUTS.resolve():
            raise RuntimeError(f"refusing to remove unexpected path: {resolved}")
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    missing = copy_files()
    write_readme()
    write_manifest(missing)
    make_zip()
    print(
        json.dumps(
            {
                "package_dir": str(DEST),
                "zip": str(ZIP_PATH),
                "zip_size": ZIP_PATH.stat().st_size,
                "zip_sha256": sha256(ZIP_PATH),
                "missing_optional_sources": missing,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
