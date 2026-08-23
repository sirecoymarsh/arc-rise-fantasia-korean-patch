from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

VERSION = "1.1.0"
EXPECTED_PATCH_MANIFEST_SHA256 = (
    "7CAEED6D8B6B7CAC0EE4C85AB9282154F4944F2A2A4C293818B5F2B62C6B09C2"
)
EXPECTED_DELTA_BYTES = 465_404_088
PRODUCT_DIR = f"ArcRiseFantasia-Korean-ROM-Patcher-v{VERSION}"


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest().upper()


def safe_remove_tree(path: Path, required_parent: Path) -> None:
    resolved = path.resolve()
    parent = required_parent.resolve()
    if resolved == parent or parent not in resolved.parents:
        raise ValueError(f"refusing to remove path outside build root: {resolved}")
    if path.exists():
        shutil.rmtree(path)


def copy_file(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def compile_app(repo: Path, output: Path) -> None:
    csc = Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")
    sources = [
        repo / "work/rom_patcher/src/PatcherCore.cs",
        repo / "work/rom_patcher/src/Program.cs",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(csc),
        "/nologo",
        "/target:winexe",
        "/platform:anycpu",
        "/optimize+",
        "/debug-",
        f"/out:{output}",
        "/reference:System.dll",
        "/reference:System.Core.dll",
        "/reference:System.Drawing.dll",
        "/reference:System.Windows.Forms.dll",
        "/reference:System.Web.Extensions.dll",
        *(str(path) for path in sources),
    ]
    proc = subprocess.run(command, text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stdout + proc.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-zip", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    build_root = repo / "work/rom_patcher/build"
    dist_root = repo / "work/rom_patcher/dist"
    stage = dist_root / PRODUCT_DIR
    safe_remove_tree(stage, dist_root)
    stage.mkdir(parents=True, exist_ok=True)

    payload_source = build_root / "payload"
    patch_manifest_source = payload_source / "patch_manifest.json"
    if sha256_file(patch_manifest_source) != EXPECTED_PATCH_MANIFEST_SHA256:
        raise ValueError("patch manifest hash changed; update the pinned application contract")
    manifest = json.loads(patch_manifest_source.read_text(encoding="utf-8"))
    if manifest["game_id"] != "RPJJ99" or len(manifest["entries"]) != 722:
        raise ValueError("unexpected patch manifest identity/count")
    if manifest["totals"]["delta_bytes"] != EXPECTED_DELTA_BYTES:
        raise ValueError("unexpected total delta size")
    if not all(row["roundtrip_verified"] for row in manifest["entries"]):
        raise ValueError("payload contains a delta without roundtrip proof")

    app_build = build_root / "app/ArcRiseFantasiaKoreanRomPatcher.exe"
    compile_app(repo, app_build)
    copy_file(app_build, stage / "ArcRiseFantasiaKoreanRomPatcher.exe")
    shutil.copytree(payload_source, stage / "payload")

    dolphin_root = repo / "work/tools/dolphin-2603a/Dolphin-x64"
    xdelta_root = (
        repo / "work/tools/xdelta3-3.2.0/extracted/"
        "xdelta3-3.2.0-windows-x86_64"
    )
    wit_root = (
        repo / "work/tools/wit-v3.05a-r8638/extracted/"
        "wit-v3.05a-r8638-cygwin64"
    )
    copy_file(dolphin_root / "DolphinTool.exe", stage / "tools/DolphinTool.exe")
    copy_file(dolphin_root / "COPYING", stage / "licenses/Dolphin-COPYING.txt")
    copy_file(xdelta_root / "xdelta3.exe", stage / "tools/xdelta3.exe")
    copy_file(
        repo / "work/tools/xdelta3-3.2.0/LICENSE",
        stage / "licenses/Xdelta3-Apache-2.0.txt",
    )
    for name in (
        "wit.exe",
        "cygcrypto-1.1.dll",
        "cygncursesw-10.dll",
        "cygwin1.dll",
        "cygz.dll",
    ):
        copy_file(wit_root / "bin" / name, stage / "tools/wit" / name)
    copy_file(wit_root / "gpl-2.0.txt", stage / "licenses/WIT-GPL-2.0.txt")

    usage = """아크 라이즈 판타지아 한국어 롬 패처 v1.1.0

사용법
1. ZIP의 압축을 완전히 풉니다.
2. ArcRiseFantasiaKoreanRomPatcher.exe를 더블클릭합니다.
3. 일본판 RPJJ99 원본 .rvz 또는 .iso 파일을 선택합니다.
4. 한국어판을 저장할 위치와 RVZ/ISO 형식을 선택합니다.
5. '한국어판 만들기'를 누르고 완료될 때까지 기다립니다.

중요
- 원본 게임 파일은 수정하지 않습니다. 별도의 한국어판 복사본을 만듭니다.
- RVZ 출력에는 약 15 GiB, ISO 출력에는 약 11 GiB의 여유 공간이 필요합니다.
- 출력 게임 ID는 RPJJ99로 유지되므로 기존 RPJJ99 세이브를 그대로 사용합니다.
- Dolphin/Riivolution/PowerShell 설치나 명령 입력은 필요하지 않습니다.
- 실기용으로는 ISO 출력을 선택한 뒤 사용하는 USB 로더의 방식에 맞게 넣으면 됩니다.
- 실패하면 원본은 그대로이며 임시 파일은 자동 정리됩니다.
- 완료되면 출력 옆에 .patch-report.json 검증 보고서가 함께 생성됩니다.
"""
    (stage / "사용법.txt").write_text(usage, encoding="utf-8-sig")

    notices = """Third-party notices

DolphinTool 2603a
- Project: https://dolphin-emu.org/
- Source: https://github.com/dolphin-emu/dolphin
- The included COPYING notice is in licenses/Dolphin-COPYING.txt.

Xdelta 3.2.0
- Project/source: https://github.com/jmacd/xdelta
- License: Apache License 2.0
- License text: licenses/Xdelta3-Apache-2.0.txt

Wiimms ISO Tools (WIT) 3.05a r8638
- Project/source: https://wit.wiimm.de/
- License: GNU GPL version 2
- License text: licenses/WIT-GPL-2.0.txt

The payload directory contains VCDIFF deltas only. It contains neither a
complete original game image nor a complete patched game image.
"""
    (stage / "THIRD_PARTY_NOTICES.txt").write_text(notices, encoding="utf-8")

    forbidden_extensions = {".rvz", ".iso", ".wbfs", ".wia", ".gcz", ".ciso"}
    forbidden = [
        str(path.relative_to(stage))
        for path in stage.rglob("*")
        if path.is_file() and path.suffix.lower() in forbidden_extensions
    ]
    if forbidden:
        raise ValueError(f"forbidden complete-image extensions in package: {forbidden}")

    file_rows = []
    for path in sorted(
        (p for p in stage.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(stage).as_posix().lower(),
    ):
        rel = path.relative_to(stage).as_posix()
        file_rows.append(
            {"path": rel, "size": path.stat().st_size, "sha256": sha256_file(path)}
        )

    sums = "\n".join(f"{row['sha256']} *{row['path']}" for row in file_rows) + "\n"
    (stage / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    release_manifest = {
        "schema": "arf-rom-patcher-release-v1",
        "version": VERSION,
        "game_id": "RPJJ99",
        "entry_count": 722,
        "delta_bytes": EXPECTED_DELTA_BYTES,
        "patch_manifest_sha256": EXPECTED_PATCH_MANIFEST_SHA256,
        "contains_complete_game_image": False,
        "supported_inputs": ["RVZ", "ISO"],
        "supported_outputs": ["RVZ", "ISO"],
        "files_excluding_release_metadata": file_rows,
    }
    (stage / "release_manifest.json").write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    zip_path = dist_root / f"{PRODUCT_DIR}.zip"
    if not args.no_zip:
        zip_path.unlink(missing_ok=True)
        with zipfile.ZipFile(zip_path, "w", allowZip64=True) as archive:
            for path in sorted(
                (p for p in stage.rglob("*") if p.is_file()),
                key=lambda p: p.relative_to(stage).as_posix().lower(),
            ):
                arcname = f"{stage.name}/{path.relative_to(stage).as_posix()}"
                compress = (
                    zipfile.ZIP_STORED
                    if path.suffix.lower() == ".vcdiff"
                    else zipfile.ZIP_DEFLATED
                )
                archive.write(path, arcname, compress_type=compress)
        zip_sha = sha256_file(zip_path)
        (dist_root / f"{zip_path.name}.sha256").write_text(
            f"{zip_sha} *{zip_path.name}\n", encoding="ascii"
        )
    else:
        zip_sha = None

    report = {
        "valid": True,
        "stage": str(stage),
        "stage_file_count": sum(1 for p in stage.rglob("*") if p.is_file()),
        "stage_bytes": sum(p.stat().st_size for p in stage.rglob("*") if p.is_file()),
        "zip": str(zip_path) if not args.no_zip else None,
        "zip_size": zip_path.stat().st_size if not args.no_zip else None,
        "zip_sha256": zip_sha,
        "patch_manifest_sha256": EXPECTED_PATCH_MANIFEST_SHA256,
        "delta_entries": len(manifest["entries"]),
        "delta_roundtrip_verified": True,
        "contains_complete_game_image": False,
    }
    (dist_root / "rom_patcher_release_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
