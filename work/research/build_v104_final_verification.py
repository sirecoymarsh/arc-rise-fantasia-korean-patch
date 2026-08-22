#!/usr/bin/env python3
"""Bind the single final v1.0.4 verification batch into one attestation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work"
OUTPUTS = ROOT / "outputs"
INPUTS = {
    "untranslated_surface_closure": W / "validation/untranslated_surface_closure_v104.json",
    "release_validation": W / "validation/final_release_validation_v104.json",
    "installer_fixture": W / "validation/final_release_installer_fixture_v104.json",
}
ZIP = OUTPUTS / "Arc_Rise_Fantasia_Korean_Patch_v1.0.4.zip"
CHECKSUM = OUTPUTS / "Arc_Rise_Fantasia_Korean_Patch_v1.0.4.zip.sha256"
OUTPUT = W / "validation/final_v104_comprehensive_validation.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    checks = []
    artifacts = []
    for name, path in INPUTS.items():
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        passed = doc.get("valid") is True and int(doc.get("error_count", 0)) == 0
        checks.append({"name": name, "passed": passed, "schema": doc.get("schema")})
        artifacts.append({"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha(path)})
    zip_hash = sha(ZIP)
    sidecar_hash = CHECKSUM.read_text(encoding="ascii").split()[0].upper()
    checks.append({"name": "zip_checksum", "passed": zip_hash == sidecar_hash, "sha256": zip_hash})
    artifacts.extend([
        {"path": str(ZIP), "size_bytes": ZIP.stat().st_size, "sha256": zip_hash},
        {"path": str(CHECKSUM), "size_bytes": CHECKSUM.stat().st_size, "sha256": sha(CHECKSUM)},
    ])
    failed = [row for row in checks if not row["passed"]]
    report = {
        "schema": "arf-ko-final-v104-comprehensive-validation-v1",
        "game_id": "RPJJ99",
        "release": "Arc_Rise_Fantasia_Korean_Patch_v1.0.4",
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "checks": checks,
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "error_count": len(failed),
        "errors": [row["name"] for row in failed],
        "artifacts": artifacts,
        "valid": not failed,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": report["valid"], "checks": len(checks), "zip_sha256": zip_hash, "report": str(OUTPUT), "report_sha256": sha(OUTPUT)}, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
