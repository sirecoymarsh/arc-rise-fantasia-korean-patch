from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SCHEMA = "arf-rom-patcher-delta-v1"
GAME_ID = "RPJJ99"
EXPECTED_MAIN_DOL_SHA256 = "4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC"
EXPECTED_FILE_COUNT = 721
EXPECTED_MEMORY_RULES = 945


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest().upper()


def safe_rel(value: str) -> Path:
    text = value.replace("\\", "/")
    rel = Path(*[p for p in text.split("/") if p not in ("", ".")])
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe relative path: {value!r}")
    return rel


def dol_sections(data: bytes) -> list[tuple[int, int, int]]:
    if len(data) < 0x100:
        raise ValueError("main.dol is smaller than its header")
    file_offsets = list(struct.unpack(">7I", data[0x00:0x1C]))
    file_offsets += list(struct.unpack(">11I", data[0x1C:0x48]))
    addresses = list(struct.unpack(">7I", data[0x48:0x64]))
    addresses += list(struct.unpack(">11I", data[0x64:0x90]))
    sizes = list(struct.unpack(">7I", data[0x90:0xAC]))
    sizes += list(struct.unpack(">11I", data[0xAC:0xD8]))
    result: list[tuple[int, int, int]] = []
    for file_offset, address, size in zip(file_offsets, addresses, sizes):
        if size:
            if file_offset + size > len(data):
                raise ValueError(
                    f"DOL section exceeds file: file=0x{file_offset:X}, "
                    f"address=0x{address:X}, size=0x{size:X}"
                )
            result.append((address, file_offset, size))
    return result


def address_to_file_offset(
    sections: list[tuple[int, int, int]], address: int, length: int
) -> int:
    for section_address, section_file_offset, section_size in sections:
        if (
            address >= section_address
            and address + length <= section_address + section_size
        ):
            return section_file_offset + (address - section_address)
    raise ValueError(
        f"memory rule is outside DOL-backed sections: "
        f"address=0x{address:08X}, length={length}"
    )


def bake_main_dol(source: Path, xml_path: Path, output: Path) -> dict[str, Any]:
    source_sha = sha256_file(source)
    if source_sha != EXPECTED_MAIN_DOL_SHA256:
        raise ValueError(
            f"source main.dol SHA-256 mismatch: expected "
            f"{EXPECTED_MAIN_DOL_SHA256}, got {source_sha}"
        )

    raw = bytearray(source.read_bytes())
    sections = dol_sections(raw)
    memories = list(ET.parse(xml_path).getroot().iter("memory"))
    if len(memories) != EXPECTED_MEMORY_RULES:
        raise ValueError(
            f"unexpected memory rule count: expected {EXPECTED_MEMORY_RULES}, "
            f"got {len(memories)}"
        )

    touched: list[tuple[int, int, int]] = []
    for index, node in enumerate(memories):
        offset_text = node.attrib.get("offset")
        value_text = node.attrib.get("value")
        if not offset_text or value_text is None:
            raise ValueError(f"memory rule {index} lacks offset/value")
        address = int(offset_text, 16)
        value = bytes.fromhex(value_text)
        file_offset = address_to_file_offset(sections, address, len(value))
        raw[file_offset : file_offset + len(value)] = value
        touched.append((address, file_offset, len(value)))

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".partial")
    temp.write_bytes(raw)
    os.replace(temp, output)

    return {
        "source_sha256": source_sha,
        "output_sha256": sha256_file(output),
        "source_size": source.stat().st_size,
        "output_size": output.stat().st_size,
        "memory_rule_count": len(memories),
        "total_written_bytes": sum(length for _, _, length in touched),
        "min_address": f"0x{min(address for address, _, _ in touched):08X}",
        "max_address_end": (
            f"0x{max(address + length for address, _, length in touched):08X}"
        ),
    }


def run_checked(args: list[str]) -> None:
    proc = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if proc.returncode:
        command = " ".join(args[:4])
        raise RuntimeError(
            f"command failed ({proc.returncode}): {command}\n{proc.stdout}"
        )


def build_one(
    entry: dict[str, Any],
    xdelta: Path,
    delta_root: Path,
    verify_root: Path,
    force: bool,
) -> dict[str, Any]:
    logical = entry["logical_path"]
    source = Path(entry["source_path"])
    target = Path(entry["target_path"])
    delta_rel = safe_rel(logical + ".vcdiff")
    delta = delta_root / delta_rel
    delta.parent.mkdir(parents=True, exist_ok=True)

    source_sha = sha256_file(source)
    target_sha = sha256_file(target)
    if source_sha != entry["source_sha256"]:
        raise ValueError(
            f"{logical}: source hash mismatch: expected "
            f"{entry['source_sha256']}, got {source_sha}"
        )
    if target_sha != entry["output_sha256"]:
        raise ValueError(
            f"{logical}: output hash mismatch: expected "
            f"{entry['output_sha256']}, got {target_sha}"
        )
    if source.stat().st_size != entry["source_size"]:
        raise ValueError(f"{logical}: source size mismatch")
    if target.stat().st_size != entry["output_size"]:
        raise ValueError(f"{logical}: output size mismatch")

    if force or not delta.exists():
        partial = delta.with_suffix(delta.suffix + ".partial")
        partial.unlink(missing_ok=True)
        run_checked(
            [
                str(xdelta),
                "-9",
                "-S",
                "lzma",
                "-e",
                "-f",
                "-s",
                str(source),
                str(target),
                str(partial),
            ]
        )
        os.replace(partial, delta)

    verify = verify_root / safe_rel(logical)
    verify.parent.mkdir(parents=True, exist_ok=True)
    verify.unlink(missing_ok=True)
    run_checked(
        [
            str(xdelta),
            "-d",
            "-f",
            "-s",
            str(source),
            str(delta),
            str(verify),
        ]
    )
    decoded_sha = sha256_file(verify)
    decoded_size = verify.stat().st_size
    verify.unlink()
    if decoded_sha != target_sha or decoded_size != target.stat().st_size:
        raise ValueError(
            f"{logical}: decoded output mismatch: "
            f"sha={decoded_sha}, size={decoded_size}"
        )

    return {
        "logical_path": logical.replace("\\", "/"),
        "delta_path": ("deltas/" + delta_rel.as_posix()),
        "source_sha256": source_sha,
        "output_sha256": target_sha,
        "delta_sha256": sha256_file(delta),
        "source_size": source.stat().st_size,
        "output_size": target.stat().st_size,
        "delta_size": delta.stat().st_size,
        "roundtrip_verified": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build copyright-safe Xdelta payload for the RPJJ99 ROM patcher."
    )
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 8:
        parser.error("--jobs must be in the range 1..8")

    repo = Path(__file__).resolve().parents[2]
    staging_manifest_path = (
        repo / "work/final_runtime_staging/staging_manifest.json"
    )
    staging = json.loads(staging_manifest_path.read_text(encoding="utf-8"))
    if staging.get("game_id") != GAME_ID:
        raise ValueError("staging game ID is not RPJJ99")
    staged_files = staging["static_validation"]["staged_files"]
    if len(staged_files) != EXPECTED_FILE_COUNT:
        raise ValueError(
            f"expected {EXPECTED_FILE_COUNT} staged files, got {len(staged_files)}"
        )

    source_data = repo / "work/disc_extracted/DATA"
    patch_root = (
        repo
        / "work/final_runtime_staging/riivolution_sd/"
        / "arc_rise_fantasia_ko_full/files"
    )
    xml_path = (
        repo
        / "work/final_runtime_staging/riivolution_sd/riivolution/"
        / "arc_rise_fantasia_ko_full.xml"
    )
    xdelta = (
        repo
        / "work/tools/xdelta3-3.2.0/extracted/"
        / "xdelta3-3.2.0-windows-x86_64/xdelta3.exe"
    )
    build_root = repo / "work/rom_patcher/build"
    payload_root = build_root / "payload"
    delta_root = payload_root / "deltas"
    verify_root = build_root / "verify"
    main_target = build_root / "intermediate/main.dol"

    for required in (
        staging_manifest_path,
        source_data / "sys/main.dol",
        patch_root,
        xml_path,
        xdelta,
    ):
        if not required.exists():
            raise FileNotFoundError(required)

    started = time.time()
    main_info = bake_main_dol(
        source_data / "sys/main.dol", xml_path, main_target
    )
    entries: list[dict[str, Any]] = []
    non_ascii_paths: list[str] = []

    for row in staged_files:
        rel = safe_rel(row["physical_path"])
        logical = "DATA/files/" + rel.as_posix()
        if not logical.isascii():
            non_ascii_paths.append(logical)
        entries.append(
            {
                "logical_path": logical,
                "source_path": str(source_data / "files" / rel),
                "target_path": str(patch_root / rel),
                "source_sha256": row["source_sha256"].upper(),
                "output_sha256": row["output_sha256"].upper(),
                "source_size": int(row["source_size"]),
                "output_size": int(row["output_size"]),
            }
        )

    entries.append(
        {
            "logical_path": "DATA/sys/main.dol",
            "source_path": str(source_data / "sys/main.dol"),
            "target_path": str(main_target),
            "source_sha256": main_info["source_sha256"],
            "output_sha256": main_info["output_sha256"],
            "source_size": main_info["source_size"],
            "output_size": main_info["output_size"],
        }
    )
    if len({row["logical_path"].lower() for row in entries}) != len(entries):
        raise ValueError("case-insensitive duplicate logical paths found")

    delta_root.mkdir(parents=True, exist_ok=True)
    if verify_root.exists():
        shutil.rmtree(verify_root)
    verify_root.mkdir(parents=True)

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(
                build_one,
                entry,
                xdelta,
                delta_root,
                verify_root,
                args.force,
            ): entry["logical_path"]
            for entry in entries
        }
        for future in concurrent.futures.as_completed(futures):
            logical = futures[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                if completed == 1 or completed % 25 == 0 or completed == len(entries):
                    total_mb = sum(r["delta_size"] for r in results) / 1024 / 1024
                    print(
                        f"[{completed:3d}/{len(entries)}] "
                        f"delta={total_mb:,.1f} MiB last={logical}",
                        flush=True,
                    )
            except Exception as exc:
                failures.append(f"{logical}: {exc}")
                print(f"[FAILED] {logical}: {exc}", flush=True)

    shutil.rmtree(verify_root, ignore_errors=True)
    if failures:
        raise RuntimeError(
            f"{len(failures)} delta entries failed:\n" + "\n".join(failures[:20])
        )

    results.sort(key=lambda row: row["logical_path"].lower())
    aggregate = hashlib.sha256()
    for row in results:
        aggregate.update(row["logical_path"].encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(bytes.fromhex(row["delta_sha256"]))
        aggregate.update(b"\0")

    payload_manifest = {
        "schema": SCHEMA,
        "game_id": GAME_ID,
        "disc_region": "Japan",
        "disc_revision": 0,
        "patch_title": "Arc Rise Fantasia Korean ROM Patch",
        "patch_version": "1.1.2",
        "translator_model": "Codex internal",
        "meaning_translation_external_services_used": [],
        "copyright_policy": (
            "The payload contains VCDIFF deltas only and does not contain "
            "a complete source or patched game image."
        ),
        "source_contract": {
            "main_dol_sha256": EXPECTED_MAIN_DOL_SHA256,
            "staged_file_count": EXPECTED_FILE_COUNT,
            "total_entry_count": len(results),
        },
        "runtime_patch": {
            **main_info,
            "riivolution_xml_sha256": sha256_file(xml_path),
        },
        "xdelta": {
            "version": "3.2.0",
            "format": "VCDIFF/RFC 3284",
            "encode_options": ["-9", "-S", "lzma"],
            "roundtrip_verified_entries": len(results),
        },
        "counts": {
            "file_entries": len(results),
            "staged_files": len(staged_files),
            "main_dol_entries": 1,
            "non_ascii_logical_paths": len(non_ascii_paths),
        },
        "totals": {
            "source_bytes": sum(r["source_size"] for r in results),
            "output_bytes": sum(r["output_size"] for r in results),
            "delta_bytes": sum(r["delta_size"] for r in results),
        },
        "aggregate_delta_sha256": aggregate.hexdigest().upper(),
        "entries": results,
        "build": {
            "elapsed_seconds": round(time.time() - started, 3),
            "jobs": args.jobs,
            "staging_manifest_sha256": sha256_file(staging_manifest_path),
            "non_ascii_logical_paths": non_ascii_paths,
        },
    }

    payload_root.mkdir(parents=True, exist_ok=True)
    manifest_path = payload_root / "patch_manifest.json"
    temp_manifest = manifest_path.with_suffix(".json.partial")
    temp_manifest.write_text(
        json.dumps(payload_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_manifest, manifest_path)

    report = {
        "valid": True,
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "entries": len(results),
        "total_delta_bytes": payload_manifest["totals"]["delta_bytes"],
        "aggregate_delta_sha256": payload_manifest["aggregate_delta_sha256"],
        "main_dol_output_sha256": main_info["output_sha256"],
        "all_roundtrip_verified": all(
            r["roundtrip_verified"] for r in results
        ),
    }
    report_path = build_root / "delta_build_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
