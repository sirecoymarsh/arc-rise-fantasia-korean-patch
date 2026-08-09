#!/usr/bin/env python3
"""Read-only extractor/auditor for a Wii opening.bnr package."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path, PurePosixPath


U8_MAGIC = 0x55AA382D


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def be32(buf: bytes, off: int) -> int:
    return struct.unpack_from(">I", buf, off)[0]


def u8_extract(buf: bytes, out: Path) -> list[dict]:
    if be32(buf, 0) != U8_MAGIC:
        raise ValueError("not a U8 archive")
    root_off = be32(buf, 4)
    node_count = be32(buf, root_off + 8)
    string_off = root_off + node_count * 12
    nodes = []
    for i in range(node_count):
        off = root_off + i * 12
        w0, w1, w2 = struct.unpack_from(">III", buf, off)
        typ, name_off = w0 >> 24, w0 & 0xFFFFFF
        end = buf.find(b"\0", string_off + name_off)
        if end < 0:
            raise ValueError(f"unterminated U8 name at node {i}")
        name = buf[string_off + name_off:end].decode("ascii", "replace")
        nodes.append({"index": i, "type": typ, "name": name,
                      "word1": w1, "word2": w2})
    out.mkdir(parents=True, exist_ok=True)
    stack: list[tuple[int, PurePosixPath]] = [(nodes[0]["word2"], PurePosixPath())]
    rows = []
    for i, n in enumerate(nodes[1:], 1):
        while stack and i >= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else PurePosixPath()
        rel = parent / n["name"]
        if n["type"] == 1:
            (out / Path(*rel.parts)).mkdir(parents=True, exist_ok=True)
            stack.append((n["word2"], rel))
            rows.append({**n, "path": rel.as_posix(), "kind": "directory"})
        elif n["type"] == 0:
            payload = buf[n["word1"]:n["word1"] + n["word2"]]
            target = out / Path(*rel.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            rows.append({**n, "path": rel.as_posix(), "kind": "file",
                         "size": len(payload), "sha256": sha256_bytes(payload),
                         "head16": payload[:16].hex().upper()})
        else:
            raise ValueError(f"unknown U8 node type {n['type']} at {i}")
    return rows


def lz77_decompress(buf: bytes) -> bytes:
    if buf[:4] == b"LZ77":
        buf = buf[4:]
    if not buf or buf[0] != 0x10:
        raise ValueError("not Nintendo LZ77 type 0x10")
    expected = int.from_bytes(buf[1:4], "little")
    src, out = 4, bytearray()
    while len(out) < expected:
        flags = buf[src]
        src += 1
        for bit in range(7, -1, -1):
            if len(out) >= expected:
                break
            if flags & (1 << bit):
                b1, b2 = buf[src], buf[src + 1]
                src += 2
                length = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8) | b2
                back = len(out) - disp - 1
                if back < 0:
                    raise ValueError("invalid LZ77 back-reference")
                for _ in range(length):
                    out.append(out[back])
                    back += 1
                    if len(out) >= expected:
                        break
            else:
                out.append(buf[src])
                src += 1
                if len(out) >= expected:
                    break
    return bytes(out)


def unwrap_imd5(data: bytes) -> tuple[bytes, dict]:
    if data[:4] != b"IMD5" or len(data) < 32:
        raise ValueError("missing IMD5")
    declared = be32(data, 4)
    payload = data[32:32 + declared]
    digest = data[16:32]
    import hashlib as _hashlib
    valid = _hashlib.md5(payload).digest() == digest
    return payload, {"declared_payload_size": declared,
                     "actual_payload_size": len(payload),
                     "md5": digest.hex().upper(), "md5_valid": valid}


def decode_imet_names(data: bytes) -> list[str]:
    # IMET names are ten UTF-16BE fields of 42 code units at 0x5c.
    names = []
    for i in range(10):
        raw = data[0x5C + i * 84:0x5C + (i + 1) * 84]
        names.append(raw.decode("utf-16-be", "replace").split("\0", 1)[0])
    return names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    data = args.source.read_bytes()
    if data[0x40:0x44] != b"IMET":
        raise SystemExit("IMET not found at 0x40")
    outer = data[0x600:]
    outer_dir = args.output / "outer"
    rows = u8_extract(outer, outer_dir)
    nested = {}
    for row in rows:
        if row.get("kind") != "file" or row["path"] not in {"meta/banner.bin", "meta/icon.bin"}:
            continue
        raw = (outer_dir / Path(*PurePosixPath(row["path"]).parts)).read_bytes()
        imd5_payload, imd5 = unwrap_imd5(raw)
        decompressed = lz77_decompress(imd5_payload)
        dec_path = args.output / (Path(row["path"]).name + ".decompressed")
        dec_path.write_bytes(decompressed)
        nested_dir = args.output / Path(row["path"]).stem
        inner_rows = u8_extract(decompressed, nested_dir)
        nested[row["path"]] = {
            "imd5": imd5,
            "lz77_decompressed_size": len(decompressed),
            "lz77_decompressed_sha256": sha256_bytes(decompressed),
            "files": inner_rows,
        }
    report = {
        "schema": "arf-ko-opening-bnr-extract-v1",
        "source": str(args.source),
        "source_size": len(data),
        "source_sha256": sha256(args.source),
        "imet_names": decode_imet_names(data),
        "outer_files": rows,
        "nested": nested,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    rp = args.output / "opening_bnr_extract_report.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(rp), "sha256": sha256(rp),
                      "outer_rows": len(rows),
                      "nested_files": sum(len(v["files"]) for v in nested.values()),
                      "imet_names": report["imet_names"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
