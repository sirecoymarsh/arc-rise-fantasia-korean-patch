from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath


FORBIDDEN_IMAGE_EXTENSIONS = {".rvz", ".iso", ".wbfs", ".wia", ".gcz", ".ciso"}
TEXT_EXTENSIONS = {".json", ".txt"}
LEAK_MARKERS = (b"P:\\\\", b"C:\\\\Users\\\\", b"CadriacLord", b"AppData\\\\")


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_size):
            digest.update(block)
    return digest.hexdigest().upper()


def safe_remove_tree(path: Path, required_parent: Path) -> None:
    resolved = path.resolve()
    parent = required_parent.resolve()
    if resolved == parent or parent not in resolved.parents:
        raise ValueError(f"refusing to remove path outside validation root: {resolved}")
    if path.exists():
        shutil.rmtree(path)


def validate_member(info: zipfile.ZipInfo) -> None:
    name = PurePosixPath(info.filename)
    if name.is_absolute() or ".." in name.parts or any(":" in part for part in name.parts):
        raise ValueError(f"unsafe ZIP member: {info.filename}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ValueError(f"symlink ZIP member: {info.filename}")


def parse_sums(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(" *", 1)
        rows[rel] = digest.upper()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("extract_root", type=Path)
    parser.add_argument("report_path", type=Path)
    args = parser.parse_args()

    zip_path = args.zip_path.resolve()
    extract_root = args.extract_root.resolve()
    report_path = args.report_path.resolve()
    safe_remove_tree(extract_root, extract_root.parent)
    extract_root.mkdir(parents=True)

    with zipfile.ZipFile(zip_path, "r", allowZip64=True) as archive:
        members = archive.infolist()
        for info in members:
            validate_member(info)
        bad_crc_member = archive.testzip()
        if bad_crc_member is not None:
            raise ValueError(f"ZIP CRC failure: {bad_crc_member}")
        roots = {PurePosixPath(info.filename).parts[0] for info in members}
        if len(roots) != 1:
            raise ValueError(f"expected one package root, got {sorted(roots)}")
        archive.extractall(extract_root)

    package_root = extract_root / next(iter(roots))
    sums = parse_sums(package_root / "SHA256SUMS.txt")
    manifest = json.loads((package_root / "release_manifest.json").read_text(encoding="utf-8"))
    manifest_rows = {row["path"]: row for row in manifest["files_excluding_release_metadata"]}
    actual_files = {
        path.relative_to(package_root).as_posix(): path
        for path in package_root.rglob("*")
        if path.is_file()
    }
    metadata = {"SHA256SUMS.txt", "release_manifest.json"}
    if set(sums) != set(actual_files) - metadata:
        raise ValueError("SHA256SUMS file set does not match extracted package")
    if set(manifest_rows) != set(sums):
        raise ValueError("release manifest file set does not match SHA256SUMS")

    mismatches: list[str] = []
    for rel, expected in sums.items():
        path = actual_files[rel]
        actual = sha256_file(path)
        row = manifest_rows[rel]
        if actual != expected or actual != row["sha256"] or path.stat().st_size != row["size"]:
            mismatches.append(rel)

    forbidden = sorted(rel for rel in actual_files if Path(rel).suffix.lower() in FORBIDDEN_IMAGE_EXTENSIONS)
    leaks: list[str] = []
    for rel, path in actual_files.items():
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        data = path.read_bytes()
        if any(marker.lower() in data.lower() for marker in LEAK_MARKERS):
            leaks.append(rel)

    exe_rel = "ArcRiseFantasiaKoreanRomPatcher.exe"
    report = {
        "valid": not mismatches and not forbidden and not leaks,
        "zip_path": str(zip_path),
        "zip_size": zip_path.stat().st_size,
        "zip_sha256": sha256_file(zip_path),
        "zip_crc_failure": bad_crc_member,
        "zip_member_count": len(members),
        "package_root": str(package_root),
        "extracted_file_count": len(actual_files),
        "manifest_file_count": len(manifest_rows),
        "hash_or_size_mismatches": mismatches,
        "forbidden_complete_image_files": forbidden,
        "absolute_path_or_username_leaks": leaks,
        "contains_complete_game_image": manifest["contains_complete_game_image"],
        "delta_entry_count": manifest["entry_count"],
        "patch_manifest_sha256": manifest["patch_manifest_sha256"],
        "patcher_exe_sha256": sha256_file(actual_files[exe_rel]),
    }
    if manifest["contains_complete_game_image"] or manifest["entry_count"] != 722:
        report["valid"] = False
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
