# RVZ tooling audit (read-only)

## Source image

- Path: `F:\DOWN\Arc Rise Fantasia (Japan)\Arc Rise Fantasia (Japan).rvz`
- Size: `3,589,772,720` bytes
- SHA-256: `4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5`
- LastWriteTime: `1996-12-24 23:32:00` (local display)

Hash command:

```powershell
Get-FileHash -LiteralPath 'F:\DOWN\Arc Rise Fantasia (Japan)\Arc Rise Fantasia (Japan).rvz' -Algorithm SHA256
```

## Working RVZ tool

- Official Dolphin 2603a workspace copy:
  `C:\Users\CadriacLord\Documents\Codex\2026-08-03\f-down-arc-rise-fantasia-japan\work\tools\dolphin-2603a\Dolphin-x64\DolphinTool.exe`
- `DolphinTool.exe` SHA-256:
  `46E2ABDC7AB327AAB12638B34176CE3068F514F68ED92DAAE59CCB3079756F57`
- Supported commands reported by the binary: `convert`, `verify`, `header`, `extract`.
- `extract -h` supports `--list`, `--partition`, and `--single`, so complete or selective file listing needs no extraction.

Header command:

```powershell
& 'C:\Users\CadriacLord\Documents\Codex\2026-08-03\f-down-arc-rise-fantasia-japan\work\tools\dolphin-2603a\Dolphin-x64\DolphinTool.exe' `
  header -i 'F:\DOWN\Arc Rise Fantasia (Japan)\Arc Rise Fantasia (Japan).rvz' -j
```

Header JSON:

```json
{"block_size":131072,"compression_level":19,"compression_method":"Zstandard","country":"Japan","game_id":"RPJJ99","internal_name":"ARC RISE FANTASIA","region":"NTSC-J","revision":0,"title_id":281476357704266}
```

Complete read-only listing command:

```powershell
& 'C:\Users\CadriacLord\Documents\Codex\2026-08-03\f-down-arc-rise-fantasia-japan\work\tools\dolphin-2603a\Dolphin-x64\DolphinTool.exe' `
  extract -i 'F:\DOWN\Arc Rise Fantasia (Japan)\Arc Rise Fantasia (Japan).rvz' -l
```

Selective listing example (confirmed exit code 0):

```powershell
& 'C:\Users\CadriacLord\Documents\Codex\2026-08-03\f-down-arc-rise-fantasia-japan\work\tools\dolphin-2603a\Dolphin-x64\DolphinTool.exe' `
  extract -i 'F:\DOWN\Arc Rise Fantasia (Japan)\Arc Rise Fantasia (Japan).rvz' `
  -p DATA -s 'Sys/help.bin' -l
```

## Partitions and entries

The full listing exposes exactly two partitions:

| Partition | Files | Directories | Total entries |
|---|---:|---:|---:|
| UPDATE | 31 | 1 | 32 |
| DATA | 14,526 | 840 | 15,366 |

The `UPDATE` partition contains `_sys/`, 29 WAD payloads under it, and the two root files `__update.inf` and `__update.inf.TWN` (31 files total).

DATA top-level counts (each count includes files and directory entries):

| Top-level | Files | Directories | Entries |
|---|---:|---:|---:|
| Event | 12,607 | 811 | 13,418 |
| interface | 758 | 1 | 759 |
| world | 551 | 10 | 561 |
| Map | 336 | 4 | 340 |
| Char | 151 | 1 | 152 |
| minigame | 36 | 3 | 39 |
| Btl | 25 | 2 | 27 |
| Movie | 23 | 1 | 24 |
| _sasaki | 13 | 2 | 15 |
| Hbm | 13 | 1 | 14 |
| Sys | 8 | 1 | 9 |
| Title | 2 | 2 | 4 |
| _viewer | 2 | 1 | 3 |
| opening.bnr | 1 | 0 | 1 |

DATA file extensions: `.adx` 12,133; `.cxd` 990; `.vol` 758; `.bin` 549; `.wtm` 45; `.sfd` 21; `.arc` 9; `.vld` 7; `.bat` 3; `.tpl` 2; `.csv` 2; `.txt` 2; `.swd`, `.go`, `.afs`, `.bnr`, `.sed` 1 each.

Likely localization-relevant names visible at disc level include `Btl/btl_tutorial.vld`, `interface/msgfrm.vol`, `Sys/help.bin`, `Sys/system.vol`, `Sys/title.vol`, `Title/title.vol`, `Hbm/home.csv`, `Hbm/home_nosave.csv`, many `interface/tex_loc_title_*_wtm.cxd` assets, 758 `.vol` containers, and 549 `.bin` files. This is only filename evidence; container internals were not extracted in this audit.

Full captured listing: `full_file_list.txt` (15,400 lines including the two partition marker lines).

## Verify result and caveat

Command (temporary/user data confined to the audit work folder):

```powershell
& 'C:\Users\CadriacLord\Documents\Codex\2026-08-03\f-down-arc-rise-fantasia-japan\work\tools\dolphin-2603a\Dolphin-x64\DolphinTool.exe' `
  verify -i 'F:\DOWN\Arc Rise Fantasia (Japan)\Arc Rise Fantasia (Japan).rvz' `
  -u 'C:\Users\CadriacLord\Documents\Codex\2026-08-03\f-down-arc-rise-fantasia-japan\work\rvz_tooling_audit\dolphin_user'
```

Exact output:

```text
Error creating key
CRC32: f92834dc
MD5 not computed
SHA1: 383599d38df8105da21a32d7a18fb4a30514878e
Problems Found: No
```

The process returned exit code 0. Keep the `Error creating key`/`MD5 not computed` messages as explicit limitations; do not overstate the result as a complete cryptographic verification of every encrypted component.

## Other environment findings

- No global/PATH command or registered install was found for `DolphinTool`, `Dolphin`, `wit`, `wwt`, `7z`, `7zz`, `7za`, WinRAR, or Everything.
- No installed 7-Zip/NanaZip/PeaZip directory was found in the standard Program Files/AppData locations, so no RVZ-capable 7-Zip plugin was available.
- `P:\DOWNLOAD\7z1900-x64.exe` is only an installer; it was not run.
- `P:\DOWNLOAD\에뮬 앱\dolphin-2512.apk` is an Android APK, not a usable Windows CLI for this workflow.
- Windows `C:\Windows\System32\tar.exe` exists but rejects the RVZ with `Error opening archive: Unrecognized archive format` and exit code 1.

No source files were extracted, converted, renamed, or modified. Only listing/header/hash/verify reads were performed; the only new files are under `work\rvz_tooling_audit`.
