#!/usr/bin/env python3
"""Safely patch reviewed, NUL-terminated strings in Arc Rise Fantasia main.dol.

The patch is deliberately fixed-width.  Each JSONL row identifies an original
byte span and carries the exact original bytes as ``raw_hex`` (the aliases
``source_raw_hex`` and ``source_raw`` are also accepted).  The Korean text is
encoded with the project's frozen EUC28 codebook and existing encoder, written
at the same offset, and zero-padded to the original byte length.  The original
terminating NUL immediately following the span is required and is never moved.

Required JSONL fields per row::

    {"offset": 1234, "byte_length": 8, "raw_hex": "...",
     "translation_ko": "..."}

Optional ``id``/``source_text`` fields are copied into the report.  When
``source_text`` is present it must encode as EUC-JP to exactly ``raw_hex``.
Blank lines are ignored.  No header row is used.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "arf-main-dol-fixed-string-patch-v1"
CODEBOOK_FORMAT = "arc-rise-fantasia-korean-codebook-v1"
SHA256_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
HEX_RE = re.compile(r"^(?:[0-9A-Fa-f]{2})*$")


class PatchError(RuntimeError):
    """Raised before an unsafe or unverifiable patch can be written."""


@dataclass(frozen=True)
class PatchRow:
    line: int
    row_id: str
    offset: int
    byte_length: int
    raw: bytes
    translation_ko: str
    source_text: str | None
    encoded: bytes

    @property
    def end(self) -> int:
        return self.offset + self.byte_length


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise PatchError(f"cannot import encoder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PatchError(message)


def parse_expected_sha(value: str) -> str:
    value = value.strip().upper()
    require(bool(SHA256_RE.fullmatch(value)), "expected source SHA-256 must be 64 hexadecimal characters")
    return value


def parse_raw_hex(obj: dict[str, Any], line: int) -> bytes:
    present = [key for key in ("raw_hex", "source_raw_hex", "source_raw") if key in obj]
    require(len(present) == 1, f"line {line}: exactly one raw byte field is required (raw_hex)")
    value = obj[present[0]]
    require(isinstance(value, str), f"line {line}: {present[0]} must be a hexadecimal string")
    compact = "".join(value.split())
    require(bool(HEX_RE.fullmatch(compact)), f"line {line}: invalid hexadecimal source raw bytes")
    return bytes.fromhex(compact)


def read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    require(path.is_file(), f"translation JSONL does not exist: {path}")
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PatchError(f"line {line_number}: invalid JSON: {exc.msg}") from exc
            require(isinstance(value, dict), f"line {line_number}: JSONL row must be an object")
            rows.append((line_number, value))
    require(bool(rows), "translation JSONL has no patch rows")
    return rows


def normalize_rows(
    raw_rows: Iterable[tuple[int, dict[str, Any]]],
    codebook: dict[str, Any],
    encoder_module: Any,
) -> list[PatchRow]:
    rows: list[PatchRow] = []
    seen_ids: set[str] = set()
    for line, obj in raw_rows:
        offset = obj.get("offset")
        byte_length = obj.get("byte_length")
        translation = obj.get("translation_ko")
        require(type(offset) is int and offset >= 0, f"line {line}: offset must be a non-negative integer")
        require(type(byte_length) is int and byte_length > 0, f"line {line}: byte_length must be a positive integer")
        require(isinstance(translation, str), f"line {line}: translation_ko must be a string")
        require(translation != "", f"line {line}: translation_ko must not be empty")
        require("\x00" not in translation, f"line {line}: translation_ko contains a literal NUL")

        raw = parse_raw_hex(obj, line)
        require(len(raw) == byte_length, f"line {line}: raw byte count {len(raw)} != byte_length {byte_length}")
        require(b"\x00" not in raw, f"line {line}: raw span contains NUL; byte_length must exclude the terminator")

        row_id_value = obj.get("id", f"line-{line:06d}")
        require(isinstance(row_id_value, (str, int)), f"line {line}: id must be a string or integer")
        row_id = str(row_id_value)
        require(row_id != "", f"line {line}: id must not be empty")
        require(row_id not in seen_ids, f"line {line}: duplicate id {row_id!r}")
        seen_ids.add(row_id)

        source_text_value = obj.get("source_text")
        require(source_text_value is None or isinstance(source_text_value, str), f"line {line}: source_text must be a string")
        if source_text_value is not None:
            try:
                source_text_raw = source_text_value.encode("euc_jp")
            except UnicodeEncodeError as exc:
                raise PatchError(f"line {line}: source_text is not EUC-JP encodable") from exc
            require(source_text_raw == raw, f"line {line}: source_text does not encode to raw_hex")

        try:
            encoded = encoder_module.encode_text(translation, codebook)
        except Exception as exc:
            raise PatchError(f"line {line}: translation encoding failed: {exc}") from exc
        require(isinstance(encoded, bytes), f"line {line}: encoder did not return bytes")
        require(b"\x00" not in encoded, f"line {line}: encoded translation contains NUL")
        require(len(encoded) <= byte_length, f"line {line}: encoded translation is {len(encoded)} bytes, capacity is {byte_length}")

        rows.append(
            PatchRow(
                line=line,
                row_id=row_id,
                offset=offset,
                byte_length=byte_length,
                raw=raw,
                translation_ko=translation,
                source_text=source_text_value,
                encoded=encoded,
            )
        )

    rows.sort(key=lambda row: (row.offset, row.end, row.line))
    for previous, current in zip(rows, rows[1:]):
        # The fixed source span excludes its NUL, but that terminator is part of
        # the protected field boundary and may not be another row's first byte.
        require(
            current.offset > previous.end,
            f"lines {previous.line} and {current.line}: overlapping spans or shared terminator",
        )
    return rows


def validate_source(source: bytes, rows: list[PatchRow], expected_source_sha256: str) -> str:
    actual_sha = sha256_bytes(source)
    require(actual_sha == expected_source_sha256, f"source SHA-256 mismatch: expected {expected_source_sha256}, got {actual_sha}")
    for row in rows:
        require(row.end < len(source), f"line {row.line}: source span or terminating NUL is out of bounds")
        actual_raw = source[row.offset : row.end]
        require(actual_raw == row.raw, f"line {row.line}: original raw bytes mismatch at offset 0x{row.offset:X}")
        require(source[row.end] == 0, f"line {row.line}: original string is not NUL-terminated at offset 0x{row.end:X}")
    return actual_sha


def apply_rows(source: bytes, rows: list[PatchRow]) -> bytes:
    patched = bytearray(source)
    for row in rows:
        patched[row.offset : row.end] = row.encoded + (b"\x00" * (row.byte_length - len(row.encoded)))

    output = bytes(patched)
    require(len(output) == len(source), "internal error: output size changed")
    for row in rows:
        require(output[row.end] == 0, f"line {row.line}: original terminating NUL was modified")
        require(output[row.offset : row.offset + len(row.encoded)] == row.encoded, f"line {row.line}: encoded bytes were not written exactly")
        require(set(output[row.offset + len(row.encoded) : row.end]) <= {0}, f"line {row.line}: residual source bytes remain after translation")

    allowed = bytearray(len(source))
    for row in rows:
        allowed[row.offset : row.end] = b"\x01" * row.byte_length
    unexpected = [index for index, (before, after) in enumerate(zip(source, output)) if before != after and not allowed[index]]
    require(not unexpected, f"internal error: bytes changed outside allowlisted spans: {unexpected[:8]}")
    return output


def build_report(
    source_path: Path,
    translations_path: Path,
    codebook_path: Path,
    encoder_path: Path,
    output_path: Path,
    source: bytes,
    output: bytes,
    rows: list[PatchRow],
) -> dict[str, Any]:
    changed_offsets = sum(before != after for before, after in zip(source, output))
    return {
        "schema": SCHEMA,
        "valid": True,
        "source": {
            "path": str(source_path.resolve()),
            "size": len(source),
            "sha256": sha256_bytes(source),
        },
        "inputs": {
            "translations_jsonl": {
                "path": str(translations_path.resolve()),
                "sha256": sha256_file(translations_path),
            },
            "codebook": {
                "path": str(codebook_path.resolve()),
                "format": CODEBOOK_FORMAT,
                "sha256": sha256_file(codebook_path),
            },
            "encoder": {
                "path": str(encoder_path.resolve()),
                "sha256": sha256_file(encoder_path),
            },
        },
        "output": {
            "path": str(output_path.resolve()),
            "size": len(output),
            "sha256": sha256_bytes(output),
        },
        "summary": {
            "patch_rows": len(rows),
            "source_bytes": sum(row.byte_length for row in rows),
            "encoded_bytes": sum(len(row.encoded) for row in rows),
            "zero_padding_bytes": sum(row.byte_length - len(row.encoded) for row in rows),
            "changed_byte_offsets": changed_offsets,
            "file_size_preserved": len(source) == len(output),
            "all_original_raw_verified": True,
            "all_original_terminating_nuls_preserved": True,
            "changes_confined_to_allowlisted_spans": True,
        },
        "patches": [
            {
                "line": row.line,
                "id": row.row_id,
                "offset": row.offset,
                "offset_hex": f"0x{row.offset:X}",
                "byte_length": row.byte_length,
                "source_raw_hex": row.raw.hex().upper(),
                **({"source_text": row.source_text} if row.source_text is not None else {}),
                "translation_ko": row.translation_ko,
                "encoded_hex": row.encoded.hex().upper(),
                "encoded_byte_length": len(row.encoded),
                "zero_padding_bytes": row.byte_length - len(row.encoded),
                "terminator_offset": row.end,
                "terminator_preserved": True,
            }
            for row in rows
        ],
        "errors": [],
    }


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_json_atomic(path: Path, value: Any) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    write_atomic(path, payload)


def patch_file(
    source_path: Path,
    translations_path: Path,
    codebook_path: Path,
    output_path: Path,
    report_path: Path,
    expected_source_sha256: str,
    encoder_path: Path,
) -> dict[str, Any]:
    source_resolved = source_path.resolve()
    output_resolved = output_path.resolve()
    report_resolved = report_path.resolve()
    require(source_path.is_file(), f"source main.dol does not exist: {source_path}")
    require(codebook_path.is_file(), f"codebook does not exist: {codebook_path}")
    require(encoder_path.is_file(), f"encoder does not exist: {encoder_path}")
    require(output_resolved != source_resolved, "refusing to overwrite the source main.dol")
    require(report_resolved not in {source_resolved, output_resolved}, "report path collides with source or output")

    expected_sha = parse_expected_sha(expected_source_sha256)
    try:
        codebook = json.loads(codebook_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PatchError(f"cannot read codebook: {exc}") from exc
    require(isinstance(codebook, dict), "codebook root must be an object")
    require(codebook.get("format") == CODEBOOK_FORMAT, f"unsupported codebook format: {codebook.get('format')!r}")
    require(isinstance(codebook.get("characters"), dict), "codebook characters map is missing")

    encoder = load_module("arf_main_dol_euc28_encoder", encoder_path)
    require(callable(getattr(encoder, "encode_text", None)), "encoder has no encode_text function")
    raw_rows = read_jsonl(translations_path)
    rows = normalize_rows(raw_rows, codebook, encoder)
    source = source_path.read_bytes()
    validate_source(source, rows, expected_sha)
    output = apply_rows(source, rows)
    report = build_report(
        source_path,
        translations_path,
        codebook_path,
        encoder_path,
        output_path,
        source,
        output,
        rows,
    )

    # Write the binary first and the report last.  The report is therefore a
    # completion marker and binds the exact bytes present on disk.
    write_atomic(output_path, output)
    require(sha256_file(output_path) == report["output"]["sha256"], "output hash mismatch after atomic write")
    write_json_atomic(report_path, report)
    return report


def build_parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="trusted original main.dol")
    parser.add_argument("translations", type=Path, help="reviewed fixed-field translation JSONL")
    parser.add_argument("codebook", type=Path, help="frozen final EUC28 codebook JSON")
    parser.add_argument("output", type=Path, help="patched main.dol output (must differ from source)")
    parser.add_argument("report", type=Path, help="JSON provenance/verification report")
    parser.add_argument("--expected-source-sha256", required=True, help="trusted original main.dol SHA-256")
    parser.add_argument(
        "--encoder",
        type=Path,
        default=root / "encode_custom_euc28.py",
        help="existing project encoder (default: adjacent encode_custom_euc28.py)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = patch_file(
            args.source,
            args.translations,
            args.codebook,
            args.output,
            args.report,
            args.expected_source_sha256,
            args.encoder,
        )
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "valid": True,
                "patch_rows": report["summary"]["patch_rows"],
                "source_sha256": report["source"]["sha256"],
                "output_sha256": report["output"]["sha256"],
                "report": str(args.report),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
