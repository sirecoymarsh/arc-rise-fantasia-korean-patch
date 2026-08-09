#!/usr/bin/env python3
"""Read-only structural audit for the localized Arc Rise Fantasia item.bin."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work/pristine/Sys/system.vol/item.bin"
FINAL = ROOT / "work/final_system_table_application/payloads/item.bin"
EARLY = ROOT / "work/system_table_application/payloads/item.bin"
CATALOG = ROOT / "work/final_system_table_application/replacement_catalogs/item.json"
EARLY_CATALOG = ROOT / "work/system_table_application/replacement_catalogs/item.json"
CODEBOOK = ROOT / "work/font/final_v2/codebook.json"
OUTPUT = ROOT / "work/runtime_validation/item_static_audit.json"
CANDIDATE = ROOT / "work/runtime_validation/item_metadata_repaired_candidate.bin"

RECORD_SIZE = 255
RECORD_COUNT = 772
FIELDS = {
    "name": (0, 17),
    "description_primary": (17, 81),
    "description_secondary": (98, 82),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def logical(blob: bytes) -> tuple[bytes, int | None]:
    pos = blob.find(b"\0")
    return (blob if pos < 0 else blob[:pos], None if pos < 0 else pos)


def control_signature(raw: bytes) -> list[str]:
    result: list[str] = []
    i = 0
    while i < len(raw):
        value = raw[i]
        if value in (0x09, 0x0A, 0x0D):
            i += 1
            continue
        if 0x01 <= value <= 0x1F or value == 0x7F:
            end = i + 1
            if value in (0x13, 0x15) and end + 2 <= len(raw) and all(
                chr(b) in "0123456789ABCDEFabcdef" for b in raw[end : end + 2]
            ):
                end += 2
            elif value == 0x1F:
                while end < len(raw) and 0x30 <= raw[end] <= 0x39:
                    end += 1
            result.append(raw[i:end].hex().upper())
            i = end
            continue
        if 0xA1 <= value <= 0xFE and i + 1 < len(raw) and 0xA1 <= raw[i + 1] <= 0xFE:
            i += 2
        elif value == 0x8E and i + 1 < len(raw):
            i += 2
        elif value == 0x8F and i + 2 < len(raw):
            i += 3
        else:
            i += 1
    return result


def strict_units(raw: bytes) -> tuple[list[bytes], list[dict]]:
    units: list[bytes] = []
    errors: list[dict] = []
    i = 0
    while i < len(raw):
        b = raw[i]
        if b <= 0x7F:
            units.append(raw[i : i + 1])
            i += 1
        elif 0xA1 <= b <= 0xFE:
            if i + 1 >= len(raw) or not 0xA1 <= raw[i + 1] <= 0xFE:
                errors.append({"relative_offset": i, "bytes_hex": raw[i : i + 2].hex().upper()})
                i += 1
            else:
                units.append(raw[i : i + 2])
                i += 2
        elif b == 0x8E:
            if i + 1 >= len(raw) or not 0xA1 <= raw[i + 1] <= 0xDF:
                errors.append({"relative_offset": i, "bytes_hex": raw[i : i + 2].hex().upper()})
                i += 1
            else:
                units.append(raw[i : i + 2])
                i += 2
        elif b == 0x8F:
            if i + 2 >= len(raw) or not (0xA1 <= raw[i + 1] <= 0xFE and 0xA1 <= raw[i + 2] <= 0xFE):
                errors.append({"relative_offset": i, "bytes_hex": raw[i : i + 3].hex().upper()})
                i += 1
            else:
                units.append(raw[i : i + 3])
                i += 3
        else:
            errors.append({"relative_offset": i, "bytes_hex": f"{b:02X}"})
            i += 1
    return units, errors


def ascii_tokens(raw: bytes) -> list[str]:
    # Potential formatting/lookup syntax; whitespace and prose ASCII are ignored.
    text = "".join(chr(b) if 0x20 <= b <= 0x7E else " " for b in raw)
    return re.findall(r"%[-+0-9.#]*[A-Za-z]|\\[A-Za-z]|\{[^{}]+\}|\[[^\[\]]+\]|<[^<>]+>|\$[A-Za-z0-9_]+", text)


def decode_custom(raw: bytes, reverse: dict[bytes, str]) -> str:
    out: list[str] = []
    i = 0
    while i < len(raw):
        if i + 1 < len(raw) and raw[i : i + 2] in reverse:
            out.append(reverse[raw[i : i + 2]])
            i += 2
            continue
        b = raw[i]
        if b <= 0x7F:
            out.append(chr(b))
            i += 1
            continue
        if 0xA1 <= b <= 0xFE and i + 1 < len(raw) and 0xA1 <= raw[i + 1] <= 0xFE:
            try:
                out.append(raw[i : i + 2].decode("euc_jp"))
            except UnicodeDecodeError:
                out.append(f"<#{raw[i:i+2].hex().upper()}>")
            i += 2
            continue
        out.append(f"<#{b:02X}>")
        i += 1
    return "".join(out)


def main() -> int:
    src = SOURCE.read_bytes()
    out = FINAL.read_bytes()
    early = EARLY.read_bytes() if EARLY.exists() else b""
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    early_cat = json.loads(EARLY_CATALOG.read_text(encoding="utf-8")) if EARLY_CATALOG.exists() else {"units": []}
    codebook = json.loads(CODEBOOK.read_text(encoding="utf-8"))
    reverse = {bytes.fromhex(entry["bytes_hex"]): char for char, entry in codebook["characters"].items()}
    pair_dupes = defaultdict(list)
    for char, entry in codebook["characters"].items():
        pair_dupes[entry["bytes_hex"].upper()].append(char)

    assert len(src) == len(out) == RECORD_SIZE * RECORD_COUNT
    units_by_id = {unit["id"]: unit for unit in cat["units"]}
    early_by_id = {unit["id"]: unit for unit in early_cat["units"]}

    changed_offsets = [i for i, (a, b) in enumerate(zip(src, out)) if a != b]
    opaque_changed: list[dict] = []
    unterminated: list[dict] = []
    strict_errors: list[dict] = []
    signature_errors: list[dict] = []
    padding_destroyed: list[dict] = []
    ascii_token_changes: list[dict] = []
    catalog_output_mismatch: list[dict] = []
    codebook_usage: Counter[str] = Counter()
    noncodebook_pairs: Counter[str] = Counter()
    field_summary: dict[str, Counter] = {name: Counter() for name in FIELDS}
    new_since_early: list[dict] = []
    near_capacity: list[dict] = []

    for record in range(RECORD_COUNT):
        base = record * RECORD_SIZE
        if src[base + 179 : base + RECORD_SIZE] != out[base + 179 : base + RECORD_SIZE]:
            diffs = [
                base + pos
                for pos, (a, b) in enumerate(zip(src[base + 179 : base + RECORD_SIZE], out[base + 179 : base + RECORD_SIZE]), 179)
                if a != b
            ]
            opaque_changed.append({"record": record, "absolute_offsets": diffs})

        for field, (rel, cap) in FIELDS.items():
            ident = f"item:{record}:{field}"
            sblob = src[base + rel : base + rel + cap]
            oblob = out[base + rel : base + rel + cap]
            sraw, snul = logical(sblob)
            oraw, onul = logical(oblob)
            summary = field_summary[field]
            summary["fields"] += 1
            summary["changed"] += sblob != oblob
            summary["logical_changed"] += sraw != oraw
            summary["output_empty"] += not oraw
            summary["output_bytes"] += len(oraw)
            summary["source_bytes"] += len(sraw)
            if onul is None:
                unterminated.append({"id": ident, "absolute_offset": base + rel, "capacity": cap})
            if len(oraw) >= cap - 2:
                near_capacity.append({
                    "id": ident,
                    "length": len(oraw),
                    "capacity": cap,
                    "headroom_before_nul": cap - len(oraw) - 1,
                    "source_text": units_by_id[ident]["source_text"],
                    "output_text": decode_custom(oraw, reverse),
                    "output_hex": oraw.hex().upper(),
                })
            parsed_units, errors = strict_units(oraw)
            for error in errors:
                strict_errors.append({"id": ident, "absolute_offset": base + rel + error["relative_offset"], **error})
            for token in parsed_units:
                if len(token) == 2 and 0xA1 <= token[0] <= 0xFE and 0xA1 <= token[1] <= 0xFE:
                    hx = token.hex().upper()
                    if token in reverse:
                        codebook_usage[hx] += 1
                    else:
                        noncodebook_pairs[hx] += 1
            expected_sig = control_signature(sraw)
            actual_sig = control_signature(oraw)
            if actual_sig != expected_sig:
                signature_errors.append({"id": ident, "source": expected_sig, "output": actual_sig})
            if sblob != oblob and snul is not None:
                nonzero_after_nul = [(i, b) for i, b in enumerate(sblob[snul + 1 :], snul + 1) if b]
                erased = [(i, b) for i, b in nonzero_after_nul if oblob[i] == 0]
                if erased:
                    padding_destroyed.append({
                        "id": ident,
                        "source_nul_at": snul,
                        "erased_nonzero_bytes": [{"relative_offset": i, "value_hex": f"{b:02X}"} for i, b in erased],
                    })
            stokens = ascii_tokens(sraw)
            otokens = ascii_tokens(oraw)
            if stokens != otokens:
                ascii_token_changes.append({
                    "id": ident,
                    "source_tokens": stokens,
                    "output_tokens": otokens,
                    "source_text": units_by_id[ident]["source_text"],
                    "output_text": decode_custom(oraw, reverse),
                })

            cu = units_by_id[ident]
            replacement = bytes.fromhex(cu.get("replacement_hex", "")) if cu.get("replacement_hex") else sraw
            expected_blob = replacement + b"\0" * (cap - len(replacement)) if replacement != sraw else sblob
            if oblob != expected_blob:
                catalog_output_mismatch.append({"id": ident})

            eu = early_by_id.get(ident)
            if cu.get("replacement_hex") and (not eu or not eu.get("replacement_hex")):
                new_since_early.append({
                    "id": ident,
                    "record": record,
                    "field": field,
                    "source_text": cu["source_text"],
                    "output_text": decode_custom(oraw, reverse),
                    "length": len(oraw),
                    "capacity": cap,
                    "output_hex": oraw.hex().upper(),
                })

    # Pairs in custom map must be legal two-byte table coordinates and unique.
    invalid_codebook_entries = []
    for char, entry in codebook["characters"].items():
        raw = bytes.fromhex(entry["bytes_hex"])
        if len(raw) != 2 or not (0xA1 <= raw[0] <= 0xFE and 0xA1 <= raw[1] <= 0xFE):
            invalid_codebook_entries.append({"character": char, "bytes_hex": entry["bytes_hex"]})

    # Independently simulate the writer with the proven 81-byte secondary array.
    candidate = bytearray(src)
    corrected_capacities = {"name": 17, "description_primary": 81, "description_secondary": 81}
    for unit in cat["units"]:
        if not unit.get("replacement_hex"):
            continue
        raw = bytes.fromhex(unit["replacement_hex"])
        cap = corrected_capacities[unit["field"]]
        if len(raw) >= cap:
            raise ValueError(f"{unit['id']}: {len(raw)} does not fit corrected capacity {cap}")
        start = int(unit["offset"])
        candidate[start : start + cap] = b"\0" * cap
        candidate[start : start + len(raw)] = raw
    candidate = bytes(candidate)
    CANDIDATE.write_bytes(candidate)

    def item_id_summary(data: bytes) -> dict:
        ids: dict[int, list[int]] = defaultdict(list)
        for record in range(RECORD_COUNT):
            item_id = int.from_bytes(data[record * RECORD_SIZE + 179 : record * RECORD_SIZE + 181], "big")
            ids[item_id].append(record)
        duplicates = {f"0x{item_id:04X}": records for item_id, records in ids.items() if len(records) > 1}
        return {
            "unique_count": len(ids),
            "duplicate_id_count": len(duplicates),
            "records_participating_in_duplicates": sum(len(records) for records in duplicates.values()),
            "duplicates": duplicates,
        }

    report = {
        "schema": "arf-item-static-audit-v1",
        "inputs": {
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": sha(src),
            "final": str(FINAL.relative_to(ROOT)),
            "final_sha256": sha(out),
            "early": str(EARLY.relative_to(ROOT)),
            "early_sha256": sha(early) if early else None,
            "size": len(src),
        },
        "geometry": {
            "record_size": RECORD_SIZE,
            "record_count": RECORD_COUNT,
            "fields": {name: {"offset": off, "capacity": cap} for name, (off, cap) in FIELDS.items()},
            "actual_secondary_capacity": 81,
            "metadata_tail": {"offset": 179, "size": 76},
            "item_id": {"offset": 179, "size": 2, "byte_order": "big"},
        },
        "byte_diff": {
            "changed_byte_count": len(changed_offsets),
            "first_changed_offset": min(changed_offsets) if changed_offsets else None,
            "last_changed_offset": max(changed_offsets) if changed_offsets else None,
            "opaque_tail_changed_record_count": len(opaque_changed),
            "opaque_tail_changes": opaque_changed,
        },
        "item_ids": {
            "source": item_id_summary(src),
            "early": item_id_summary(early),
            "final": item_id_summary(out),
            "corrected_candidate": item_id_summary(candidate),
            "source_high_byte_distribution": dict(sorted(Counter(src[r * RECORD_SIZE + 179] for r in range(RECORD_COUNT)).items())),
            "final_high_byte_distribution": dict(sorted(Counter(out[r * RECORD_SIZE + 179] for r in range(RECORD_COUNT)).items())),
        },
        "fields": {name: dict(counter) for name, counter in field_summary.items()},
        "checks": {
            "unterminated_field_count": len(unterminated),
            "unterminated_fields": unterminated,
            "invalid_byte_sequence_count": len(strict_errors),
            "invalid_byte_sequences": strict_errors,
            "control_signature_mismatch_count": len(signature_errors),
            "control_signature_mismatches": signature_errors,
            "catalog_output_mismatch_count": len(catalog_output_mismatch),
            "catalog_output_mismatches": catalog_output_mismatch,
            "source_nonzero_padding_erased_field_count": len(padding_destroyed),
            "source_nonzero_padding_erased_fields": padding_destroyed,
            "potential_ascii_token_change_count": len(ascii_token_changes),
            "potential_ascii_token_changes": ascii_token_changes,
            "near_capacity_field_count": len(near_capacity),
            "near_capacity_fields": near_capacity,
        },
        "codebook": {
            "assigned": len(codebook["characters"]),
            "unique_byte_pairs": len(pair_dupes),
            "duplicate_pair_count": sum(1 for chars in pair_dupes.values() if len(chars) > 1),
            "duplicate_pairs": {pair: chars for pair, chars in pair_dupes.items() if len(chars) > 1},
            "invalid_entry_count": len(invalid_codebook_entries),
            "invalid_entries": invalid_codebook_entries,
            "used_custom_pair_count": len(codebook_usage),
            "used_custom_pair_occurrences": sum(codebook_usage.values()),
            "noncodebook_euc_pair_count": len(noncodebook_pairs),
            "noncodebook_euc_pair_occurrences": sum(noncodebook_pairs.values()),
        },
        "regression_delta": {
            "early_replacement_fields": sum(bool(u.get("replacement_hex")) for u in early_cat.get("units", [])),
            "final_replacement_fields": sum(bool(u.get("replacement_hex")) for u in cat["units"]),
            "newly_replaced_field_count": len(new_since_early),
            "newly_replaced_fields": new_since_early,
        },
        "corrected_schema_candidate": {
            "path": str(CANDIDATE.relative_to(ROOT)),
            "sha256": sha(candidate),
            "differences_from_broken_final": sum(a != b for a, b in zip(candidate, out)),
            "differences_from_source": sum(a != b for a, b in zip(candidate, src)),
            "metadata_tail_exactly_preserved": all(
                candidate[r * RECORD_SIZE + 179 : (r + 1) * RECORD_SIZE]
                == src[r * RECORD_SIZE + 179 : (r + 1) * RECORD_SIZE]
                for r in range(RECORD_COUNT)
            ),
            "byte_equivalent_to_restoring_offset_179": all(
                candidate[i] == (src[i] if i % RECORD_SIZE == 179 else out[i])
                for i in range(len(src))
            ),
        },
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "source_sha256": sha(src),
        "final_sha256": sha(out),
        "changed_bytes": len(changed_offsets),
        "field_summary": report["fields"],
        "check_counts": {k: v for k, v in report["checks"].items() if k.endswith("_count")},
        "codebook": report["codebook"],
        "newly_replaced_fields": len(new_since_early),
        "final_item_ids": report["item_ids"]["final"],
        "candidate": report["corrected_schema_candidate"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
