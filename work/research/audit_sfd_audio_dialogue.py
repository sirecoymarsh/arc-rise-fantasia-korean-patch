#!/usr/bin/env python3
"""Transcribe SFD ADX audio for dialogue-presence auditing.

The STT output is evidence for locating Japanese speech only. It is never used
as an accepted Korean translation; all semantic Korean remains Codex-authored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--packages", type=Path, required=True)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--model", default="small")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--compute-type", default="float16")
    args = ap.parse_args()

    sys.path.insert(0, str(args.packages))
    from faster_whisper import WhisperModel

    args.cache.mkdir(parents=True, exist_ok=True)
    started = time.time()
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        download_root=str(args.cache),
    )
    rows = []
    for wav in sorted(args.wav_dir.glob("*.wav"), key=lambda p: p.name.lower()):
        file_started = time.time()
        segments, info = model.transcribe(
            str(wav),
            language="ja",
            task="transcribe",
            beam_size=5,
            best_of=5,
            condition_on_previous_text=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            word_timestamps=True,
            temperature=0.0,
        )
        rendered = []
        for seg in segments:
            words = []
            for word in seg.words or []:
                words.append({
                    "start": round(float(word.start), 3),
                    "end": round(float(word.end), 3),
                    "word": word.word,
                    "probability": round(float(word.probability), 6),
                })
            rendered.append({
                "id": int(seg.id),
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": seg.text.strip(),
                "avg_logprob": round(float(seg.avg_logprob), 6),
                "no_speech_prob": round(float(seg.no_speech_prob), 6),
                "compression_ratio": round(float(seg.compression_ratio), 6),
                "words": words,
            })
        row = {
            "wav": wav.name,
            "wav_size": wav.stat().st_size,
            "wav_sha256": sha256(wav),
            "language": info.language,
            "language_probability": round(float(info.language_probability), 6),
            "duration": round(float(info.duration), 3),
            "duration_after_vad": round(float(info.duration_after_vad), 3),
            "segment_count": len(rendered),
            "segments": rendered,
            "elapsed_seconds": round(time.time() - file_started, 3),
        }
        rows.append(row)
        print(json.dumps({"wav": wav.name, "segments": len(rendered), "elapsed": row["elapsed_seconds"]}, ensure_ascii=False), flush=True)

    report = {
        "schema": "arf-sfd-audio-dialogue-stt-v1",
        "game_id": "RPJJ99",
        "purpose": "Japanese speech presence and timing discovery only",
        "accepted_korean_translation_source": "Codex internal only",
        "stt_is_translation": False,
        "stt_model": f"faster-whisper/{args.model}",
        "device": args.device,
        "compute_type": args.compute_type,
        "audio_file_count": len(rows),
        "elapsed_seconds": round(time.time() - started, 3),
        "files": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": sha256(args.output), "files": len(rows)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
