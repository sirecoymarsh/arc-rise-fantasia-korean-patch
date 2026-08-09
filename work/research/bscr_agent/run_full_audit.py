#!/usr/bin/env python3
"""Run the RPJJ99-wide BSCR structural and rebuild proof suite."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

from bscr_tool import POINTER_OPCODES, control_tokens, parse_bscr, structural_control_signature
from explore_bscr import iter_bscr


HERE = Path(__file__).resolve().parent
WORKSPACE = Path(__file__).resolve().parents[3]
DISC_ROOT = WORKSPACE / "work" / "disc_extracted" / "DATA" / "files"
FIXTURES = HERE / "fixtures"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def string_offset_map(parsed, replacements: dict[int, bytes]) -> dict[int, int]:
    cursor = 0
    result: dict[int, int] = {}
    for record in parsed.strings:
        result[record.relative_offset] = cursor
        cursor += len(replacements.get(record.relative_offset, record.raw)) + 1
    return result


def length_change_proof(name: str, source: bytes, target_offset: int, suffix: bytes) -> dict[str, object]:
    parsed = parse_bscr(source)
    target = parsed.string_by_offset[target_offset]
    if "call_target" in target.roles:
        raise AssertionError("probe target unexpectedly has call-target role")
    replacement = target.raw + suffix
    replacements = {target_offset: replacement}
    offsets = string_offset_map(parsed, replacements)
    rebuilt = parsed.rebuild(replacements)
    reparsed = parse_bscr(rebuilt)

    assert reparsed.strings[target.index].raw == replacement
    assert len(reparsed.descriptors) == len(parsed.descriptors)
    assert all(old.raw == new.raw for old, new in zip(parsed.descriptors, reparsed.descriptors, strict=True))
    assert parsed.variant_tag == reparsed.variant_tag
    assert parsed.file_name == reparsed.file_name
    assert parsed.pool_start == reparsed.pool_start
    assert parsed.bytecode_size == reparsed.bytecode_size
    assert len(parsed.cells) == len(reparsed.cells)

    patched_pointer_cells = 0
    changed_pointer_cells = 0
    non_pointer_cells_identical = True
    for old_cell, new_cell in zip(parsed.cells, reparsed.cells, strict=True):
        assert old_cell.opcode == new_cell.opcode
        assert old_cell.tail == new_cell.tail
        if old_cell.opcode in POINTER_OPCODES:
            expected = offsets[old_cell.operand]
            assert new_cell.operand == expected
            patched_pointer_cells += 1
            if old_cell.operand != new_cell.operand:
                changed_pointer_cells += 1
        elif old_cell.operand != new_cell.operand:
            non_pointer_cells_identical = False
    assert non_pointer_cells_identical

    # Reversibility proof: replace the same logical record in the changed file
    # with the original bytes and require byte identity with the source.
    new_target_offset = reparsed.strings[target.index].relative_offset
    restored = reparsed.rebuild({new_target_offset: target.raw})
    assert restored == source

    FIXTURES.mkdir(parents=True, exist_ok=True)
    original_path = FIXTURES / f"{name}.original.bscr"
    noop_path = FIXTURES / f"{name}.noop.bscr"
    changed_path = FIXTURES / f"{name}.length_changed.bscr"
    restored_path = FIXTURES / f"{name}.restored.bscr"
    original_path.write_bytes(source)
    noop = parsed.rebuild({})
    noop_path.write_bytes(noop)
    changed_path.write_bytes(rebuilt)
    restored_path.write_bytes(restored)
    assert noop == source

    old_header = {
        "file_size": len(parsed.data),
        "string_count": parsed.string_count,
        "pool_start": parsed.pool_start,
        "bytecode_size": parsed.bytecode_size,
        "bytecode_start": parsed.bytecode_start,
    }
    new_header = {
        "file_size": len(reparsed.data),
        "string_count": reparsed.string_count,
        "pool_start": reparsed.pool_start,
        "bytecode_size": reparsed.bytecode_size,
        "bytecode_start": reparsed.bytecode_start,
    }
    return {
        "name": name,
        "source_sha256": sha256(source),
        "noop_sha256": sha256(noop),
        "noop_byte_exact": noop == source,
        "changed_sha256": sha256(rebuilt),
        "restored_sha256": sha256(restored),
        "restored_byte_exact": restored == source,
        "target_index": target.index,
        "old_target_offset": target_offset,
        "new_target_offset": new_target_offset,
        "old_target_length": len(target.raw),
        "new_target_length": len(replacement),
        "old_structural_controls": structural_control_signature(target.raw),
        "new_structural_controls": structural_control_signature(replacement),
        "old_header": old_header,
        "new_header": new_header,
        "file_size_delta": len(rebuilt) - len(source),
        "bytecode_start_delta": reparsed.bytecode_start - parsed.bytecode_start,
        "pointer_cell_count": patched_pointer_cells,
        "pointer_cells_with_changed_operand": changed_pointer_cells,
        "non_pointer_cells_identical": non_pointer_cells_identical,
        "descriptors_byte_exact": all(
            old.raw == new.raw for old, new in zip(parsed.descriptors, reparsed.descriptors, strict=True)
        ),
        "paths": {
            "original": str(original_path),
            "noop": str(noop_path),
            "changed": str(changed_path),
            "restored": str(restored_path),
        },
    }


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    totals = Counter()
    variant_tags = Counter()
    descriptor_types = Counter()
    control_kinds = Counter()
    speaker_codes = Counter()
    message_style_codes = Counter()
    role_sets = Counter()
    errors: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    choice_examples: list[dict[str, object]] = []
    representative_bytes: dict[str, bytes] = {}

    for asset in iter_bscr(DISC_ROOT):
        try:
            parsed = parse_bscr(asset.data)
            noop = parsed.rebuild({})
            if noop != asset.data:
                raise AssertionError("parse -> no-op rebuild was not byte-exact")

            category = asset.physical_path.split("/", 1)[0]
            totals["assets"] += 1
            totals[f"assets:{category}"] += 1
            totals["bytes"] += len(asset.data)
            totals["descriptors"] += len(parsed.descriptors)
            totals["strings"] += len(parsed.strings)
            totals["instructions"] += len(parsed.cells)
            totals["choice_sites"] += len(parsed.choice_sites)
            totals["no_op_byte_exact"] += 1
            variant_tags[parsed.variant_tag] += 1

            for descriptor in parsed.descriptors:
                descriptor_types[f"0x{descriptor.type_code:02x}"] += 1
            for string in parsed.strings:
                role_sets["+".join(string.roles)] += 1
                totals["string_references"] += string.reference_count
                if "literal" in string.roles:
                    totals["literal_strings"] += 1
                if "call_target" in string.roles:
                    totals["call_target_strings"] += 1
                    try:
                        string.raw.decode("ascii")
                    except UnicodeDecodeError:
                        totals["non_ascii_call_targets"] += 1
                for token in control_tokens(string.raw):
                    kind = str(token["kind"])
                    control_kinds[kind] += 1
                    if token.get("well_formed") is False:
                        totals["malformed_control_tokens"] += 1
                    if kind == "speaker_slot":
                        speaker_codes[str(token.get("payload_ascii", ""))] += 1
                    if kind == "message_style":
                        message_style_codes[str(token.get("payload_ascii", ""))] += 1

            by_offset = parsed.string_by_offset
            for site in parsed.choice_sites:
                prompt = by_offset[site.prompt_offset]
                options = by_offset[site.options_offset]
                if len(choice_examples) < 24:
                    choice_examples.append(
                        {
                            "locator": asset.locator,
                            "instruction_index": site.instruction_index,
                            "prompt_offset": site.prompt_offset,
                            "prompt": prompt.decoded(),
                            "options_offset": site.options_offset,
                            "options": options.decoded().split("\n"),
                        }
                    )

            records.append(
                {
                    "locator": asset.locator,
                    "physical_path": asset.physical_path,
                    "file_name": parsed.file_name,
                    "sha256": parsed.sha256,
                    "length": len(parsed.data),
                    "variant_tag": parsed.variant_tag,
                    "descriptor_count": len(parsed.descriptors),
                    "string_count": len(parsed.strings),
                    "pool_start": parsed.pool_start,
                    "bytecode_start": parsed.bytecode_start,
                    "bytecode_size": parsed.bytecode_size,
                    "instruction_count": len(parsed.cells),
                    "choice_site_count": len(parsed.choice_sites),
                    "pool_padding_length": len(parsed.pool_padding),
                    "no_op_sha256": sha256(noop),
                    "no_op_byte_exact": True,
                }
            )

            if parsed.file_name == "fc_00_001.bscr" and "fc_00_001.vol" in asset.physical_path:
                representative_bytes.setdefault("event_fc_00_001", asset.data)
            if parsed.file_name == "map_t_jad_00.bscr":
                representative_bytes.setdefault("map_t_jad_00", asset.data)
        except Exception as exc:
            errors.append({"locator": asset.locator, "error": f"{type(exc).__name__}: {exc}"})

    if errors:
        raise AssertionError(f"full audit found {len(errors)} errors; first={errors[0]}")
    if set(representative_bytes) != {"event_fc_00_001", "map_t_jad_00"}:
        raise AssertionError(f"representative files missing: {set(representative_bytes)}")

    event_parsed = parse_bscr(representative_bytes["event_fc_00_001"])
    map_parsed = parse_bscr(representative_bytes["map_t_jad_00"])
    # Event target is the first visible line; map target is the common world-map
    # confirmation prompt.  Suffixes are ASCII probes, not translations.
    proofs = [
        length_change_proof("event_fc_00_001", event_parsed.data, 0x2F, b"!!"),
        length_change_proof("map_t_jad_00", map_parsed.data, 0x2EC, b"!"),
    ]

    result = {
        "schema": "arf-bscr-full-audit-v1",
        "game_id": "RPJJ99",
        "source_root": str(DISC_ROOT),
        "format": {
            "endianness": "big",
            "header_size": 64,
            "descriptor_start": 64,
            "vm_cell_size": 16,
            "literal_pointer_opcode_hex": "1af0f15a",
            "call_target_pointer_opcode_hex": "8100f3f2",
            "choice_opcode_sequence_hex": [value.hex() for value in (
                bytes.fromhex("82bcf35a"), bytes.fromhex("82bdf35a"), bytes.fromhex("82bef3f2")
            )],
        },
        "totals": dict(totals),
        "variant_tags": dict(sorted(variant_tags.items())),
        "descriptor_types": dict(sorted(descriptor_types.items())),
        "string_role_sets": dict(sorted(role_sets.items())),
        "control_kinds": dict(sorted(control_kinds.items())),
        "speaker_slot_codes": dict(sorted(speaker_codes.items())),
        "message_style_codes": dict(sorted(message_style_codes.items())),
        "choice_examples": choice_examples,
        "length_change_proofs": proofs,
        "error_count": len(errors),
        "errors": errors,
        "records": sorted(records, key=lambda item: str(item["locator"]).lower()),
    }
    output = HERE / "full_audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
