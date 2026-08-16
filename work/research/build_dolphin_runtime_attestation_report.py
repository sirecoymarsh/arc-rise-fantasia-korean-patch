#!/usr/bin/env python3
"""Build the artifact-bound Dolphin report consumed by the final verifier.

This builder deliberately separates observation from report construction.  A
human/reviewer first records explicit pass/fail decisions in an attestation
file; this program then rejects every non-passing or unbound decision, hashes
the exact runtime evidence, and binds it to the current staging manifest,
release MANIFEST.json, and Riivolution XML.

Create a conservative template (all checks start as ``passed: false``)::

    python work/research/build_dolphin_runtime_attestation_report.py \
      --emit-template work/runtime_validation/dolphin_runtime_attestation.json

After reviewing the named screenshots and changing only genuinely observed
checks to ``passed: true``, build the verifier input::

    python work/research/build_dolphin_runtime_attestation_report.py \
      --attestation work/runtime_validation/dolphin_runtime_attestation.json

The output defaults to ``work/validation/dolphin_runtime_validation.json``.
It is compatible with ``verify_dolphin_runtime`` in
``build_full_final_verification.py``.  This script never invokes Dolphin or the
final verifier.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GAME_ID = "RPJJ99"
REPORT_SCHEMA = "arf-ko-dolphin-runtime-validation-v1"
ATTESTATION_SCHEMA = "arf-ko-dolphin-runtime-attestation-v1"
SESSION_SCHEMA = "arf-ko-dolphin-runtime-session-v1"

DEFAULT_STAGING_MANIFEST = ROOT / "work/final_runtime_staging/staging_manifest.json"
DEFAULT_PACKAGE_MANIFEST = ROOT / "outputs/Arc_Rise_Fantasia_Korean_Patch_v1.0/MANIFEST.json"
DEFAULT_RIIVOLUTION_XML = (
    ROOT
    / "work/final_runtime_staging/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
)
DEFAULT_SESSION = ROOT / "work/runtime_validation/final_runtime_v5/full_runtime_session.json"
DEFAULT_OUTPUT = ROOT / "work/validation/dolphin_runtime_validation.json"

TEMPLATE_CHECKS: tuple[dict[str, Any], ...] = (
    {
        "name": "final_patch_reaches_original_cinematic",
        "passed": False,
        "evidence_paths": [
            "work/runtime_validation/final_runtime_v5/final_v6_probe_35s.png",
        ],
        "notes": "Confirm the exact final staging reaches the original in-game cinematic without a restart loop.",
    },
    {
        "name": "original_sfd_sequence_reaches_live_battle",
        "passed": False,
        "evidence_paths": [
            "work/runtime_validation/final_runtime_v5/final_v6_probe_35s.png",
            "work/runtime_validation/final_runtime_v5/final_v6_wyvern_01.png",
        ],
        "notes": "Confirm the same session advances from the original disc cinematic to live battle with no replacement SFD overlay.",
    },
    {
        "name": "korean_battle_monster_and_result_text_renders",
        "passed": False,
        "evidence_paths": [
            "work/runtime_validation/final_runtime_v5/final_v6_wyvern_03.png",
        ],
        "notes": "Confirm live battle visibly renders the Korean monster name and Korean critical-hit result text; this does not claim an enemy skill-name label.",
    },
    {
        "name": "battle_frames_continue_advancing",
        "passed": False,
        "evidence_paths": [
            "work/runtime_validation/final_runtime_v5/final_v6_wyvern_01.png",
            "work/runtime_validation/final_runtime_v5/final_v6_wyvern_02.png",
            "work/runtime_validation/final_runtime_v5/final_v6_wyvern_03.png",
        ],
        "notes": "Confirm three time-separated live-battle frames differ.",
    },
    {
        "name": "runtime_session_bound_and_logs_clean",
        "passed": False,
        "evidence_paths": [
            "work/runtime_validation/final_runtime_v5/final_v6_runtime_probe.json",
        ],
        "notes": "Confirm the captured session is bound to current staging, Vulkan is active with MMU and FastDiscSpeed disabled, logs are empty, and frame progression is measured.",
    },
)

class ContractError(RuntimeError):
    """Raised when evidence cannot satisfy the final verifier contract."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read {label} JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a JSON object: {path}")
    return value


def resolve_project_file(value: str | os.PathLike[str], label: str) -> tuple[Path, str]:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ContractError(f"missing {label}: {candidate}") from exc
    if not resolved.is_file():
        raise ContractError(f"{label} is not a file: {resolved}")
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ContractError(f"{label} must stay inside the project root: {resolved}") from exc
    return resolved, relative.as_posix()


def resolve_project_output(value: str | os.PathLike[str], label: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ContractError(f"{label} must stay inside the project root: {resolved}") from exc
    return resolved


def require_exact_hash(record: Any, key: str, expected_path: Path) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ContractError(f"runtime session {key!r} must be an object")
    expected_hash = sha256_file(expected_path)
    observed_hash = str(record.get("sha256", "")).upper()
    if observed_hash != expected_hash:
        raise ContractError(
            f"runtime session {key!r} is stale: expected {expected_hash}, observed {observed_hash or '<empty>'}"
        )
    raw_path = record.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ContractError(f"runtime session {key!r} has no path")
    observed_path = Path(raw_path)
    if not observed_path.is_absolute():
        observed_path = ROOT / observed_path
    try:
        same_path = observed_path.resolve(strict=True) == expected_path.resolve(strict=True)
    except OSError as exc:
        raise ContractError(f"runtime session {key!r} path is missing: {observed_path}") from exc
    if not same_path:
        raise ContractError(
            f"runtime session {key!r} points at a different artifact: {observed_path} != {expected_path}"
        )
    return record


def artifact_record(path: Path, relative: str, used_by_checks: set[str]) -> dict[str, Any]:
    return {
        "path": relative,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "used_by_checks": sorted(used_by_checks),
    }


def add_artifact(
    artifacts: dict[str, tuple[Path, set[str]]],
    path_value: str | os.PathLike[str],
    purpose: str,
) -> tuple[Path, str]:
    path, relative = resolve_project_file(path_value, f"artifact for {purpose}")
    if relative in artifacts:
        artifacts[relative][1].add(purpose)
    else:
        artifacts[relative] = (path, {purpose})
    return path, relative


def validate_attestation(
    value: dict[str, Any], artifacts: dict[str, tuple[Path, set[str]]]
) -> list[dict[str, Any]]:
    if value.get("schema") != ATTESTATION_SCHEMA:
        raise ContractError(
            f"attestation schema must be {ATTESTATION_SCHEMA!r}, got {value.get('schema')!r}"
        )
    if value.get("game_id") != GAME_ID:
        raise ContractError(f"attestation game_id must be {GAME_ID!r}")
    raw_checks = value.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        raise ContractError("attestation checks must be a non-empty array")

    seen_names: set[str] = set()
    checks: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_checks):
        if not isinstance(raw, dict):
            raise ContractError(f"attestation checks[{index}] must be an object")
        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ContractError(f"attestation checks[{index}] has an empty name")
        name = name.strip()
        if name in seen_names:
            raise ContractError(f"duplicate attestation check name: {name}")
        seen_names.add(name)
        if raw.get("passed") is not True:
            raise ContractError(
                f"attestation check {name!r} is not explicitly passed; review its evidence first"
            )
        evidence = raw.get("evidence_paths")
        if not isinstance(evidence, list) or not evidence:
            raise ContractError(f"attestation check {name!r} has no evidence_paths")
        evidence_relatives: list[str] = []
        for evidence_index, path_value in enumerate(evidence):
            if not isinstance(path_value, str) or not path_value:
                raise ContractError(
                    f"attestation check {name!r} evidence_paths[{evidence_index}] is invalid"
                )
            _, relative = add_artifact(artifacts, path_value, name)
            evidence_relatives.append(relative)
        if len(set(evidence_relatives)) != len(evidence_relatives):
            raise ContractError(f"attestation check {name!r} repeats an evidence path")

        check: dict[str, Any] = {
            "name": name,
            "passed": True,
            "evidence_paths": evidence_relatives,
        }
        notes = raw.get("notes")
        if notes is not None:
            if not isinstance(notes, str):
                raise ContractError(f"attestation check {name!r} notes must be a string")
            check["notes"] = notes
        observed_at = raw.get("observed_at_utc")
        if observed_at is not None:
            if not isinstance(observed_at, str) or not observed_at:
                raise ContractError(
                    f"attestation check {name!r} observed_at_utc must be a non-empty string"
                )
            check["observed_at_utc"] = observed_at
        checks.append(check)
    return checks


def validate_runtime_session(
    session_path: Path,
    staging_manifest_path: Path,
    xml_path: Path,
    artifacts: dict[str, tuple[Path, set[str]]],
) -> dict[str, Any]:
    session = read_json_object(session_path, "runtime session")
    if session.get("schema") != SESSION_SCHEMA:
        raise ContractError(
            f"runtime session schema must be {SESSION_SCHEMA!r}, got {session.get('schema')!r}"
        )
    require_exact_hash(session.get("staging_manifest"), "staging_manifest", staging_manifest_path)
    require_exact_hash(session.get("xml"), "xml", xml_path)
    settings = session.get("settings")
    if not isinstance(settings, dict) or settings.get("GFXBackend") != "Vulkan":
        raise ContractError("runtime session did not use the required Vulkan backend")
    if settings.get("MMU") is not False:
        raise ContractError("runtime session MMU setting differs from the tested contract")
    if settings.get("FastDiscSpeed") is not False:
        raise ContractError("runtime session unexpectedly depends on fast disc transfer")

    system_vol_path = (
        ROOT
        / "work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Sys/system.vol"
    )
    if not system_vol_path.is_file():
        raise ContractError(f"current staged system.vol is missing: {system_vol_path}")
    system_vol = require_exact_hash(session.get("system_vol"), "system_vol", system_vol_path)

    # Preserve the launch descriptor and empty/non-empty Dolphin logs as hashed
    # evidence when the session declares them.  They are not allowed outside the
    # project root, which keeps the final report portable and reviewable.
    descriptor = session.get("descriptor")
    descriptor_relative: str | None = None
    if isinstance(descriptor, dict):
        raw_descriptor_path = descriptor.get("path")
        if not isinstance(raw_descriptor_path, str) or not raw_descriptor_path:
            raise ContractError("runtime session descriptor has no path")
        descriptor_path, descriptor_relative = add_artifact(
            artifacts, raw_descriptor_path, "runtime_session_descriptor"
        )
        if str(descriptor.get("sha256", "")).upper() != sha256_file(descriptor_path):
            raise ContractError("runtime session descriptor hash is stale")

    log_relatives: dict[str, str] = {}
    for stream in ("stdout", "stderr"):
        raw_log_path = session.get(stream)
        if raw_log_path is None:
            continue
        if not isinstance(raw_log_path, str) or not raw_log_path:
            raise ContractError(f"runtime session {stream} path is invalid")
        _, relative = add_artifact(artifacts, raw_log_path, f"runtime_session_{stream}")
        log_relatives[stream] = relative

    return {
        "schema": SESSION_SCHEMA,
        "path": session_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "sha256": sha256_file(session_path),
        "started_utc": session.get("started_utc"),
        "settings": session.get("settings"),
        "system_vol_sha256": str(system_vol.get("sha256", "")).upper(),
        "descriptor_path": descriptor_relative,
        "logs": log_relatives,
    }


def validate_binding_inputs(
    staging_manifest_path: Path,
    package_manifest_path: Path,
    xml_path: Path,
) -> None:
    staging = read_json_object(staging_manifest_path, "staging manifest")
    if staging.get("schema") != "arf-full-runtime-staging-v2":
        raise ContractError("unexpected staging manifest schema")
    if staging.get("game_id") != GAME_ID:
        raise ContractError(f"staging manifest game_id must be {GAME_ID!r}")
    riivolution = staging.get("riivolution")
    if not isinstance(riivolution, dict):
        raise ContractError("staging manifest has no riivolution object")
    if str(riivolution.get("sha256", "")).upper() != sha256_file(xml_path):
        raise ContractError("staging manifest Riivolution XML hash is stale")

    package = read_json_object(package_manifest_path, "package manifest")
    if package.get("schema") != "arf-ko-riivolution-release-v1":
        raise ContractError("unexpected package manifest schema")
    if package.get("game_id") != GAME_ID:
        raise ContractError(f"package manifest game_id must be {GAME_ID!r}")


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def emit_template(path: Path) -> None:
    if path.exists():
        raise ContractError(f"refusing to overwrite attestation template: {path}")
    template = {
        "schema": ATTESTATION_SCHEMA,
        "game_id": GAME_ID,
        "session_path": DEFAULT_SESSION.resolve().relative_to(ROOT.resolve()).as_posix(),
        "checks": [dict(row) for row in TEMPLATE_CHECKS],
    }
    atomic_write_json(path, template)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    attestation_path, attestation_relative = resolve_project_file(
        args.attestation, "runtime attestation"
    )
    staging_manifest_path, _ = resolve_project_file(
        args.staging_manifest, "staging manifest"
    )
    package_manifest_path, _ = resolve_project_file(
        args.package_manifest, "package manifest"
    )
    xml_path, _ = resolve_project_file(args.riivolution_xml, "Riivolution XML")
    validate_binding_inputs(staging_manifest_path, package_manifest_path, xml_path)

    attestation = read_json_object(attestation_path, "runtime attestation")
    artifacts: dict[str, tuple[Path, set[str]]] = {}
    checks = validate_attestation(attestation, artifacts)
    add_artifact(artifacts, attestation_path, "attestation_source")

    raw_session_path: str | os.PathLike[str]
    if args.session is not None:
        raw_session_path = args.session
    else:
        raw_session_path = attestation.get("session_path", DEFAULT_SESSION)
    session_path, _ = add_artifact(artifacts, raw_session_path, "runtime_session_binding")
    session_evidence = validate_runtime_session(
        session_path, staging_manifest_path, xml_path, artifacts
    )

    artifact_rows = [
        artifact_record(path, relative, purposes)
        for relative, (path, purposes) in sorted(artifacts.items())
    ]
    if not artifact_rows:
        raise ContractError("at least one hashed runtime artifact is required")

    return {
        "schema": REPORT_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "game_id": GAME_ID,
        "staging_manifest_sha256": sha256_file(staging_manifest_path),
        "package_manifest_sha256": sha256_file(package_manifest_path),
        "riivolution_xml_sha256": sha256_file(xml_path),
        "runtime_session": session_evidence,
        "attestation_source": attestation_relative,
        "checks": checks,
        "passed_count": len(checks),
        "failed_count": 0,
        "error_count": 0,
        "errors": [],
        "valid": True,
        "artifacts": artifact_rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--attestation",
        type=Path,
        help="reviewed attestation JSON; every check must be explicitly passed",
    )
    mode.add_argument(
        "--emit-template",
        type=Path,
        help="write a non-passing review template and exit",
    )
    parser.add_argument("--session", type=Path, default=None)
    parser.add_argument("--staging-manifest", type=Path, default=DEFAULT_STAGING_MANIFEST)
    parser.add_argument("--package-manifest", type=Path, default=DEFAULT_PACKAGE_MANIFEST)
    parser.add_argument("--riivolution-xml", type=Path, default=DEFAULT_RIIVOLUTION_XML)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.emit_template is not None:
            template_path = resolve_project_output(args.emit_template, "attestation template")
            emit_template(template_path)
            print(f"[runtime-report] template: {template_path}")
            return 0

        output_path = resolve_project_output(args.output, "runtime report")
        report = build_report(args)
        atomic_write_json(output_path, report)
        print(f"[runtime-report] checks: {report['passed_count']}")
        print(f"[runtime-report] artifacts: {len(report['artifacts'])}")
        print(f"[runtime-report] output: {output_path}")
        print(f"[runtime-report] sha256: {sha256_file(output_path)}")
        return 0
    except ContractError as exc:
        print(f"[runtime-report] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
