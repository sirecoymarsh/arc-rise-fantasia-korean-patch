# Arc Rise Fantasia (RPJJ99) BSCR tool

`bscr_tool.py` is a byte-oriented parser, strict validator, and variable-length
string-pool rebuilder for the game's inner `.bscr` files. It performs no
translation and calls no external service.

## Commands

```powershell
python bscr_tool.py verify input.bscr
python bscr_tool.py inspect input.bscr --output inspection.json
python bscr_tool.py rebuild input.bscr output.bscr
python bscr_tool.py rebuild input.bscr output.bscr --replacements replacements.json
```

A rebuild without a replacement manifest exercises the full parser/rebuilder
and must be byte-identical.

Replacement manifest:

```json
{
  "replacements": [
    {
      "offset": "0x2f",
      "raw_hex": "...replacement bytes, without a NUL..."
    }
  ]
}
```

Offsets are original string-pool-relative starts. Raw bytes are intentional:
the future Korean font/code mapping is outside this format layer. Embedded NUL
is rejected. VM call-target strings and structural controls are protected by
default. `--allow-call-targets` and `--allow-control-changes` exist only for
explicit format research.

## Proof suite

```powershell
python run_full_audit.py
```

This recursively discovers the BSCR payloads inside the extracted RPJJ99
RTDP/LZ10 tree, validates all assets, performs a byte-exact no-op rebuild of
every one, and regenerates `full_audit.json` plus representative fixtures.

See `RESEARCH_REPORT.md` for the format specification and measured results.
