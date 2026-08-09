# Canonical System Boundary Integration Audit

- **Overall:** `PASS_WITH_STATE_NOTE`
- **Checks:** 11 total / 10 PASS / 1 WARN / 0 FAIL
- **Auditor:** Independent Codex internal-model technical audit
- **External translation models/APIs:** not used
- **Requested 1,000-unit snapshot canonical SHA-256:** `C25EA40505BED4F414AB61D921D94676047851431C825C16022CB32C6AE59360`
- **Live canonical SHA-256 at completion:** `131DBA7684CA37C974FA0AF30654A71F53886A129B7258E978DF2C24BEB71920`

## Check results

- **canonical_hash_and_component_pins:** `PASS`
- **canonical_composition:** `PASS`
- **exact_offset_raw_and_clean_source_linking:** `PASS`
- **reviewed_clean_target_and_capacity_application:** `PASS`
- **component_application_reports:** `PASS`
- **current_translation_memory:** `WARN`
- **five_validators_merge_and_fit:** `PASS`
- **canonical_builder_idempotence_and_pin_rejection:** `PASS`
- **component_application_idempotence_and_pin_rejection:** `PASS`
- **control_token_exception_scope:** `PASS`
- **review_sidecar_provenance_metadata:** `PASS`

## Verified facts

- Three hash-pinned components compose byte-for-byte into the requested 1,000-unit canonical snapshot.
- 169 unique TM units map to 176 unique structured table fields; there are no duplicates, omissions, ambiguous units, or unmatched audited units.
- All occurrence IDs, offsets, raw byte slices, source-file hashes, clean source strings, clean targets, and field capacities were independently checked.
- Reviewed batches 0001-0005 contain 1,000 approved units; all 169 audited targets and metadata are applied exactly.
- Fresh validators completed all five 200-unit batches with zero errors and zero warnings.
- Fresh fit preflight reports matched_unique=1000, unmatched=0, fixed overflow=0, global encoding errors=0, and safe_for_fixed_table_insertion=true.
- Canonical builder, three component applications, validator reports, merge outputs, and fit report are byte-idempotent in disposable fixtures.
- Modified component audits are rejected by their SHA pins, and a non-audited control-token mismatch is rejected by validator and merger.
- `help:295:title` (`코핀에게 전해진 진실`) is 20 payload bytes and exactly 21/21 bytes including NUL.

## State note

- The shared live state advanced to batch 0006 while this audit was running. The requested 1,000-unit/batches-0001-to-0005 snapshot was therefore rebuilt from its pinned reviewed inputs and historical append-only codebook, and its TM/CSV/coverage/fit hashes were reproduced exactly. The later live state is reported separately and is not treated as a defect in the requested snapshot.

## Artifact hashes

- `work/translation/boundary_audit/canonical_system_boundary_audit.json`: `131DBA7684CA37C974FA0AF30654A71F53886A129B7258E978DF2C24BEB71920`
- `work/translation/boundary_audit/batches_0001_0002.json`: `E47BA47E1B2A33940EB08EFFFF1E313FD6ACC4F23D63C5219680D63DBAEE80C7`
- `work/translation/boundary_audit/batches_0003_0004.json`: `8500248960597E9A7A656F14FD07010A923C0B60544B1D1478E8B497900BDB5C`
- `work/translation/boundary_audit/batch_0005.json`: `4776B6BB8042A707C9A2E3ADDEE08520396BF52B54E88ED0D72989936BA7339E`
- `work/translation/boundary_audit/application_report.json`: `2634F894BC741426F7D4185CDD52CAA7370BFD44D1740BBB7F094059FD3A0B99`
- `work/translation/boundary_audit/application_report_0003_0004.json`: `4A9B6AA5E1CB9977DBE8E9693554EF4A25426CAC8956C616B2D7A3953BC1A2C9`
- `work/translation/boundary_audit/application_report_0005.json`: `A2EBF8E8845112298AA69C454869DBB54CC3CADB27702DF16CF1228B63865DFD`
- `work/translation/reviewed/batch_0001.jsonl`: `7EBB22A7017CC14D1A133F806CE2197E55A3E2481077B4494171014C7EF135AB`
- `work/translation/reviewed/batch_0002.jsonl`: `422DC33FAAE578EADAF5102CBE34C170423E71E0A45C278F587F77620433BE63`
- `work/translation/reviewed/batch_0003.jsonl`: `3121E26E086B697C9F97BCC75ED3683B994CB86A4ABAEFA6F97AAFD9A2581302`
- `work/translation/reviewed/batch_0004.jsonl`: `2B0ACF14211E87DC7348AFF253FB5A719692373764DB82E3AA2411F90BC8CC1B`
- `work/translation/reviewed/batch_0005.jsonl`: `FDD35157505093D8F849759253A63C03CC1FA7F0E6740310A5CD0F04DEBE30F0`
- `work/translation/current/translation_memory_draft.json`: `EA80A6C38B6FDEE64997F6BE9D9E2314F1198032AFE44D299BDDC0D1EDC3CC3F`
- `work/translation/current/coverage.json`: `5C4CA079FF4A5A10F6B775197EF9076A6F3E036F4D4BBDAECE0C0F217AABAD66`
- `work/font/canonical_v1/codebook.json`: `C2B3EFD964B88FB58B166AEE72EC655DCBBE0E6245A7B69AFFA22F96EF55851A`
- `work/font/canonical_v1/codebook_before_batch_0006.json`: `284CA42BE7F27AB8861593B1D9B72399903DCC006876C405A58624973818A313`
- `work/font/canonical_v1/fit_preflight.json`: `1A94C05F2C3411CE1E93053DC5803831B0A09093538A7124F3CF45BF8DCCBB11`
- `work/research/apply_boundary_audit.py`: `FF8D2C7B374D34C70AEE13B8EB155C852CD625DCB73A116C3A4DB47315B4B0AC`
- `work/research/apply_boundary_audit_0003_0004.py`: `2BE6E03E90022D00799DBD8E4E3813129B62909C4828ED49D747E97F13560589`
- `work/research/apply_boundary_audit_0005.py`: `EB1D216F6A7F6E144145813BE09DA90FD9D0178802033C4128955D4675EDDA91`
- `work/research/build_canonical_boundary_audit.py`: `3778EF3BFE5CD61A6B22D78D1AB26F7E1402FDF1524057BA7B131987C6AA004D`
- `work/research/validate_translation_batch.py`: `F737FB4DE8250A52670D1FE0C0E4BA609B3CEA437A4A659C6A575C3F319F4580`
- `work/research/merge_translation_batches.py`: `31BE0001A2AC005A62CEB6100CA269865391CF03CB554E41077560A0F0DBD2F2`
- `work/research/check_translation_fit.py`: `AF62002DDD574C645B8C228A2B97CE8A5BF280F06832723FFF1A5E6A7DC755B5`
- `work/research/build_checkpoint.py`: `99C3F2CED7E2967F7B9C93AEF05FA5CF1F1A57E1EDC7DA1E01483F06272C160B`
- `work/project/baseline_manifest.json`: `E2E04B0D3811F5DD57CEC6E50C4E33E9429B91CDD5DB4087B5EB4E8AAC6389C9`
