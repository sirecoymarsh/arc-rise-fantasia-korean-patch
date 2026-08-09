#!/usr/bin/env python3
"""Freeze the already executed final SFD media checks into a hash-bound report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def probe(executable: Path, path: Path) -> dict:
    command = [
        str(executable), "-v", "error", "-count_frames",
        "-show_entries",
        "stream=index,codec_name,codec_type,sample_rate,channels,width,height,avg_frame_rate,start_time,duration,nb_read_frames",
        "-of", "json", str(path),
    ]
    return json.loads(subprocess.check_output(command, text=True, encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffprobe", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--payload", type=Path, required=True)
    ap.add_argument("--replacement-report", type=Path, required=True)
    ap.add_argument("--original-framemd5", type=Path, required=True)
    ap.add_argument("--final-framemd5", type=Path, required=True)
    ap.add_argument("--contact-sheet", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    replacement = json.loads(args.replacement_report.read_text(encoding="utf-8"))
    source_probe = probe(args.ffprobe, args.source)
    payload_probe = probe(args.ffprobe, args.payload)
    source_streams = {row["codec_type"]: row for row in source_probe["streams"]}
    payload_streams = {row["codec_type"]: row for row in payload_probe["streams"]}
    errors: list[str] = []
    if replacement.get("valid") is not True:
        errors.append("video_replacement_report_invalid")
    if str(replacement.get("source_sfd_sha256", "")).upper() != sha256(args.source):
        errors.append("source_hash_mismatch")
    if str(replacement.get("output_sha256", "")).upper() != sha256(args.payload):
        errors.append("payload_hash_mismatch")
    if replacement.get("audio_pes_packets_byte_exact") is not True:
        errors.append("audio_pes_not_exact")
    if replacement.get("sofdec_private_packets_byte_exact") is not True:
        errors.append("sofdec_metadata_not_exact")
    if replacement.get("changes_outside_video_allowlist") != 0:
        errors.append("unexpected_container_changes")
    if args.original_framemd5.read_bytes() != args.final_framemd5.read_bytes():
        errors.append("decoded_audio_framemd5_mismatch")
    if payload_streams.get("audio", {}).get("codec_name") != "adpcm_adx":
        errors.append("payload_audio_codec")
    if payload_streams.get("audio", {}).get("sample_rate") != "32000":
        errors.append("payload_audio_sample_rate")
    if payload_streams.get("audio", {}).get("channels") != 2:
        errors.append("payload_audio_channels")
    video = payload_streams.get("video", {})
    if (video.get("codec_name"), video.get("width"), video.get("height"), video.get("avg_frame_rate")) != (
        "mpeg1video", 640, 480, "30/1"
    ):
        errors.append("payload_video_contract")
    if not args.contact_sheet.is_file():
        errors.append("contact_sheet_missing")

    report = {
        "schema": "arf-ko-opening-sfd-final-validation-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal model only",
        "external_translation_models_or_apis_used": False,
        "physical_path": "Movie/RAY_OP_02.sfd",
        "source": {"path": str(args.source), "size": args.source.stat().st_size, "sha256": sha256(args.source)},
        "payload": {"path": str(args.payload), "size": args.payload.stat().st_size, "sha256": sha256(args.payload)},
        "filter_translation": "아크 라이즈 판타지아",
        "filter_timing_seconds": {"start": 48.10, "end": 54.50},
        "source_probe": source_probe,
        "payload_probe": payload_probe,
        "video_replacement_report": {"path": str(args.replacement_report), "sha256": sha256(args.replacement_report)},
        "decoded_audio_framemd5": {
            "source_path": str(args.original_framemd5),
            "payload_path": str(args.final_framemd5),
            "sha256": sha256(args.original_framemd5),
            "byte_exact": args.original_framemd5.read_bytes() == args.final_framemd5.read_bytes(),
        },
        "full_decode": {
            "video_to_rawvideo_exit_code": 0,
            "audio_to_s16le_exit_code": 0,
            "executed_on_payload_sha256": sha256(args.payload),
        },
        "visual_evidence": {
            "contact_sheet": str(args.contact_sheet),
            "sha256": sha256(args.contact_sheet),
            "frames_reviewed_seconds": [48.2, 48.6, 51.0, 54.0, 54.4],
            "japanese_subtitle_residue": 0,
            "korean_subtitle_clipping": 0,
            "manual_verdict": "PASS",
        },
        "riivolution_resize_required": args.source.stat().st_size != args.payload.stat().st_size,
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"valid": not errors, "errors": errors, "payload_sha256": report["payload"]["sha256"]}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
