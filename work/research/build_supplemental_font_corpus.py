#!/usr/bin/env python3
"""Build the UTF-8 corpus needed by late runtime text patches.

This helper deliberately performs no translation.  It only copies already
approved Korean display strings into a plain-text corpus for the append-only
EUC28 codebook builder.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-dol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    strings: list[str] = []
    with args.main_dol.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            value = row.get("translation_ko")
            if not isinstance(value, str) or not value:
                raise ValueError(f"missing translation_ko at line {line_number}")
            strings.append(value)

    # Stable first-occurrence ordering makes this input deterministic.  The
    # codebook itself remains append-only because --existing is supplied to
    # arf_euc28_mapping.py.
    unique = list(dict.fromkeys(strings))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(unique) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"input_rows": len(strings), "unique_strings": len(unique),
                      "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
