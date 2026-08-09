#!/usr/bin/env python3
"""Probe Arc Rise Fantasia RTDP entries for Japanese text candidates."""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path


JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uff01-\uff60]")
DISPLAY_RE = re.compile(r"[\x20-\x7e\u3000-\u30ff\u3400-\u9fff\uff01-\uff60]{3,}")


def parse_rtdp(path: Path) -> tuple[dict[str, int], list[dict[str, object]]]:
    data = path.read_bytes()
    if data[:4] != b"RTDP":
        raise ValueError(f"not RTDP: {path}")
    end_of_header, count, total_size = struct.unpack_from(">III", data, 4)
    entries: list[dict[str, object]] = []
    for index in range(count):
        pos = 0x20 + index * 40
        raw_name, size, relative_offset = struct.unpack_from(">32sII", data, pos)
        name = raw_name.split(b"\0", 1)[0].decode("ascii", errors="replace")
        start = end_of_header + relative_offset
        payload = bytes(value ^ 0x55 for value in data[start : start + size])
        entries.append(
            {
                "index": index,
                "name": name,
                "size": size,
                "relative_offset": relative_offset,
                "absolute_offset": start,
                "head_hex": payload[:32].hex().upper(),
                "head_ascii": "".join(chr(x) if 32 <= x <= 126 else "." for x in payload[:32]),
                "payload": payload,
            }
        )
    return {"end_of_header": end_of_header, "count": count, "declared_size": total_size, "actual_size": len(data)}, entries


def extract_sjis_runs(payload: bytes, minimum: int = 3) -> list[dict[str, object]]:
    """Find NUL/control-delimited byte runs that decode as CP932 and contain Japanese."""
    results: list[dict[str, object]] = []
    # Treat common binary/control bytes as separators while preserving Shift-JIS lead/trail bytes.
    start = 0
    for match in re.finditer(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]+", payload):
        for left, right in ((start, match.start()),):
            chunk = payload[left:right].strip(b"\t\n\r ")
            if len(chunk) < minimum:
                continue
            try:
                decoded = chunk.decode("cp932")
            except UnicodeDecodeError:
                continue
            for text_match in DISPLAY_RE.finditer(decoded):
                text = text_match.group(0).strip()
                if len(text) >= minimum and JAPANESE_RE.search(text):
                    results.append({"byte_offset_approx": left, "text": text})
        start = match.end()
    if start < len(payload):
        chunk = payload[start:].strip(b"\t\n\r ")
        if len(chunk) >= minimum:
            try:
                decoded = chunk.decode("cp932")
            except UnicodeDecodeError:
                decoded = ""
            for text_match in DISPLAY_RE.finditer(decoded):
                text = text_match.group(0).strip()
                if len(text) >= minimum and JAPANESE_RE.search(text):
                    results.append({"byte_offset_approx": start, "text": text})
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--extract-dir", type=Path)
    parser.add_argument("--max-runs", type=int, default=30)
    args = parser.parse_args()

    header, entries = parse_rtdp(args.archive)
    output_entries: list[dict[str, object]] = []
    if args.extract_dir:
        args.extract_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        payload = entry.pop("payload")
        assert isinstance(payload, bytes)
        if args.extract_dir:
            safe_name = Path(str(entry["name"])).name
            if not safe_name or safe_name == "reserved_file":
                safe_name = f"entry_{int(entry['index']):04d}_{safe_name or 'unnamed'}"
            destination = args.extract_dir / safe_name
            if destination.exists():
                destination = args.extract_dir / f"entry_{int(entry['index']):04d}_{safe_name}"
            destination.write_bytes(payload)
            entry["extracted_path"] = str(destination.resolve())
        runs = extract_sjis_runs(payload)
        entry["sjis_run_count"] = len(runs)
        entry["sjis_runs"] = runs[: args.max_runs]
        output_entries.append(entry)

    result = {"archive": str(args.archive.resolve()), "header": header, "entries": output_entries}
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
