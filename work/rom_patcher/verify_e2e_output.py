from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest().upper()


def run(args: list[str]) -> str:
    proc = subprocess.run(args, text=True, encoding="utf-8", errors="replace",
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode:
        raise RuntimeError(f"exit {proc.returncode}: {' '.join(args[:3])}\n{proc.stdout}")
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    image = args.image.resolve()
    manifest_path = repo / "work/rom_patcher/build/payload/patch_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dolphin = repo / "work/tools/dolphin-2603a/Dolphin-x64/DolphinTool.exe"
    verify_root = repo / "work/rom_patcher/e2e/verify" / args.name
    extract_root = verify_root / "extract"
    if verify_root.exists():
        shutil.rmtree(verify_root)
    verify_root.mkdir(parents=True)

    header = run([str(dolphin), "header", "-i", str(image)])
    container_verify = run([str(dolphin), "verify", "-i", str(image)])
    run([str(dolphin), "extract", "-i", str(image), "-o", str(extract_root), "-g", "-q"])

    mismatches: list[dict[str, object]] = []
    checked = []
    for index, row in enumerate(manifest["entries"], 1):
        path = extract_root / Path(*row["logical_path"].split("/"))
        if not path.is_file():
            mismatches.append({"path": row["logical_path"], "error": "missing"})
            continue
        size = path.stat().st_size
        digest = sha256_file(path)
        if size != row["output_size"] or digest != row["output_sha256"]:
            mismatches.append({
                "path": row["logical_path"],
                "error": "output_mismatch",
                "expected_size": row["output_size"],
                "actual_size": size,
                "expected_sha256": row["output_sha256"],
                "actual_sha256": digest,
            })
        checked.append({"path": row["logical_path"], "size": size, "sha256": digest})
        if index == 1 or index % 100 == 0 or index == len(manifest["entries"]):
            print(f"[{index}/{len(manifest['entries'])}] {row['logical_path']}", flush=True)

    expected_low = {
        "The update partition is missing.",
        "The DATA partition is not correctly signed.",
    }
    summaries = {
        line.split(":", 1)[1].strip()
        for line in container_verify.splitlines()
        if line.strip().lower().startswith("summary:")
    }
    unexpected = sorted(summaries - expected_low)
    report = {
        "schema": "arf-rom-patcher-e2e-output-v1",
        "name": args.name,
        "valid": not mismatches and not unexpected,
        "image": str(image),
        "image_size": image.stat().st_size,
        "image_sha256": sha256_file(image),
        "header": header.strip(),
        "dolphin_verify": container_verify.strip(),
        "accepted_low_severity_summaries": sorted(summaries & expected_low),
        "unexpected_verify_summaries": unexpected,
        "manifest_sha256": sha256_file(manifest_path),
        "expected_entries": len(manifest["entries"]),
        "checked_entries": len(checked),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "main_dol_output_sha256": manifest["runtime_patch"]["output_sha256"],
        "all_722_output_hashes_match": not mismatches and len(checked) == 722,
    }
    report_path = verify_root / "report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    shutil.rmtree(extract_root)
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("dolphin_verify", "header", "mismatches")},
                     ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
