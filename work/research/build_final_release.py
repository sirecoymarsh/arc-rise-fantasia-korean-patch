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
PACKAGE_NAME = "Arc_Rise_Fantasia_Korean_Patch_v1.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


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
        "part_names": 3,
        "skill_names": 563,
        "total_units": 836,
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
    readme = f"""# 아크 라이즈 판타지아 한국어 패치 v1.0

## 대상

- 게임 ID: `{GAME_ID}`
- 일본판 원본 RVZ SHA-256: `{SOURCE_RVZ_SHA256}`
- 일본어 음성 유지
- 원본 RVZ는 수정하지 않는 Riivolution/Dolphin 오버레이 방식
- 전투 몬스터명 270개, 보스 부위명 3개, 몬스터 기술명 563회(고유 기술명 209개) 한국어화

## 설치

1. Dolphin을 종료합니다.
2. PowerShell에서 다음을 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\\Install-ARF-KO.ps1 `
  -SourceRvz 'D:\\Games\\Arc Rise Fantasia (Japan).rvz' `
  -TargetRoot 'D:\\DolphinUser\\Load'
```

`TargetRoot`에는 Riivolution SD 구조를 둘 폴더를 지정합니다. 설치기는 패키지와
원본 해시를 확인한 뒤 `riivolution` 및 `arc_rise_fantasia_ko` 폴더를 복사합니다.

## 복원

```powershell
powershell -ExecutionPolicy Bypass -File .\\Restore-ARF-KO.ps1
```

설치 전에 같은 경로에 있던 파일은 외부 백업에서 복구되고, 새로 추가된 파일은
제거됩니다. 설치 상태는 `%LOCALAPPDATA%\\ArcRiseFantasiaKO`에 기록됩니다.

## 무결성 확인

```powershell
powershell -ExecutionPolicy Bypass -File .\\Verify-ARF-KO.ps1
```

번역·교정·윤문·용어 통일에는 Codex 내부 모델만 사용했습니다. 외부 번역
서비스나 외부 생성 모델은 사용하지 않았습니다.

## 오프닝 영상 안정성

`Movie/RAY_OP_02.sfd`는 일본판 원본을 그대로 사용합니다. 개발 중 전체 영상을
재인코딩한 후보에서 프레임 타임스탬프 역행과 실제 정지가 확인되어 릴리스에서는
해당 영상 오버레이를 제외했습니다. 따라서 오프닝 중 게임 제목 한 줄은 일본어로
남지만, 영상과 음성은 원본과 동일하게 재생됩니다.
"""
    (package / "README_KO.md").write_text(readme, encoding="utf-8")
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
        + int(staging_manifest.get("counts", {}).get("battle_enemy_unique_skill_names", 0)),
        "translation_occurrences": int(staging_manifest.get("counts", {}).get("catalog_occurrences", 0))
        + int(staging_manifest.get("counts", {}).get("battle_enemy_translation_occurrences", 0)),
        "battle_enemy": {
            "entries": staging_manifest.get("counts", {}).get("battle_enemy_entries"),
            "display_name_occurrences": staging_manifest.get("counts", {}).get("battle_enemy_display_name_occurrences"),
            "skill_name_occurrences": staging_manifest.get("counts", {}).get("battle_enemy_skill_name_occurrences"),
            "unique_skill_names": staging_manifest.get("counts", {}).get("battle_enemy_unique_skill_names"),
        },
        "reviewed_batches": 149,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "delivery": "reversible Riivolution-style overlay",
        "staging_summary": public_staging,
    }
    (package / "PROVENANCE.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def copy_installer_scripts(root: Path, package: Path) -> None:
    script_dir = root / "work" / "release_scripts"
    for name in ("Install-ARF-KO.ps1", "Restore-ARF-KO.ps1", "Verify-ARF-KO.ps1"):
        source = script_dir / name
        if not source.is_file():
            raise RuntimeError(f"missing release script: {source}")
        # Windows PowerShell 5.1 requires a BOM to parse non-ASCII source
        # reliably; emit UTF-8-SIG regardless of the workspace encoding.
        (package / name).write_text(
            source.read_text(encoding="utf-8-sig"), encoding="utf-8-sig"
        )


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
    (package / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
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
    checksum.write_text(f"{sha256(zip_path)}  {zip_path.name}\n", encoding="ascii")
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
