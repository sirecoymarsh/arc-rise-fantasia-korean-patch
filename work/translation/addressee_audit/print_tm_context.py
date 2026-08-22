#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus", type=Path)
    ap.add_argument("tm_ids", nargs="+")
    ap.add_argument("--radius", type=int, default=5)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    wanted = set(args.tm_ids)
    found: dict[str, int] = {key: 0 for key in wanted}
    for scene in corpus["scenes"]:
        rows = scene["utterances"]
        for row in rows:
            tm_id = row.get("tm_id")
            if tm_id not in wanted or (found[tm_id] and not args.all):
                continue
            found[tm_id] += 1
            print(f"\n## {tm_id} :: {scene['locator']} :: line {row['line_index']} :: speaker {row['speaker_slot']}")
            print(f"JP {row['source_text'].replace(chr(10), ' / ')}")
            print(f"KO {row['translation_ko'].replace(chr(10), ' / ')}")
            start = max(0, int(row["line_index"]) - args.radius)
            stop = min(len(rows), int(row["line_index"]) + args.radius + 1)
            for peer in rows[start:stop]:
                mark = "=>" if peer["line_index"] == row["line_index"] else "  "
                src = peer["source_text"].replace("\n", " / ")
                ko = peer["translation_ko"].replace("\n", " / ")
                print(f"{mark} L{peer['line_index']:03d} S{peer['speaker_slot']} {peer.get('tm_id') or '-'}")
                print(f"   JP {src}")
                print(f"   KO {ko}")
    missing = [key for key, count in found.items() if not count]
    if missing:
        print("\nMISSING " + " ".join(sorted(missing)))


if __name__ == "__main__":
    main()
