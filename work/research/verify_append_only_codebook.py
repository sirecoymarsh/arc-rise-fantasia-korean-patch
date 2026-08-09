#!/usr/bin/env python3
"""Verify that an ARF Korean codebook is a collision-free append-only extension."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("existing", type=Path)
    parser.add_argument("extended", type=Path)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("reserved_hex", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    existing = json.loads(args.existing.read_text(encoding="utf-8"))
    extended = json.loads(args.extended.read_text(encoding="utf-8"))
    old_characters = existing["characters"]
    new_characters = extended["characters"]
    reserved = {
        token.strip().upper()
        for token in args.reserved_hex.read_text(encoding="utf-8").split()
        if token.strip()
    }
    corpus = args.corpus.read_text(encoding="utf-8")
    required_hangul = {
        char
        for char in corpus
        if ("가" <= char <= "힣")
        or ("㄰" <= char <= "㆏")
        or ("ᄀ" <= char <= "ᇿ")
    }
    required_custom = set(required_hangul)
    for char in set(corpus):
        try:
            char.encode("euc_jp")
        except UnicodeEncodeError:
            required_custom.add(char)

    changed_existing = sorted(
        char
        for char, record in old_characters.items()
        if new_characters.get(char) != record
    )
    missing_required = sorted(required_custom - set(new_characters), key=ord)
    pairs = [str(record["bytes_hex"]).upper() for record in new_characters.values()]
    duplicate_pair_count = len(pairs) - len(set(pairs))
    reserved_collisions = sorted(set(pairs) & reserved)
    declared_assigned = int(extended["assigned"])
    capacity_ok = declared_assigned <= int(extended["available_after_reservations"])
    errors = []
    if changed_existing:
        errors.append(
            {
                "code": "existing_assignment_changed_or_missing",
                "count": len(changed_existing),
                "sample": changed_existing[:20],
            }
        )
    if missing_required:
        errors.append(
            {
                "code": "required_custom_glyph_missing",
                "count": len(missing_required),
                "sample": missing_required[:20],
            }
        )
    if duplicate_pair_count:
        errors.append({"code": "duplicate_byte_pairs", "count": duplicate_pair_count})
    if reserved_collisions:
        errors.append(
            {
                "code": "reserved_pair_collision",
                "count": len(reserved_collisions),
                "sample": reserved_collisions[:20],
            }
        )
    if declared_assigned != len(new_characters):
        errors.append(
            {
                "code": "assigned_count_mismatch",
                "declared": declared_assigned,
                "actual": len(new_characters),
            }
        )
    if not capacity_ok:
        errors.append({"code": "allocation_capacity_exceeded"})

    report = {
        "schema": "arf-append-only-codebook-verification-v1",
        "translation_engine_policy": "Codex internal models only",
        "existing_codebook_sha256": sha256(args.existing),
        "extended_codebook_sha256": sha256(args.extended),
        "corpus_sha256": sha256(args.corpus),
        "reserved_hex_sha256": sha256(args.reserved_hex),
        "existing_assigned": len(old_characters),
        "extended_assigned": len(new_characters),
        "appended_characters": len(new_characters) - len(old_characters),
        "required_hangul": len(required_hangul),
        "required_custom_glyphs": len(required_custom),
        "missing_required_custom_glyphs": len(missing_required),
        "existing_assignments_changed": len(changed_existing),
        "reserved_source_pairs": len(reserved),
        "reserved_pair_collisions": len(reserved_collisions),
        "duplicate_pair_count": duplicate_pair_count,
        "available_after_reservations": int(extended["available_after_reservations"]),
        "capacity_ok": capacity_ok,
        "error_count": len(errors),
        "errors": errors,
        "valid": not errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
