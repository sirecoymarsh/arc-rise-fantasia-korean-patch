#!/usr/bin/env python3
"""Validate the final ARF Korean Riivolution release directory and ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


EXPECTED_SOURCE = "4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5"
EXPECTED_GAME_ID = "RPJJ99"
PACKAGE_NAME = "Arc_Rise_Fantasia_Korean_Patch_v1.0"
TEXT_EXTENSIONS = {".md", ".json", ".ps1", ".txt", ".xml"}
PROHIBITED_PUBLIC_PATTERNS = [
    re.compile(r"C:\\Users\\", re.I),
    re.compile(r"CadriacLord", re.I),
    re.compile(r"Documents\\Codex", re.I),
    re.compile(r"P:\\AI", re.I),
    re.compile(r"F:\\DOWN", re.I),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest().upper()


def compare_trees(left: Path, right: Path) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    left_files = {
        path.relative_to(left).as_posix(): path
        for path in left.rglob("*")
        if path.is_file()
    }
    right_files = {
        path.relative_to(right).as_posix(): path
        for path in right.rglob("*")
        if path.is_file()
    }
    if set(left_files) != set(right_files):
        errors.append(
            {
                "code": "staging_release_file_set_mismatch",
                "missing_from_release": sorted(set(left_files) - set(right_files)),
                "extra_in_release": sorted(set(right_files) - set(left_files)),
            }
        )
    changed = [
        relative
        for relative in sorted(left_files.keys() & right_files.keys())
        if sha256(left_files[relative]) != sha256(right_files[relative])
    ]
    if changed:
        errors.append(
            {
                "code": "staging_release_hash_mismatch",
                "count": len(changed),
                "paths": changed[:50],
            }
        )
    return errors


def safe_name(name: str, package_name: str | None = None) -> bool:
    pure = PurePosixPath(name)
    if pure.is_absolute() or ".." in pure.parts or "" in pure.parts:
        return False
    if package_name is not None and (not pure.parts or pure.parts[0] != package_name):
        return False
    return True


def validate_tree(package: Path, manifest: dict[str, object]) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    actual = {
        path.relative_to(package).as_posix(): path
        for path in package.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
    }
    declared = {str(item["path"]): item for item in manifest.get("files", [])}
    if set(actual) != set(declared):
        errors.append(
            {
                "code": "manifest_file_set_mismatch",
                "missing": sorted(set(declared) - set(actual)),
                "extra": sorted(set(actual) - set(declared)),
            }
        )
    for relative, path in actual.items():
        if not safe_name(relative):
            errors.append({"code": "unsafe_tree_path", "path": relative})
            continue
        item = declared.get(relative)
        if item is None:
            continue
        if path.stat().st_size != int(item["size_bytes"]) or sha256(path) != str(item["sha256"]).upper():
            errors.append({"code": "file_hash_or_size_mismatch", "path": relative})
        if path.suffix.lower() in TEXT_EXTENSIONS:
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                if not relative.startswith("payload/riivolution_sd/"):
                    errors.append({"code": "public_text_not_utf8", "path": relative})
                continue
            if not relative.startswith("payload/riivolution_sd/"):
                for pattern in PROHIBITED_PUBLIC_PATTERNS:
                    if pattern.search(text):
                        errors.append(
                            {
                                "code": "public_absolute_or_private_path",
                                "path": relative,
                                "pattern": pattern.pattern,
                            }
                        )
    overlay_actual = {
        path for path in actual if path.startswith("payload/riivolution_sd/")
    }
    game_replacement_actual = {
        path
        for path in overlay_actual
        if not path.startswith("payload/riivolution_sd/riivolution/")
    }
    overlay_declared = {
        str(item["path"])
        for item in manifest.get("files", [])
        if item.get("role") == "riivolution_overlay"
    }
    if overlay_actual != overlay_declared:
        errors.append({"code": "overlay_role_set_mismatch"})
    if len(overlay_actual) != int(manifest.get("overlay_file_count", -1)):
        errors.append(
            {
                "code": "overlay_count_mismatch",
                "actual": len(overlay_actual),
                "declared": manifest.get("overlay_file_count"),
            }
        )
    if len(game_replacement_actual) != int(manifest.get("game_replacement_file_count", -1)):
        errors.append(
            {
                "code": "game_replacement_count_mismatch",
                "actual": len(game_replacement_actual),
                "declared": manifest.get("game_replacement_file_count"),
            }
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("checksum_path", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--staging-manifest", type=Path)
    parser.add_argument("--staging-root", type=Path)
    args = parser.parse_args()
    package = args.package_dir.resolve()
    errors: list[dict[str, object]] = []
    manifest_path = package / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_fields = {
        "schema": "arf-ko-riivolution-release-v1",
        "package": PACKAGE_NAME,
        "game_id": EXPECTED_GAME_ID,
        "source_rvz_sha256": EXPECTED_SOURCE,
        "source_media_included": False,
        "source_media_write_policy": "read-only; never overwrite",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "runtime_ready_release": True,
    }
    for key, expected in expected_fields.items():
        if manifest.get(key) != expected:
            errors.append(
                {
                    "code": "manifest_field_mismatch",
                    "field": key,
                    "expected": expected,
                    "actual": manifest.get(key),
                }
            )
    errors.extend(validate_tree(package, manifest))
    zip_hash = sha256(args.zip_path)
    tokens = args.checksum_path.read_text(encoding="ascii").split()
    if not tokens or tokens[0].upper() != zip_hash:
        errors.append({"code": "zip_checksum_sidecar_mismatch"})
    with zipfile.ZipFile(args.zip_path) as archive:
        bad = archive.testzip()
        if bad:
            errors.append({"code": "zip_crc_failure", "member": bad})
        names = {info.filename for info in archive.infolist() if not info.is_dir()}
        unsafe = sorted(name for name in names if not safe_name(name, package.name))
        if unsafe:
            errors.append({"code": "unsafe_zip_members", "members": unsafe})
        expected = {
            (PurePosixPath(package.name) / path.relative_to(package).as_posix()).as_posix()
            for path in package.rglob("*")
            if path.is_file()
        }
        if names != expected:
            errors.append(
                {
                    "code": "zip_file_set_mismatch",
                    "missing": sorted(expected - names),
                    "extra": sorted(names - expected),
                }
            )
        with tempfile.TemporaryDirectory(prefix="arf-ko-release-") as temporary:
            archive.extractall(temporary)
            extracted = Path(temporary) / package.name
            extracted_manifest = json.loads((extracted / "MANIFEST.json").read_text(encoding="utf-8"))
            extracted_errors = validate_tree(extracted, extracted_manifest)
            errors.extend(
                {"code": "extracted_" + str(item.get("code")), **{k: v for k, v in item.items() if k != "code"}}
                for item in extracted_errors
            )
    staging_summary: dict[str, object] = {}
    staging_manifest_hash: str | None = None
    staging_tree_hash: str | None = None
    if args.staging_manifest and not args.staging_manifest.is_file():
        errors.append(
            {
                "code": "staging_manifest_missing",
                "path": str(args.staging_manifest.resolve()),
            }
        )
    if args.staging_manifest and args.staging_manifest.is_file():
        staging_summary = json.loads(args.staging_manifest.read_text(encoding="utf-8"))
        staging_manifest_hash = sha256(args.staging_manifest)
        if (
            str(manifest.get("staging_manifest_sha256", "")).upper()
            != staging_manifest_hash
        ):
            errors.append(
                {
                    "code": "release_staging_manifest_hash_mismatch",
                    "declared": manifest.get("staging_manifest_sha256"),
                    "actual": staging_manifest_hash,
                }
            )
        declared = (
            staging_summary.get("counts", {}).get("staged_physical_files")
            or staging_summary.get("riivolution", {}).get("file_count")
            or staging_summary.get("overlay_file_count")
            or staging_summary.get("file_count")
        )
        if declared is not None and int(declared) != int(manifest.get("game_replacement_file_count", -1)):
            errors.append(
                {
                    "code": "staging_release_count_mismatch",
                    "staging": declared,
                    "release": manifest.get("game_replacement_file_count"),
                }
            )
    if args.staging_root and not args.staging_root.is_dir():
        errors.append(
            {
                "code": "staging_root_missing",
                "path": str(args.staging_root.resolve()),
            }
        )
    if args.staging_root and args.staging_root.is_dir():
        staging_root = args.staging_root.resolve()
        staging_tree_hash = tree_sha256(staging_root)
        if str(manifest.get("staging_tree_sha256", "")).upper() != staging_tree_hash:
            errors.append(
                {
                    "code": "release_staging_tree_hash_mismatch",
                    "declared": manifest.get("staging_tree_sha256"),
                    "actual": staging_tree_hash,
                }
            )
        errors.extend(
            compare_trees(staging_root, package / "payload" / "riivolution_sd")
        )
    report = {
        "schema": "arf-ko-final-release-validation-v1",
        "package_dir": str(package),
        "zip_path": str(args.zip_path.resolve()),
        "zip_size_bytes": args.zip_path.stat().st_size,
        "zip_sha256": zip_hash,
        "manifest_sha256": sha256(manifest_path),
        "staging_manifest_sha256": staging_manifest_hash,
        "staging_tree_sha256": staging_tree_hash,
        "overlay_file_count": manifest.get("overlay_file_count"),
        "game_replacement_file_count": manifest.get("game_replacement_file_count"),
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
