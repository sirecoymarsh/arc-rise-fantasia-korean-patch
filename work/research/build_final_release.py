#!/usr/bin/env python3
"""Build the final source-bound Riivolution/Dolphin Korean patch package.

The release is assembled only from an explicit allowlist rooted at the final
runtime staging directory.  It never embeds the pristine RVZ and never edits
the user's source image.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


SOURCE_RVZ_SHA256 = "4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5"
GAME_ID = "RPJJ99"
PACKAGE_NAME = "Arc_Rise_Fantasia_Korean_Patch_v1.0.1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_text_crlf(path: Path, text: str, encoding: str) -> None:
    """Write deterministic Windows text, optionally with an encoding BOM."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(normalized.replace("\n", "\r\n").encode(encoding))


def safe_relative(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise RuntimeError(f"unsafe release path: {relative}")
    return relative


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = safe_relative(path, root).encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest().upper()


def validate_staging(
    staging: Path, staging_manifest_path: Path, staging_manifest: dict[str, object]
) -> None:
    if staging_manifest.get("schema") != "arf-full-runtime-staging-v2":
        raise RuntimeError("unexpected or missing final staging manifest schema")
    if staging_manifest.get("game_id") != GAME_ID:
        raise RuntimeError("final staging manifest game ID mismatch")
    static = dict(staging_manifest.get("static_validation", {}))
    if static.get("valid") is not True or int(static.get("error_count", -1)) != 0:
        raise RuntimeError("final staging static validation is not green")
    physical_root = staging / "arc_rise_fantasia_ko_full" / "files"
    xml_path = staging / "riivolution" / "arc_rise_fantasia_ko_full.xml"
    if not physical_root.is_dir() or not xml_path.is_file():
        raise RuntimeError("final staging layout is incomplete")
    physical_count = sum(path.is_file() for path in physical_root.rglob("*"))
    declared_physical = int(
        dict(staging_manifest.get("counts", {})).get("staged_physical_files", -1)
    )
    if physical_count != declared_physical:
        raise RuntimeError(
            f"staging physical count mismatch: {physical_count} != {declared_physical}"
        )
    riivolution = dict(staging_manifest.get("riivolution", {}))
    if int(riivolution.get("file_count", -1)) != physical_count:
        raise RuntimeError("Riivolution file-rule count does not match physical staging")
    if str(riivolution.get("sha256", "")).upper() != sha256(xml_path):
        raise RuntimeError("Riivolution XML hash differs from staging manifest")
    battle = dict(staging_manifest.get("battle_enemy_application", {}))
    expected_battle = {
        "entries": 270,
        "display_names": 270,
        "alternate_display_names": 87,
        "part_names": 3,
        "skill_names": 672,
        "total_units": 1032,
        "entries_fitting_source_slots": 270,
        "changed_outside_allowed_bytes": 0,
    }
    if battle.get("valid") is not True or any(
        int(battle.get(key, -1)) != value for key, value in expected_battle.items()
    ):
        raise RuntimeError("battle enemy translation application is incomplete")
    enemy_vld = physical_root / "Btl" / "btl_enemy.vld"
    staged_rows = {
        str(row.get("physical_path")): row
        for row in static.get("staged_files", [])
        if isinstance(row, dict)
    }
    enemy_row = staged_rows.get("Btl/btl_enemy.vld", {})
    if not enemy_vld.is_file() or sha256(enemy_vld) != str(enemy_row.get("output_sha256", "")).upper():
        raise RuntimeError("battle enemy VLD is missing or differs from the bound staging row")
    residue = dict(staging_manifest.get("system_text_residue_application", {}))
    if (
        residue.get("valid") is not True
        or int(residue.get("translated_fields", -1)) != 30
        or int(residue.get("ability_names", -1)) != 14
        or int(residue.get("semantic_japanese_unmatched_after", -1)) != 0
        or int(residue.get("changed_outside_allowed_bytes", -1)) != 0
    ):
        raise RuntimeError("system text residue closure is incomplete")
    if not staging_manifest_path.is_file():
        raise RuntimeError("staging manifest disappeared during validation")


def copy_tree_allowlisted(source: Path, destination: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for item in sorted(source.rglob("*")):
        if item.is_symlink():
            raise RuntimeError(f"symlink/reparse-like source rejected: {item}")
        if not item.is_file():
            continue
        relative = safe_relative(item, source)
        target = destination / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        entries.append(
            {
                "path": f"payload/riivolution_sd/{relative}",
                "role": "riivolution_overlay",
                "size_bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )
    if not entries:
        raise RuntimeError("final runtime staging contains no files")
    return entries


def write_public_files(
    package: Path,
    staging_manifest: dict[str, object],
    staging_manifest_sha256: str,
    staging_tree_sha256: str,
) -> None:
    readme = f"""# 아크 라이즈 판타지아 한국어 패치 v1.0.1

## 설치

1. ZIP 파일의 압축을 완전히 풉니다.
2. Dolphin을 종료합니다.
3. `설치하기.cmd`를 더블클릭합니다.
4. 설치 완료 안내가 나오면 Dolphin을 실행합니다.
5. 게임을 우클릭하고 **Riivolution 패치로 시작**을 선택한 뒤 한국어 패치를 켭니다.

Dolphin 사용자 폴더를 자동으로 찾지 못하면 폴더 선택창이 열립니다. Dolphin의
**파일 → 사용자 폴더 열기**로 확인되는 폴더를 선택하면 됩니다. PowerShell 명령이나
원본 RVZ 경로를 입력할 필요가 없으며 원본 RVZ는 수정하지 않습니다.

## 직접 복사할 경우

`payload\\riivolution_sd` 안의 `arc_rise_fantasia_ko_full` 폴더와
`riivolution` 폴더를 Dolphin 사용자 폴더의 `Load` 폴더에 복사합니다.
`riivolution_sd` 폴더 자체를 복사하면 안 됩니다.

## 삭제

Dolphin 사용자 폴더의 다음 두 항목만 삭제합니다.

- `Load\\arc_rise_fantasia_ko_full`
- `Load\\riivolution\\arc_rise_fantasia_ko_full.xml`

다른 Riivolution 패치가 있을 수 있으므로 `Load\\riivolution` 폴더 전체를 삭제하면
안 됩니다.

## 대상 및 범위

- 게임 ID: `{GAME_ID}`
- 일본판 원본 RVZ SHA-256: `{SOURCE_RVZ_SHA256}`
- 일본어 음성 유지
- 원본 RVZ를 수정하지 않는 Riivolution/Dolphin 오버레이 방식
- 전투 몬스터 기본명 270개와 보조 표시명 87회, 보스 부위명 3개, 몬스터 기술명 672회(고유 기술명 226개) 한국어화
- 전수검사에서 추가 발견한 어빌리티명 14개, 채팅 제목 15개, 상점명 1개 한국어화

번역·교정·윤문·용어 통일에는 Codex 내부 모델만 사용했습니다. 외부 번역
서비스나 외부 생성 모델은 사용하지 않았습니다.

## 오프닝 영상 안정성

`Movie/RAY_OP_02.sfd`는 일본판 원본을 그대로 사용합니다. 개발 중 전체 영상을
재인코딩한 후보에서 실제 정지가 확인되어 릴리스에서는 해당 영상 오버레이를
제외했습니다. 따라서 오프닝 중 게임 제목 한 줄은 일본어로 남지만 영상과 음성은
원본과 동일하게 재생됩니다.
"""
    write_text_crlf(package / "README_KO.md", readme, "utf-8")
    public_staging = {
        "schema": staging_manifest.get("schema"),
        "game_id": staging_manifest.get("game_id"),
        "counts": staging_manifest.get("counts", {}),
        "riivolution": {
            "xml": staging_manifest.get("riivolution", {}).get("xml"),
            "file_count": staging_manifest.get("riivolution", {}).get("file_count"),
            "memory_count": staging_manifest.get("riivolution", {}).get("memory_count"),
            "resize_true_count": staging_manifest.get("riivolution", {}).get("resize_true_count"),
            "sha256": staging_manifest.get("riivolution", {}).get("sha256"),
        },
        "static_validation": {
            "valid": staging_manifest.get("static_validation", {}).get("valid"),
            "error_count": staging_manifest.get("static_validation", {}).get("error_count"),
        },
        "manifest_sha256": staging_manifest_sha256,
        "tree_sha256": staging_tree_sha256,
    }
    public = {
        "schema": "arf-ko-public-provenance-v1",
        "game_id": GAME_ID,
        "source_rvz_sha256": SOURCE_RVZ_SHA256,
        "translation_units": int(staging_manifest.get("counts", {}).get("tm_units", 0))
        + int(staging_manifest.get("counts", {}).get("battle_enemy_unique_skill_names", 0))
        + int(staging_manifest.get("counts", {}).get("system_text_residue_translation_occurrences", 0)),
        "translation_occurrences": int(staging_manifest.get("counts", {}).get("catalog_occurrences", 0))
        + int(staging_manifest.get("counts", {}).get("battle_enemy_translation_occurrences", 0))
        + int(staging_manifest.get("counts", {}).get("system_text_residue_translation_occurrences", 0)),
        "battle_enemy": {
            "entries": staging_manifest.get("counts", {}).get("battle_enemy_entries"),
            "display_name_occurrences": staging_manifest.get("counts", {}).get("battle_enemy_display_name_occurrences"),
            "alternate_display_name_occurrences": staging_manifest.get("counts", {}).get("battle_enemy_alternate_display_name_occurrences"),
            "part_name_occurrences": staging_manifest.get("counts", {}).get("battle_enemy_part_name_occurrences"),
            "skill_name_occurrences": staging_manifest.get("counts", {}).get("battle_enemy_skill_name_occurrences"),
            "unique_skill_names": staging_manifest.get("counts", {}).get("battle_enemy_unique_skill_names"),
        },
        "system_text_residue": {
            "translation_occurrences": staging_manifest.get("counts", {}).get("system_text_residue_translation_occurrences"),
            "ability_names": staging_manifest.get("system_text_residue_application", {}).get("ability_names"),
            "chat_titles": staging_manifest.get("system_text_residue_application", {}).get("chat_titles"),
            "shop_names": staging_manifest.get("system_text_residue_application", {}).get("shop_names"),
            "semantic_japanese_unmatched_after": staging_manifest.get("system_text_residue_application", {}).get("semantic_japanese_unmatched_after"),
        },
        "reviewed_batches": 149,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "delivery": "one-click Riivolution overlay installer",
        "staging_summary": public_staging,
    }
    write_text_crlf(
        package / "PROVENANCE.json",
        json.dumps(public, ensure_ascii=False, indent=2) + "\n",
        "utf-8",
    )


def copy_installer_scripts(root: Path, package: Path) -> None:
    script_dir = root / "work" / "release_scripts"
    for name in ("Install-ARF-KO.ps1", "설치하기.cmd"):
        source = script_dir / name
        if not source.is_file():
            raise RuntimeError(f"missing release script: {source}")
        if source.suffix.lower() == ".ps1":
            # Windows PowerShell 5.1 requires a BOM for non-ASCII source.
            write_text_crlf(
                package / name,
                source.read_text(encoding="utf-8-sig"),
                "utf-8-sig",
            )
        else:
            # Keep the CMD launcher ASCII so cmd.exe never interprets a BOM
            # as part of the first command.
            shutil.copy2(source, package / name)


def build_manifest(
    package: Path,
    overlay_entries: list[dict[str, object]],
    staging_manifest_sha256: str,
    staging_tree_sha256: str,
) -> dict[str, object]:
    fixed_entries: list[dict[str, object]] = []
    for path in sorted(p for p in package.rglob("*") if p.is_file() and p.name != "MANIFEST.json"):
        relative = safe_relative(path, package)
        role = "installer_metadata"
        if relative.startswith("payload/riivolution_sd/"):
            role = "riivolution_overlay"
        fixed_entries.append(
            {
                "path": relative,
                "role": role,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    overlay_paths = {str(item["path"]) for item in overlay_entries}
    actual_overlay = {
        str(item["path"]) for item in fixed_entries if item["role"] == "riivolution_overlay"
    }
    if overlay_paths != actual_overlay:
        raise RuntimeError("overlay allowlist changed while constructing the release")
    manifest = {
        "schema": "arf-ko-riivolution-release-v1",
        "package": PACKAGE_NAME,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "game_id": GAME_ID,
        "source_rvz_sha256": SOURCE_RVZ_SHA256,
        "source_media_included": False,
        "source_media_write_policy": "read-only; never overwrite",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "runtime_ready_release": True,
        "staging_manifest_sha256": staging_manifest_sha256,
        "staging_tree_sha256": staging_tree_sha256,
        "overlay_file_count": len(actual_overlay),
        "game_replacement_file_count": len(
            {
                path
                for path in actual_overlay
                if not path.startswith("payload/riivolution_sd/riivolution/")
            }
        ),
        "file_count_excluding_manifest": len(fixed_entries),
        "files": fixed_entries,
    }
    write_text_crlf(
        package / "MANIFEST.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        "utf-8",
    )
    return manifest


def make_zip(package: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in package.rglob("*") if p.is_file()):
            member = (PurePosixPath(package.name) / PurePosixPath(safe_relative(path, package))).as_posix()
            archive.write(path, member)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--staging", type=Path)
    parser.add_argument("--staging-manifest", type=Path)
    parser.add_argument("--outputs", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    staging = (args.staging or root / "work" / "final_runtime_staging" / "riivolution_sd").resolve()
    outputs = (args.outputs or root / "outputs").resolve()
    staging_manifest_path = (
        args.staging_manifest or staging.parent / "staging_manifest.json"
    ).resolve()
    if not staging.is_dir():
        raise RuntimeError(f"missing final runtime staging: {staging}")
    if not staging_manifest_path.is_file():
        raise RuntimeError(f"missing staging manifest: {staging_manifest_path}")
    staging_manifest = json.loads(staging_manifest_path.read_text(encoding="utf-8"))
    validate_staging(staging, staging_manifest_path, staging_manifest)
    staging_manifest_hash = sha256(staging_manifest_path)
    staging_tree_hash = tree_sha256(staging)
    package = outputs / PACKAGE_NAME
    zip_path = outputs / f"{PACKAGE_NAME}.zip"
    if package.exists():
        if package.parent.resolve() != outputs:
            raise RuntimeError(f"refusing to remove unexpected path: {package}")
        shutil.rmtree(package)
    package.mkdir(parents=True)
    payload = package / "payload" / "riivolution_sd"
    payload.mkdir(parents=True)
    overlay_entries = copy_tree_allowlisted(staging, payload)
    write_public_files(
        package, staging_manifest, staging_manifest_hash, staging_tree_hash
    )
    copy_installer_scripts(root, package)
    manifest = build_manifest(
        package, overlay_entries, staging_manifest_hash, staging_tree_hash
    )
    make_zip(package, zip_path)
    checksum = outputs / f"{PACKAGE_NAME}.zip.sha256"
    write_text_crlf(checksum, f"{sha256(zip_path)}  {zip_path.name}\n", "ascii")
    print(
        json.dumps(
            {
                "package_dir": str(package),
                "zip": str(zip_path),
                "zip_size_bytes": zip_path.stat().st_size,
                "zip_sha256": sha256(zip_path),
                "overlay_file_count": manifest["overlay_file_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
