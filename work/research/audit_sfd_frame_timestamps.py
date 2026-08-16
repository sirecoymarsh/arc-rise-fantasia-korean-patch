import argparse
import json
import subprocess
from pathlib import Path


def probe_frames(ffprobe: Path, movie: Path):
    command = [
        str(ffprobe), "-v", "error", "-select_streams", "v:0", "-show_frames",
        "-show_entries", "frame=best_effort_timestamp,best_effort_timestamp_time,pkt_dts_time,key_frame,pict_type",
        "-of", "json", str(movie),
    ]
    return json.loads(subprocess.check_output(command, text=True, encoding="utf-8"))["frames"]


def summarize(frames):
    points = []
    for index, frame in enumerate(frames):
        if "best_effort_timestamp" not in frame:
            continue
        points.append((index, int(frame["best_effort_timestamp"]), frame))
    regressions = []
    duplicates = []
    abnormal_steps = []
    for before, after in zip(points, points[1:]):
        delta = after[1] - before[1]
        item = {
            "previous_frame_index": before[0],
            "frame_index": after[0],
            "previous_timestamp": before[1],
            "timestamp": after[1],
            "previous_seconds": before[1] / 90000,
            "seconds": after[1] / 90000,
            "delta_ticks": delta,
            "previous_pict_type": before[2].get("pict_type"),
            "pict_type": after[2].get("pict_type"),
            "key_frame": after[2].get("key_frame"),
        }
        if delta < 0:
            regressions.append(item)
        elif delta == 0:
            duplicates.append(item)
        elif delta != 3000:
            abnormal_steps.append(item)
    return {
        "frame_count": len(frames),
        "timestamped_frame_count": len(points),
        "first_timestamp": points[0][1] if points else None,
        "last_timestamp": points[-1][1] if points else None,
        "regression_count": len(regressions),
        "duplicate_count": len(duplicates),
        "abnormal_positive_step_count": len(abnormal_steps),
        "first_regressions": regressions[:20],
        "first_duplicates": duplicates[:20],
        "first_abnormal_positive_steps": abnormal_steps[:20],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffprobe", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--payload", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    report = {
        "schema": "arf-ko-sfd-frame-timestamp-audit-v1",
        "source": summarize(probe_frames(args.ffprobe, args.source)),
        "payload": summarize(probe_frames(args.ffprobe, args.payload)),
    }
    report["valid"] = (
        report["source"]["regression_count"] == 0
        and report["payload"]["regression_count"] == 0
        and report["source"]["duplicate_count"] == 0
        and report["payload"]["duplicate_count"] == 0
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
