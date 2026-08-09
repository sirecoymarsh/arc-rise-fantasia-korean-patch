#!/usr/bin/env python3
"""Validate the source-free ARF localization checkpoint directory and ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


PROHIBITED_GAME_EXTENSIONS = {
    ".rvz",
    ".iso",
    ".wbfs",
    ".wia",
    ".vol",
    ".wtm",
    ".bin",
    ".dat",
    ".bscr",
    ".cxd",
    ".vld",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("checksum_path", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    errors: list[dict[str, object]] = []
    manifest_path = args.package_dir / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contains_original_game_data") is not False:
        errors.append({"code": "manifest_original_data_flag_not_false"})
    if manifest.get("runtime_ready_release") is not False:
        errors.append({"code": "manifest_runtime_ready_flag_not_false"})
    if manifest.get("translation_engine_policy") != "Codex internal models only":
        errors.append({"code": "translation_policy_mismatch"})
    if manifest.get("external_translation_models_or_apis_used") is not False:
        errors.append({"code": "external_translation_policy_mismatch"})
    if manifest.get("independent_static_audit_status") != "PASS_STATIC_RUNTIME_PENDING":
        errors.append({"code": "independent_static_audit_status_mismatch"})
    if manifest.get("missing_optional_sources"):
        errors.append(
            {
                "code": "package_sources_missing",
                "files": manifest.get("missing_optional_sources"),
            }
        )

    actual_files = {
        path.relative_to(args.package_dir).as_posix(): path
        for path in args.package_dir.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
    }
    manifest_files = {str(item["path"]): item for item in manifest["files"]}
    if set(actual_files) != set(manifest_files):
        errors.append(
            {
                "code": "manifest_file_set_mismatch",
                "missing": sorted(set(manifest_files) - set(actual_files)),
                "extra": sorted(set(actual_files) - set(manifest_files)),
            }
        )
    bad_hashes = []
    for relative, path in actual_files.items():
        item = manifest_files.get(relative)
        if item is None:
            continue
        actual_hash = sha256(path)
        if int(item["size_bytes"]) != path.stat().st_size or str(
            item["sha256"]
        ).upper() != actual_hash:
            bad_hashes.append(relative)
    if bad_hashes:
        errors.append({"code": "manifest_hash_or_size_mismatch", "files": bad_hashes})

    prohibited = sorted(
        relative
        for relative in actual_files
        if PurePosixPath(relative).suffix.lower() in PROHIBITED_GAME_EXTENSIONS
    )
    if prohibited:
        errors.append({"code": "prohibited_game_binary_in_package", "files": prohibited})

    zip_sha = sha256(args.zip_path)
    checksum_tokens = args.checksum_path.read_text(encoding="ascii").split()
    if not checksum_tokens or checksum_tokens[0].upper() != zip_sha:
        errors.append({"code": "zip_checksum_sidecar_mismatch"})

    package_root = args.package_dir.name
    expected_zip_names = {
        (PurePosixPath(package_root) / relative).as_posix()
        for relative in actual_files
    }
    expected_zip_names.add(f"{package_root}/MANIFEST.json")
    with zipfile.ZipFile(args.zip_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            errors.append({"code": "zip_crc_failure", "member": bad_member})
        zip_names = {item.filename for item in archive.infolist() if not item.is_dir()}
        unsafe_names = sorted(
            name
            for name in zip_names
            if PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or not name.startswith(f"{package_root}/")
        )
        if unsafe_names:
            errors.append({"code": "unsafe_zip_member", "files": unsafe_names})
        if zip_names != expected_zip_names:
            errors.append(
                {
                    "code": "zip_file_set_mismatch",
                    "missing": sorted(expected_zip_names - zip_names),
                    "extra": sorted(zip_names - expected_zip_names),
                }
            )

    report = {
        "schema": "arf-ko-development-checkpoint-validation-v1",
        "package_dir": str(args.package_dir.resolve()),
        "zip_path": str(args.zip_path.resolve()),
        "zip_size_bytes": args.zip_path.stat().st_size,
        "zip_sha256": zip_sha,
        "manifest_files": len(manifest_files),
        "prohibited_game_binary_count": len(prohibited),
        "zip_crc_ok": not any(item["code"] == "zip_crc_failure" for item in errors),
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
