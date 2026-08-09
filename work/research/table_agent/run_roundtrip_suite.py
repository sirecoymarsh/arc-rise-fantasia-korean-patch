#!/usr/bin/env python3
"""Generate catalogs and byte-exact no-op proofs for every mapped table."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from arf_table_tool import apply_catalog, make_catalog, sha256, write_json


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SYSTEM = ROOT / "work/pristine/Sys/system.vol"


CASES: list[tuple[str, Path, str | None]] = [
    (name.removesuffix(".bin").removesuffix(".dat"), SYSTEM / name, None)
    for name in (
        "item.bin", "shop.bin", "dragon.bin", "treasure.bin", "magic.bin", "special.bin",
        "operation.bin", "quest.bin", "ability.bin", "chat.bin", "todo.dat",
    )
]
CASES += [
    ("copin", HERE / "mg_copin_entries/copin.dat", "copin"),
    ("help", ROOT / "work/disc_extracted/DATA/files/Sys/help.bin", None),
    ("monster_book", ROOT / "work/disc_extracted/DATA/files/Sys/monster_book.bin", None),
    ("btl_tutorial", ROOT / "work/disc_extracted/DATA/files/Btl/btl_tutorial.vld", None),
]
for path in sorted((HERE / "btl_status_entries").glob("btl_stat_party*.bin")):
    CASES.append((path.stem, path, "btem"))


def main() -> int:
    catalogs = HERE / "catalogs"
    outputs = HERE / "noop_outputs"
    catalogs.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    results = []
    all_exact = True
    for label, path, forced in CASES:
        source = path.read_bytes()
        catalog = make_catalog(path, source, forced)
        rebuilt = apply_catalog(source, catalog, rebuild_all=True)
        exact = rebuilt == source
        all_exact &= exact
        write_json(catalogs / f"{label}.json", catalog)
        (outputs / path.name).write_bytes(rebuilt)
        results.append({
            "label": label,
            "source": str(path.resolve()),
            "schema": catalog["schema"],
            "size": len(source),
            "sha256": sha256(source),
            "unit_count": catalog["unit_count"],
            "nonempty_count": catalog["nonempty_count"],
            "japanese_unit_count": catalog["japanese_unit_count"],
            "control_unit_count": sum(bool(u["control_signature"]) for u in catalog["units"]),
            "no_op_size": len(rebuilt),
            "no_op_sha256": sha256(rebuilt),
            "byte_exact": exact,
        })

    # Controlled table-level resize proof for quest.bin.
    quest_path = SYSTEM / "quest.bin"
    qsource = quest_path.read_bytes()
    qcat = make_catalog(quest_path, qsource)
    qedit = copy.deepcopy(qcat)
    first = qedit["units"][0]
    original_first = bytes.fromhex(first["raw_hex"])
    first["replacement_hex"] = b"TEST".hex().upper()
    qout = apply_catalog(qsource, qedit, rebuild_all=False)
    qparsed = make_catalog(HERE / "quest_resize_fixture.bin", qout, "quest")
    qfirst = bytes.fromhex(qparsed["units"][0]["raw_hex"])
    rest_equal = all(
        a["raw_hex"] == b["raw_hex"]
        for a, b in zip(qcat["units"][1:], qparsed["units"][1:])
    )
    (HERE / "edit_fixtures/quest_resize_fixture.bin").parent.mkdir(parents=True, exist_ok=True)
    (HERE / "edit_fixtures/quest_resize_fixture.bin").write_bytes(qout)
    quest_resize = {
        "source_size": len(qsource),
        "edited_size": len(qout),
        "expected_delta": 4 - len(original_first),
        "actual_delta": len(qout) - len(qsource),
        "first_string_became_hex": qfirst.hex().upper(),
        "all_other_479_strings_unchanged": rest_equal,
        "reparsed_record_count": qparsed["metadata"]["record_count"],
        "reparsed_pool_gap_count": qparsed["metadata"]["pool_gap_count"],
        "passed": qfirst == b"TEST" and rest_equal and len(qout) - len(qsource) == 4 - len(original_first),
    }

    # Conservative same-payload-size mode for the currently fixed-layout RTDP
    # parent writer: each string may shrink/change within its original slot.
    qfixed = apply_catalog(qsource, qedit, rebuild_all=False, quest_fixed_size=True)
    qfixed_parsed = make_catalog(HERE / "quest_fixed_size_fixture.bin", qfixed, "quest")
    qfixed_first = bytes.fromhex(qfixed_parsed["units"][0]["raw_hex"])
    qfixed_rest_equal = all(
        a["raw_hex"] == b["raw_hex"]
        for a, b in zip(qcat["units"][1:], qfixed_parsed["units"][1:])
    )
    original_reloc_bytes = qsource[0x14 : 0x14 + qcat["metadata"]["relocation_count"] * 8]
    fixed_reloc_bytes = qfixed[0x14 : 0x14 + qcat["metadata"]["relocation_count"] * 8]
    quest_fixed_size = {
        "source_size": len(qsource),
        "edited_size": len(qfixed),
        "first_string_became_hex": qfixed_first.hex().upper(),
        "all_other_479_strings_unchanged": qfixed_rest_equal,
        "all_relocation_entries_unchanged": original_reloc_bytes == fixed_reloc_bytes,
        "zero_padding_gap_count": qfixed_parsed["metadata"]["pool_gap_count"],
        "zero_padding_gap_bytes": qfixed_parsed["metadata"]["pool_gap_bytes"],
        "passed": (
            len(qfixed) == len(qsource)
            and qfixed_first == b"TEST"
            and qfixed_rest_equal
            and original_reloc_bytes == fixed_reloc_bytes
        ),
    }
    (HERE / "edit_fixtures/quest_fixed_size_fixture.bin").write_bytes(qfixed)

    # A fixed-layout shorter edit must remain the same size and stay confined
    # to the declared field.  operation[0].name has no runtime token.
    op_path = SYSTEM / "operation.bin"
    osource = op_path.read_bytes()
    ocat = make_catalog(op_path, osource)
    oedit = copy.deepcopy(ocat)
    target = oedit["units"][0]
    target["replacement_hex"] = b"TEST".hex().upper()
    oout = apply_catalog(osource, oedit, rebuild_all=False)
    diffs = [i for i, (a, b) in enumerate(zip(osource, oout)) if a != b]
    field_start, field_end = target["offset"], target["offset"] + target["capacity"]
    fixed_edit = {
        "source_size": len(osource),
        "edited_size": len(oout),
        "diff_count": len(diffs),
        "diff_min": min(diffs) if diffs else None,
        "diff_max": max(diffs) if diffs else None,
        "declared_field": [field_start, field_end],
        "all_diffs_inside_declared_field": bool(diffs) and all(field_start <= x < field_end for x in diffs),
        "passed": len(osource) == len(oout) and bool(diffs) and all(field_start <= x < field_end for x in diffs),
    }
    (HERE / "edit_fixtures/operation_shorter_fixture.bin").write_bytes(oout)

    # Negative guards.
    guards = {}
    overflow = copy.deepcopy(ocat)
    overflow["units"][0]["replacement_hex"] = (b"A" * int(target["capacity"])).hex().upper()
    try:
        apply_catalog(osource, overflow, rebuild_all=False)
    except ValueError as exc:
        guards["fixed_capacity_overflow_rejected"] = str(exc)
    control = copy.deepcopy(qcat)
    controlled = next(u for u in control["units"] if u["control_signature"])
    controlled["replacement_hex"] = b"BROKEN".hex().upper()
    try:
        apply_catalog(qsource, control, rebuild_all=False)
    except ValueError as exc:
        guards["control_signature_change_rejected"] = str(exc)

    proof = {
        "format": "arf-table-roundtrip-proof-v1",
        "game_id": "RPJJ99",
        "case_count": len(results),
        "all_no_op_byte_exact": all_exact,
        "cases": results,
        "controlled_quest_resize": quest_resize,
        "controlled_quest_fixed_size": quest_fixed_size,
        "controlled_fixed_edit": fixed_edit,
        "negative_guards": guards,
        "suite_passed": (
            all_exact and quest_resize["passed"] and quest_fixed_size["passed"]
            and fixed_edit["passed"] and len(guards) == 2
        ),
    }
    write_json(HERE / "roundtrip_proof.json", proof)
    print(json.dumps({"cases": len(results), "all_exact": all_exact, "suite_passed": proof["suite_passed"]}))
    return 0 if proof["suite_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
