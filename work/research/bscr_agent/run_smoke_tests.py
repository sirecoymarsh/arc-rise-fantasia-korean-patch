#!/usr/bin/env python3
"""Fast representative BSCR regression tests (no full-disc traversal)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from bscr_tool import BscrError, parse_bscr


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expect_rejected(callback, phrase: str) -> None:
    try:
        callback()
    except BscrError as exc:
        assert phrase in str(exc), str(exc)
    else:
        raise AssertionError(f"expected BscrError containing {phrase!r}")


def main() -> None:
    event_source = (FIXTURES / "event_fc_00_001.original.bscr").read_bytes()
    map_source = (FIXTURES / "map_t_jad_00.original.bscr").read_bytes()
    event = parse_bscr(event_source)
    map_file = parse_bscr(map_source)

    assert event.rebuild({}) == event_source
    assert map_file.rebuild({}) == map_source
    assert digest(event_source) == "84f9b5e301a916c2927c35c341eb55ee5526aa2f6eec745ee97237dc062fa6c2"
    assert digest(map_source) == "211c51ef804bcce28f9f9de459a93542353bfe553ac297d9cc4465586fd606a0"

    changed = event.rebuild({0x2F: event.string_by_offset[0x2F].raw + b"!!"})
    changed_parsed = parse_bscr(changed)
    assert len(changed) == len(event_source) + 4
    assert changed_parsed.bytecode_start == event.bytecode_start + 4
    assert changed_parsed.rebuild({0x2F: event.string_by_offset[0x2F].raw}) == event_source

    # `FC_END` is a proven 0x8100F3F2 call target and must be protected.
    expect_rejected(lambda: event.rebuild({0x2A4: b"FC_STOP"}), "protected VM call target")
    # Speaker metadata is structural, not translatable prose.
    expect_rejected(lambda: event.rebuild({0x2B: b"\x19" + b"01"}), "changes structural controls")
    # Embedded NUL would split the table and must be rejected.
    expect_rejected(lambda: event.rebuild({0x2F: b"bad\0value"}), "embedded NUL")

    print("PASS: representative parse/no-op, length-change, reversal, and safety guards")


if __name__ == "__main__":
    main()
