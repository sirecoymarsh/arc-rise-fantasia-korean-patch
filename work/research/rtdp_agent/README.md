# Arc Rise Fantasia RTDP research tool

This directory is a read-only research lane for the RTDP `.vol` archives in
`work/disc_extracted/DATA/files`.  It does not edit or replace any game file.

The parser is derived from the repository evidence at:

`work/tools/DolphinTextureExtraction-tool/lib/AuroraLip/Archives/Formats/RTDP.cs`

## Commands

```powershell
node work/research/rtdp_agent/rtdp_tool.js audit `
  work/disc_extracted/DATA/files `
  work/research/rtdp_agent/audit

node work/research/rtdp_agent/rtdp_tool.js inspect `
  work/disc_extracted/DATA/files/Event/fc/fc_00_001.vol

node work/research/rtdp_agent/rtdp_tool.js extract `
  work/disc_extracted/DATA/files/Event/fc/fc_00_001.vol `
  work/research/rtdp_agent/fixtures/fc_00_001

node work/research/rtdp_agent/rtdp_tool.js repack `
  work/research/rtdp_agent/fixtures/fc_00_001 `
  work/research/rtdp_agent/fixtures/fc_00_001.repacked.vol
```

## Safety boundary

`extract` decodes each payload with bytewise XOR `0x55` and writes an indexed
payload tree plus a manifest. `repack` reconstructs a new archive from that
tree. It preserves the original header, table, offsets, gaps, order, duplicate
names, and all other opaque bytes. It **rejects any payload size change**. This
is suitable for byte-exact no-op round-trip proof and same-size experiments,
not yet for a release archive containing length-changing translations.

