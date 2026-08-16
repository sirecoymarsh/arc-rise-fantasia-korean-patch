from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
import mmap
from pathlib import Path
import struct
import sys


KINDS = ("enemy", "magic", "map", "pc", "weapon", "win", "tutorial")
BURST_TERMS = ("バーストショット", "バースト・ショット", "バースト", "ショット")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def worker(task):
    scanner_path, path, offset, size, kind, index = task
    scan = load_module(f"scan_{kind}_{index}", Path(scanner_path))
    with open(path, "rb") as f:
        f.seek(offset)
        packed = f.read(size)
    if not packed:
        return {"kind": kind, "index": index, "empty": True, "packed_size": 0}
    data = scan.lz10_decompress(packed) if packed[:1] == b"\x10" else packed
    first_rtdp = data.find(b"RTDP")
    burst = []
    for term in BURST_TERMS:
        raw = term.encode("euc_jp")
        pos = 0
        while True:
            at = data.find(raw, pos)
            if at < 0:
                break
            burst.append({"term": term, "offset": at})
            pos = at + 1
    magic = data[:4]
    return {
        "kind": kind,
        "index": index,
        "empty": False,
        "packed_size": len(packed),
        "unpacked_size": len(data),
        "magic_hex": magic.hex().upper(),
        "magic_ascii": "".join(chr(v) if 0x20 <= v < 0x7F else "." for v in magic),
        "first_rtdp_offset": first_rtdp,
        "burst_hits": burst,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ns = ap.parse_args()
    root = ns.root.resolve()
    scanner = root / "work/research/scan_btl_enemy_text.py"
    btl = root / "work/disc_extracted/DATA/files/Btl"
    headers = root / "work/research/table_agent/btl_usual_entries"
    tasks = []
    inputs = []
    for kind in KINDS:
        vld = btl / f"btl_{kind}.vld"
        header = headers / f"btl_{kind}.vlh"
        raw_header = header.read_bytes()
        if raw_header[:4] != b"RVLX":
            raise ValueError(header)
        count = struct.unpack_from(">I", raw_header, 8)[0]
        inputs.append({
            "kind": kind,
            "header": str(header),
            "header_sha256": sha256(header),
            "vld": str(vld),
            "vld_sha256": sha256(vld),
            "entry_count": count,
        })
        for index in range(count):
            size, offset = struct.unpack_from(">II", raw_header, 0x20 + index * 8)
            tasks.append((str(scanner), str(vld), offset, size, kind, index))
    with ProcessPoolExecutor(max_workers=ns.workers) as pool:
        rows = list(pool.map(worker, tasks, chunksize=1))
    summaries = []
    burst_hits = []
    for kind in KINDS:
        group = [row for row in rows if row["kind"] == kind]
        magics = Counter(row.get("magic_ascii", "empty") for row in group)
        hits = [{"entry": row["index"], **hit} for row in group for hit in row.get("burst_hits", [])]
        burst_hits.extend([{"kind": kind, **hit} for hit in hits])
        summaries.append({
            "kind": kind,
            "entry_count": len(group),
            "nonempty_entries": sum(not row["empty"] for row in group),
            "empty_entries": sum(row["empty"] for row in group),
            "decoded_magic_counts": dict(sorted(magics.items())),
            "entries_with_nested_rtdp": sum(row.get("first_rtdp_offset", -1) >= 0 for row in group),
            "burst_name_hits": hits,
        })
    report = {
        "schema": "arf-all-btl-vld-surface-classification-v1",
        "game_id": "RPJJ99",
        "translation_engine_policy": "Codex internal model only",
        "inputs": inputs,
        "summary": summaries,
        "burst_terms": list(BURST_TERMS),
        "exact_compound_hit_count": sum(hit["term"] in BURST_TERMS[:2] for hit in burst_hits),
        "component_term_hit_count": sum(hit["term"] in BURST_TERMS[2:] for hit in burst_hits),
        "burst_term_hits": burst_hits,
        "valid": not any(hit["term"] in BURST_TERMS[:2] for hit in burst_hits),
    }
    ns.output.parent.mkdir(parents=True, exist_ok=True)
    ns.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(ns.output),
        "entries": len(rows),
        "summaries": summaries,
        "exact_compound_hit_count": report["exact_compound_hit_count"],
        "component_term_hit_count": report["component_term_hit_count"],
        "valid": report["valid"],
    }, ensure_ascii=True, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
