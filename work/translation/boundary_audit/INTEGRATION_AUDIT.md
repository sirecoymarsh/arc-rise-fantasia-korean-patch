# Boundary Audit Integration Audit

- **Overall:** `PASS_WITH_ADVISORY`
- **Auditor:** Independent Codex internal-model technical audit
- **External translation models/APIs:** not used
- **Canonical audit SHA-256:** `E47BA47E1B2A33940EB08EFFFF1E313FD6ACC4F23D63C5219680D63DBAEE80C7`

## Result summary

- **exact_boundary_linking:** `PASS`
- **reviewed_batch_application:** `PASS`
- **help_295_title_fit:** `PASS`
- **production_tool_execution:** `PASS`
- **apply_tool_idempotence:** `PASS`
- **control_token_exception_scope:** `PASS`

## Verified facts

- 61 unique TM units map exactly to 68 unique structured table fields.
- All scanner occurrence IDs, raw offsets/bytes, field offsets/bytes, source hashes, clean field strings, and capacities matched the underlying catalogs/files.
- Reviewed batch 0001 contains 11 audited units and batch 0002 contains 50; all 61 carry the exact boundary metadata.
- 60 targets differ from their pre-audit approved text; one target was already clean. All 61 current targets encode and fit their audited fields.
- `help:295:title` / `코핀에게 전해진 진실` encodes to 20 payload bytes; with its NUL terminator it occupies exactly the 21-byte field capacity.
- Fresh validator runs completed 200/200 units for each reviewed batch with zero errors.
- Fit preflight matched all 61 audited TM units / 68 table fields with zero fixed overflow and zero encoding errors.
- Apply, validator-report, merge-output, and fit-report reruns were byte-idempotent in disposable fixtures.
- With the canonical audit, a deliberately corrupted control sequence on a non-audited ID was rejected by both validator and merger.

## Non-blocking advisory

- The `--boundary-audit` consumers treat the supplied JSON as a caller-provided trust root; they do not independently pin its schema or SHA-256. The canonical file limits exemptions correctly to 61 IDs, but release orchestration should require the canonical hash shown above so a modified file cannot add exemptions.

## Scope note

- `safe_for_fixed_table_insertion` remains false because 80 other approved system TM units are still unmatched. This does not affect the 61 audited units / 68 linked fields, which are all matched and fixed-field-safe.

## Artifact hashes

- `work/translation/boundary_audit/batches_0001_0002.json`: `E47BA47E1B2A33940EB08EFFFF1E313FD6ACC4F23D63C5219680D63DBAEE80C7`
- `work/translation/boundary_audit/application_report.json`: `2634F894BC741426F7D4185CDD52CAA7370BFD44D1740BBB7F094059FD3A0B99`
- `work/translation/reviewed/batch_0001.jsonl`: `7EBB22A7017CC14D1A133F806CE2197E55A3E2481077B4494171014C7EF135AB`
- `work/translation/reviewed/batch_0002.jsonl`: `422DC33FAAE578EADAF5102CBE34C170423E71E0A45C278F587F77620433BE63`
- `work/font/canonical_v1/codebook.json`: `4BA8DFB2952355C54CC9D6B40F4732A85CFA090CA6B4998DC28BF1F02DDD0AB3`
- `work/research/apply_boundary_audit.py`: `0A2B5027CD24302E9A19DD9960D3783B2E2FCFAB84BFE8F6A621195F722ABDEE`
- `work/research/validate_translation_batch.py`: `F737FB4DE8250A52670D1FE0C0E4BA609B3CEA437A4A659C6A575C3F319F4580`
- `work/research/merge_translation_batches.py`: `31BE0001A2AC005A62CEB6100CA269865391CF03CB554E41077560A0F0DBD2F2`
- `work/research/check_translation_fit.py`: `AF62002DDD574C645B8C228A2B97CE8A5BF280F06832723FFF1A5E6A7DC755B5`
