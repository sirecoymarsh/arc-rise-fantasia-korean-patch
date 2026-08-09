# RPJJ99 outer-container variable-size rebuild report

Date: 2026-08-03 (Asia/Seoul)

Scope: RTDP `.vol`, nested RTDP, and Nintendo LZ10 `.cxd` wrapping only. No
translation was performed, and no external translation API/model was used.
Original and extracted game inputs remained read-only.

## 1. Evidence used

- `work/research/rtdp_agent/RESEARCH_REPORT.md`
- `work/research/rtdp_agent/rtdp_tool.js`
- `work/research/rtdp_agent/audit/archives.json`
- `work/research/rtdp_agent/audit/entries.json`
- `work/research/arf_lz10.py`
- payload-level research in `work/research/bscr_agent/` and
  `work/research/table_agent/` (used only to define the outer/payload boundary)

Implementation:

- `work/research/container_agent/container_tool.js`

Reproduction and proof:

- `work/research/container_agent/verify_container_tool.js`
- `work/research/container_agent/verification.json`
- `work/research/container_agent/reproduction.json`

## 2. Standard RTDP variable-size writer

The implemented parser/writer retains the established RTDP structure:

| Offset | Size | Handling |
|---:|---:|---|
| `0x00` | 4 | require `RTDP` |
| `0x04` | 4 | preserve EOH |
| `0x08` | 4 | preserve entry count |
| `0x0c` | 4 | update to rebuilt archive size |
| `0x10` | 16 | preserve opaque bytes exactly |
| `0x20` | `count * 40` | preserve order and raw names; update sizes/offsets |
| `EOH+offset` | variable | XOR every decoded payload byte with `0x55` |

For canonical archives, non-empty payloads are emitted in original entry order.
The first begins at relative offset zero and later payloads begin at
`align_up(previous_end, 0x20)`. The output tail is aligned to `0x20`. Empty
entries remain empty with relative offset zero, matching every empty record in
the audited corpus. The header-to-EOH region is copied from the template rather
than synthesized.

Before a resize is allowed, the source must have a matching size field, no
overlap, canonical EOH, canonical links, canonical final size, and no nonzero
opaque data in regions that compaction would overwrite. After writing, the
archive is reparsed and checked for count, EOH, opaque header, header padding,
raw names, sizes, payload bytes, and canonical alignment.

An unchanged payload set returns a copy of the exact original archive. This is
intentional: it preserves all unknown bytes rather than normalizing them.

## 3. `Btl/btl_gameover.vol` special policy

This is the only nonstandard archive in the 1,064-archive RTDP corpus. It is
recognized structurally, not merely by a filename:

- EOH `0x800`;
- 12 entries and file size `0x3b000`;
- opaque header `55280021000000000000000000000000`;
- exact ordered raw-name/offset geometry, including duplicate `e.wtm`;
- non-overlapping non-empty entries.

The `gameover-template` writer never compacts or moves its entries. It preserves
the fixed slots whose starts are:

`0x00000, 0x02800, 0x05000, 0x07800, 0x0a000, 0x0c800, 0x0f000,
0x11800, 0x14000, 0x23000, 0x32000, 0x36000` relative to EOH.

It verifies that observed slack is zero, clears only the selected slot, writes
the XOR payload at the original slot start, and changes only that entry's size.
Growth beyond a slot is rejected as `GAMEOVER_SLOT_OVERFLOW`. Any variable-size
write to any other noncanonical archive is rejected as
`UNSUPPORTED_NONSTANDARD_RESIZE`. Same-size writes remain safe through the
general fixed-layout path.

## 4. Deterministic LZ10 writer

The compressor implements standard Nintendo type `0x10` streams with a 24-bit
little-endian unpacked size, 4,096-byte lookbehind, and 3-to-18-byte matches.
It uses deterministic greedy longest-match selection and a nearest-distance
tie break. New streams are zero-padded to four bytes, matching all sampled
`.cxd` files. Every output is decompressed immediately and required to equal the
input buffer.

If unpacked bytes have not changed, `rebuildLz10` returns the exact packed
template, avoiding needless recompression drift. A changed wrapper refuses to
discard any nonzero bytes after the consumed original stream.

The API has two lanes:

- `rebuildCxdPayload`: expected-hash-bound whole decompressed payload replacement
  for WTMD or another non-RTDP inner format;
- `rebuildCxd`: expected-hash-bound RTDP entry-path edits followed by RTDP rebuild
  and deterministic LZ10 wrapping.

## 5. Bottom-up nested API

Edits are addressed by integer entry-index paths, never names. For example,
`[49, 0]` means root entry 49, then child RTDP entry 0. Each edit must include
the SHA-256 of the original decoded leaf. A mismatch stops before writing.

Recursive children are rebuilt before parents. Every parent size/offset table
is recalculated under its own explicit layout policy. The returned audit trail
records leaf old/new sizes and hashes plus every container policy and hash in
bottom-up order.

## 6. Verification results

`verification.json` reports `PASS` for all checks. Principal results:

- 758 physical `.vol` files tested.
- 306 nested RTDP archives tested.
- 1,064 / 1,064 unchanged RTDP rebuild calls were byte-exact.
- 34,006 RTDP entries covered.
- 1,063 canonical archives and one recognized game-over template; zero other
  nonstandard archives in this corpus.
- Same-size XOR edit re-extracted exactly and changed one stored archive byte.
- Canonical controlled growth reparsed successfully with raw names, opaque
  header, entry hashes, and `0x20` offsets verified.
- Game-over in-slot growth retained all slot offsets and every unrelated entry
  hash; one-byte overflow was explicitly rejected.
- An independently constructed valid but unknown nonstandard RTDP remained
  byte-exact for no-op and was explicitly rejected for resizing.
- Three LZ10 fixtures (WTMD and RTDP inners, up to 2,892,512 unpacked bytes)
  compressed deterministically on repeated runs and decompressed byte-equal.
- Unchanged `.cxd` wrappers were byte-exact.
- A WTMD whole-payload size change was rewrapped and decompressed byte-equal,
  with a stale source hash explicitly rejected.
- `interface/data_map_aka_vol.cxd` proved LZ10 -> resized RTDP -> LZ10.
- `Sys/system.vol::0049:enm_symbole.efp::0000:enm_symbole.bin` proved a
  two-layer nested RTDP resize; child and parent selected `standard-resize`, and
  re-extracted leaf SHA-256 equaled the requested replacement.

The authoritative offsets and SHA-256 values are in `verification.json` rather
than duplicated here.

Final integrity values (also recorded and machine-checked by
`reproduction.json`):

- `container_tool.js`: `6b7d755a2efe70170ec109b87a3f64fe9df5822e00fa80a57dafb9dc625a7374`
- `verify_container_tool.js`: `6682d911264cb28514f1294db5f52ae51c1eced87b2a3e90b99622164a0b2cd6`
- `verification.json`: `8722f16606e4bafedc65f9021e1fbe409efb7ebdd0774851756de32dd7f44aff`

## 7. Explicit boundary

This work proves the outer container transforms. It does not make an arbitrary
payload resize safe. BSCR/table/WTMD/etc. writers remain responsible for their
own pointers, field lengths, control codes, texture sizes, and semantic
validation before handing bytes to this layer.
