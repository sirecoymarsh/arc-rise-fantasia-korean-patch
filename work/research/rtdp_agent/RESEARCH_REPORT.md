# Arc Rise Fantasia (Japan) RTDP `.vol` read-only audit

Date: 2026-08-03 (Asia/Seoul)

Scope: every physical `.vol` below `work/disc_extracted/DATA/files`, plus every
XOR-decoded payload which itself begins with `RTDP`. No original was modified,
and no translation was performed.

## 1. Evidence and implemented tool

Primary source evidence:

`work/tools/DolphinTextureExtraction-tool/lib/AuroraLip/Archives/Formats/RTDP.cs`

Local implementation:

`work/research/rtdp_agent/rtdp_tool.js`

The AuroraLip implementation is read-only (`CanWrite => false`). It establishes
the big-endian header/table fields, offsets relative to EOH, and a bytewise
payload XOR key of `0x55`. The local tool independently implements parsing,
recursive inventory, extraction, fixed-layout repacking, text heuristics, and
strict range/hash checks.

## 2. Confirmed RTDP layout

| Offset | Size | Meaning |
|---:|---:|---|
| `0x00` | 4 | ASCII `RTDP` |
| `0x04` | 4 | big-endian `u32` end-of-header/data base (`EOH`) |
| `0x08` | 4 | big-endian `u32` entry count |
| `0x0C` | 4 | big-endian `u32` archive size |
| `0x10` | 16 | opaque header bytes; preserve exactly |
| `0x20` | `count * 40` | entry records |

Each 40-byte record is:

| Record offset | Size | Meaning |
|---:|---:|---|
| `+0x00` | 32 | fixed raw entry-name field (ASCII in this corpus) |
| `+0x20` | 4 | big-endian decoded payload size |
| `+0x24` | 4 | big-endian payload offset relative to `EOH` |

Every payload byte stored at `EOH + relative_offset` is XOR `0x55`. Entry
names and the RTDP header/table are not XORed.

The unknown header bytes had seven values and were not interpreted:

| `0x10..0x1F` | Archive count |
|---|---:|
| `55280022000000000000000000000000` | 892 |
| `55280021000000000000000000000000` | 144 |
| `55280020000000000000000000000000` | 13 |
| `55280017000000000000000000000000` | 8 |
| `5528001b000000000000000000000000` | 3 |
| `5528001e000000000000000000000000` | 3 |
| `55280018000000000000000000000000` | 1 |

Do not synthesize or normalize this field until its consumer is understood.

## 3. Corpus-wide structural result

Authoritative machine-readable summary:

`work/research/rtdp_agent/audit/summary.json`

Results:

- 758 physical `.vol` files.
- 1,064 RTDP archives including 306 nested RTDP payloads.
- 34,006 records in original order: 8,425 non-empty and 25,581 zero-size.
- 0 parse failures, 0 size-field mismatches, 0 out-of-range entries, 0
  overlap cases, and 0 non-monotonic non-empty offset sequences.
- All 8,425 non-empty relative offsets are aligned to `0x20`.
- All entry-name bytes are ASCII. 2,732 name fields occupy all 32 bytes without
  a NUL terminator; treat those as valid fixed-width fields, not malformed
  strings. Preserve the raw 32 bytes.
- 443 archives have duplicate decoded names. Most involve `reserved_file`, but
  genuine duplicate/truncated names also exist. Identity must be
  `archive-chain + record index`, never name alone.
- 8,109 non-empty payloads have a known magic only after XOR `0x55`; zero have a
  known magic while still stored. In particular, 306 nested payloads change
  from stored prefix `07 01 11 05` to decoded `52 54 44 50` (`RTDP`).
- Every observed header/data gap and trailing alignment byte is zero, but the
  repacker still preserves the exact opaque bytes rather than assuming zero.

### Packing rule and one exception

1,063/1,064 parsed archives follow this rule exactly:

1. `EOH = align_up(0x20 + count * 40, 0x20)`.
2. First non-empty relative offset is zero.
3. Each following payload starts at `align_up(previous_end, 0x20)`.
4. Archive size is the final decoded payload end aligned to `0x20`.

The sole exception is `work/disc_extracted/DATA/files/Btl/btl_gameover.vol`:

- table end `0x200`, but `EOH = 0x800` (extra `0x600` zero bytes);
- custom larger inter-entry slots rather than minimum `0x20` padding;
- extra zero tail;
- duplicate `e.wtm` name.

This exception is why a production writer must preserve a template or encode
an explicit per-archive layout policy instead of globally compacting data.

## 4. Complete inventories

- Archive/order/layout inventory: `work/research/rtdp_agent/audit/archives.csv`
  and `archives.json`.
- Entry name/index/offset/size/magic/XOR/hash inventory:
  `work/research/rtdp_agent/audit/entries.csv` and `entries.json`.
- Raw encoding heuristic output: `work/research/rtdp_agent/audit/text_candidates.csv`
  and `text_candidates.json`.
- Vetted localization-bearing payload inventory:
  `work/research/rtdp_agent/audit/localization_payloads.csv` and
  `localization_payloads.json`.
- BSCR-only inventory: `work/research/rtdp_agent/audit/script_payloads.csv` and
  `script_payloads.json`.
- Parser errors: `work/research/rtdp_agent/audit/errors.json` (empty array).

`entries.csv` includes, for every record, physical archive, recursive archive
identity, record index/order, raw 32-byte name, size, relative and absolute
container offsets, gap, alignment, stored/decoded prefixes and magic labels,
and SHA-256 of both stored and decoded payloads.

## 5. Text/script findings

### Encoding: EUC-JP, not Shift-JIS/CP932

The principal text encoding is EUC-JP. Strong evidence:

- `Sys/system.vol` contains nine font texture entries named `EUC28-0.wtm`
  through `EUC28-8.wtm`.
- In decoded `Event/fc/fc_00_001.vol::0000:fc_00_001.bscr`, payload offset
  `0x12F` (303) contains:

  `a4aaa4a4a1a2cbdcc5f6a4cba4b3a4eca4c7b2e1a4b4a4b9a4cea4aba1a9`

  Strict EUC-JP decoding gives `おい、本当にこれで過ごすのか？`; Shift-JIS
  decoding gives half-width/mojibake. The following NUL-terminated lines decode
  consistently as natural Japanese under EUC-JP.
- The system tables listed below also decode consistently as EUC-JP, including
  `何も無し`, `ヒールリキッド`, `疲れ切っているリフィアを休ませるため`,
  and `おまかせ`.

The raw heuristic produced two low-confidence, two-character Shift-JIS hits in
`map_info.dat` and `weapon_data.bin`; both are binary coincidences with no
supporting string corpus and are excluded from the vetted inventory.

EUC-JP cannot directly encode Hangul. A Korean patch therefore needs an
explicit game-font/code-point strategy (for example, a proven custom glyph
mapping), not a blind EUC-JP string replacement.

### BSCR scripts

There are 380 decoded `BSCR` payloads:

| Directory | Payloads | With detected Japanese | Heuristic string runs |
|---|---:|---:|---:|
| `Event/exp` | 6 | 6 | 134 |
| `Event/fc` | 310 | 307 | 4,089 |
| `Event/wld` | 64 | 64 | 746 |
| **Total** | **380** | **377** | **4,969** |

The three small command-only/no-Japanese scripts are:

- `Event/fc/fc_08_011.vol::0000:fc_08_011.bscr` (128 bytes)
- `Event/fc/fc_09_028.vol::0000:fc_09_028.bscr` (288 bytes)
- `Event/fc/fc_09_041.vol::0000:fc_09_041.bscr` (288 bytes)

The 4,969 figure is a discovery heuristic, not yet a stable translation-unit
count. BSCR commands, speaker metadata, pointers/lengths, control codes, and
re-encoding rules still need a dedicated format pass before translation.

### Vetted non-BSCR localization payloads

Twelve table payloads contain substantial NUL-terminated EUC-JP text:

- `minigame/mg_copin.vol::0000:copin.dat`
- `Sys/system.vol::0030:item.bin`
- `Sys/system.vol::0031:shop.bin`
- `Sys/system.vol::0032:dragon.bin`
- `Sys/system.vol::0033:treasure.bin`
- `Sys/system.vol::0034:magic.bin`
- `Sys/system.vol::0035:special.bin`
- `Sys/system.vol::0036:operation.bin`
- `Sys/system.vol::0037:quest.bin`
- `Sys/system.vol::0038:ability.bin`
- `Sys/system.vol::0041:chat.bin`
- `Sys/system.vol::0050:todo.dat`

Thirteen nested `btl_stat_party*.bin` payloads in
`Btl/btl_usual.vol::0000:btl_status.vol` contain EUC-JP party display names.
`Btl/btl_usual.vol::0025:fld000.bin` contains at least `レイストーン` and
`<名称未設定>` among a mixed binary resource. These 14 embedded-label payloads
need their owning BTEM/resource structure mapped before editing.

The vetted inventory therefore contains 406 payloads: 380 BSCR, 12 tables, 13
battle-party label resources, and one mixed field resource.

The separate raw heuristic file intentionally contains lower-confidence
binary coincidences. Use `localization_payloads.*`, not `text_candidates.*`, as
the next-stage worklist.

## 6. Extraction/re-encode/repack proof

Durable proof:

`work/research/rtdp_agent/roundtrip_proof.json`

Reproduction script:

`work/research/rtdp_agent/prove_roundtrips.js`

Four independently rebuilt fixtures are byte-identical to their sources:

| Fixture | Size | SHA-256 |
|---|---:|---|
| `Event/fc/fc_00_001.vol` | 4,128 | `013da5122f3cb0354840c59dd8b1ee58f37291972ba9692c70c0e6965287ecdd` |
| exceptional `Btl/btl_gameover.vol` | 241,664 | `5e1bd2605b55815364d43e586f22310cea797ff1c1d48dcd7408915f01817f17` |
| `Sys/system.vol` | 6,172,640 | `1a7c20a70c3e62d6640048d20f0200232a73fc9ea17bba9f62b8bf6d06f9471d` |
| nested `system.vol::0049:enm_symbole.efp` | 56,000 | `d9d126c095df82c41a302c888da3c112087df57d1a24f5531c9698510fc19cde` |

A controlled same-size edit to extracted `fc_00_001.bscr` also round-tripped:

- decoded payload byte at offset 31 changed `00 -> 01`;
- exactly one archive byte changed, at archive offset `0x7F`, `55 -> 54`;
- both stored bytes equal decoded byte XOR `0x55`;
- re-extraction recovered the edited payload byte-for-byte.

The safety guard was also proved: changing that payload from 4,028 to 4,029
bytes exits with failure and produces no output archive.

## 7. Current writer boundary

`rtdp_tool.js repack` is intentionally fixed-layout:

- preserves header/table bytes, record order, names, duplicates, offsets,
  exceptional gaps, tails, and opaque bytes exactly;
- XOR-encodes decoded payloads with `0x55`;
- rejects all payload-size changes.

This is sufficient for byte-exact no-op and same-size edit proofs. It is not a
release writer for length-changing Korean strings. Before enabling resize, add:

1. BSCR/table-level pointer, length, and control-code rebuilders.
2. A variable-layout RTDP mode for standard archives, plus an explicit
   template-preserving policy for `btl_gameover.vol` and any future exception.
3. Recursive bottom-up rebuild: inner RTDP/BSCR/table first, then every parent
   archive whose child size changes.
4. Entry-index/hash allowlists and complete recursive semantic comparison.
5. Korean font/code mapping validation for the `EUC28-*` font lane.

## 8. Recommended next research order

1. Reverse-engineer BSCR string records, command boundaries, pointer/length
   fields, speakers, choices, and control codes using the 380-script inventory.
2. Map record schemas for the 12 system/minigame tables, starting with
   `item.bin`, `todo.dat`, `operation.bin`, and `copin.dat`.
3. Reverse-engineer `EUC28-*.wtm` glyph indexing and the runtime decoder to
   establish a Hangul-capable mapping before translating text.
4. Implement bottom-up variable-size rebuilds and prove them on copied fixtures
   with entry-order/hash comparisons.
5. Only then create stable contextual IDs and begin Codex-internal translation.
