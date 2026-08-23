# Arc Rise Fantasia Korean ROM Patcher

This directory contains the source and reproducible validation tools for the v1.1.2 Windows one-click ROM patcher.

## User contract

- Input: unmodified Japanese `RPJJ99` revision 0 RVZ or ISO.
- Output: a separate Korean RVZ or ISO; the input is never modified.
- The output keeps game/title ID `RPJJ99`, so existing Japanese-version saves remain compatible.
- The release contains VCDIFF deltas only. It contains no complete source or patched game image.

## Source layout

- `src/PatcherCore.cs`: hash-bound extract, delta apply, image rebuild, output verification, cleanup, and result report.
- `src/Program.cs`: Korean WinForms interface.
- `src/TestHarness.cs`: command-line E2E harness used for automated validation.
- `build_delta_payload.py`: builds and round-trip verifies all 722 deltas from trusted source and final staging.
- `build_rom_patcher_release.py`: compiles the GUI and builds the explicit-allowlist release tree and ZIP.
- `verify_e2e_output.py`: independently extracts a generated image and verifies all 722 output hashes.
- `validate_rom_patcher_release.py`: independently tests ZIP CRC, safe paths, extracted hashes, forbidden image extensions, and local-path leakage.

## Bundled runtime tools

The release includes the minimum files required from:

- DolphinTool 2603a
- xdelta3 3.2.0
- Wiimms ISO Tools 3.05a r8638

Their license texts and notices are included in the release. Tool binaries and generated payloads are deliberately ignored by Git; the public metadata is stored in `release_metadata/rom_patcher_v1.1.2/`.

## Build

After recreating the pinned payload and tool inputs in `work/rom_patcher/build` and `work/tools`:

```powershell
python work/rom_patcher/build_rom_patcher_release.py
```

Independent release validation:

```powershell
python work/rom_patcher/validate_rom_patcher_release.py `
  work/rom_patcher/dist/ArcRiseFantasia-Korean-ROM-Patcher-v1.1.2.zip `
  work/rom_patcher/e2e/release_extract `
  work/rom_patcher/e2e/release_validation_report.json
```

## Frozen v1.1.2 results

- Delta entries: 722/722 round-trip verified.
- Original RVZ → Korean RVZ: 722/722 decoded output hashes matched.
- Standalone Korean RVZ boot: remained responsive for the 60-second smoke run.
- ZIP extraction: 738/738 files present; no CRC, hash, size, path, or forbidden-image issue.
- Ray Stone and unset-name field-object targets: byte-level and final-image hash proof passed.
- Full battle-text duplicate audit: zero residual Japanese across the enumerated BTEM, monster, special-skill, tutorial, runtime, and raster scopes.
- Cage shop raster labels and `main.dol` strings: static/package proof passed; manual screen recheck remains.
- Semantic translation provenance: `translator_model: Codex internal`.
