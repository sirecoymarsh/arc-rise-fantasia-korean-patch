# Arc Rise Fantasia outer-container rebuilder

This directory contains a conservative, dependency-free rebuilder for the
outer formats used by **Arc Rise Fantasia (Japan), RPJJ99**.  It does not
translate text and does not call any external API or model.

## Files

- `container_tool.js` — library plus command-line interface.
- `verify_container_tool.js` — corpus-wide no-op and controlled-resize suite.
- `verification.json` — machine-readable test evidence.
- `reproduction.json` — exact reproduction command and immutable input scope.
- `RESEARCH_REPORT.md` — format, policy, and verification conclusions.

All source files under `work/disc_extracted/DATA/files` are opened read-only.
The verifier writes only its two JSON reports in this directory.

## RTDP policy

`container_tool.js` preserves:

- entry order and index identity;
- each raw 32-byte entry-name field (including duplicates and fields without a
  NUL terminator);
- the 16 opaque bytes at `0x10..0x1f`;
- EOH and bytes between the table and EOH;
- payload XOR key `0x55`;
- `0x20` data alignment for canonical archives.

The writer selects one of four explicit policies:

1. `exact-noop`: unchanged decoded payloads return the original bytes exactly.
2. `fixed-layout`: same-size changes overwrite only the existing XOR payload.
3. `standard-resize`: the canonical layout is rebuilt with `0x20` alignment,
   table sizes/offsets and archive size updated.
4. `gameover-template`: the recognized special `Btl/btl_gameover.vol` keeps
   EOH `0x800`, all original slot offsets, total size, raw names, and opaque
   header. A payload may resize only inside its existing slot.

Any size change in an unknown nonstandard RTDP is rejected with
`UNSUPPORTED_NONSTANDARD_RESIZE`. A special game-over payload larger than its
slot is rejected with `GAMEOVER_SLOT_OVERFLOW`. No global “compact whatever was
found” fallback exists.

## LZ10 policy

The deterministic Nintendo LZ10 compressor uses:

- 24-bit unpacked size header;
- a `0x1000`-byte window;
- match lengths `3..18`;
- greedy longest match;
- nearest-distance tie break;
- zero padding to 4-byte output alignment by default.

Every newly compressed stream is immediately decompressed and compared with
the requested unpacked bytes. `rebuildLz10` returns the exact original packed
stream when the unpacked data is unchanged.

`rebuildCxdPayload` safely rewraps an arbitrary decompressed payload such as
WTMD and requires its expected original SHA-256. `rebuildCxd` handles the
common LZ10 -> RTDP tree case.

## Bottom-up safe API

Load the module from Node.js:

```js
const fs = require('fs');
const c = require('./container_tool.js');

const source = fs.readFileSync('some.cxd');
const oldLeaf = /* decoded leaf obtained from the indexed RTDP path */;
const newLeaf = /* output of the validated payload-level rebuilder */;

const result = c.rebuildCxd(source, [{
  entryPath: [0, 3],             // indexes, never names
  expectedSha256: c.sha256(oldLeaf),
  data: newLeaf,
}], { sourceLabel: 'some.cxd' });

fs.writeFileSync('some.rebuilt.cxd', result.buffer);
fs.writeFileSync('some.rebuilt.report.json',
  JSON.stringify(result.report, null, 2) + '\n');
```

For `[0, 3]`, entry `3` of the RTDP stored in root entry `0` is rebuilt first;
that new child is then inserted into entry `0`; each changed parent RTDP is
rebuilt in turn; finally the `.cxd` LZ10 layer is regenerated. The report's
`containerAuditBottomUp` is in that same child-to-parent order.

Every leaf edit requires the SHA-256 of the exact decoded source payload. This
prevents applying an index path to a different game build or stale extraction.
Duplicate names are therefore harmless.

### CLI edit manifest

```json
{
  "format": "arf-container-edits-v1",
  "edits": [
    {
      "entryPath": [0, 3],
      "expectedSha256": "64 lowercase hexadecimal characters",
      "replacementFile": "payloads/rebuilt-leaf.bin"
    }
  ]
}
```

Paths in `replacementFile` are relative to the manifest. Run:

```powershell
node work/research/container_agent/container_tool.js rebuild `
  source.cxd edits.json rebuilt.cxd rebuilt.report.json
```

For a `.cxd` whose decompressed content is not RTDP (for example WTMD):

```powershell
node work/research/container_agent/container_tool.js rewrap-cxd `
  source.cxd rebuilt.wtm EXPECTED_UNPACKED_SHA256 rebuilt.cxd report.json
```

## Verification

From the workspace root:

```powershell
node work/research/container_agent/verify_container_tool.js
```

The suite covers all 758 physical `.vol` archives and all 306 recursively
nested RTDP archives, controlled fixed-size and variable-size writes, the
special game-over template and both rejection boundaries, three representative
LZ10 `.cxd` files, an arbitrary WTMD whole-payload rewrap, LZ10 -> RTDP rebuild,
and a two-level nested RTDP rebuild.

## Boundary with payload rebuilders

This tool intentionally knows nothing about BSCR, SSCR, fixed-record tables,
WTMD texture semantics, BTEM, or other payload-internal pointers and lengths.
Those formats must first be rebuilt and validated by their dedicated tools.
Only then should their resulting bytes be passed here. Outer-container success
does not certify payload semantics.

