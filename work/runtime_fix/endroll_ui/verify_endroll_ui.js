const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const root = path.resolve(__dirname, '..', '..', '..');
const base = path.join(root, 'work/runtime_fix/endroll_ui');
const payloadRoot = path.join(base, 'payloads/Event/endroll');
const sourceRoot = path.join(root, 'work/disc_extracted/DATA/files/Event/endroll');
const readJson = (name) => JSON.parse(fs.readFileSync(path.join(base, name), 'utf8'));
const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex').toUpperCase();
const checks = [];
const errors = [];
const check = (name, ok, detail = null) => {
  checks.push({ name, passed: !!ok, detail });
  if (!ok) errors.push({ name, detail });
};

const map = readJson('translation_map.json');
const structural = readJson('structural_validation.json');
const visual = readJson('visual_validation.json');
const manifest = readJson('manifest.json');

const expectedNames = Array.from({ length: 23 }, (_, i) => `EV09_18_0200C_${String(i).padStart(2, '0')}.wtm`);
const actualNames = fs.readdirSync(payloadRoot).filter((n) => n.endsWith('.wtm')).sort();
check('payload_file_set_exact', JSON.stringify(actualNames) === JSON.stringify(expectedNames), actualNames);
check('translation_map_count_23', map.entry_count === 23 && map.entries.length === 23);
check('manifest_count_23', manifest.file_count === 23 && manifest.files.length === 23);
check('structural_pass_23_of_23', structural.valid === true && structural.checked_count === 23 && structural.passed_count === 23 && structural.failed_count === 0);
check('deterministic_rebuild_pass', structural.deterministic_rebuild_passed === true && structural.files.every((r) => r.deterministic_second_build_equal === true));
check('decode_reencode_pass', structural.files.every((r) => r.byte_exact_decode_reencode === true));
check('header_palette_preserved', structural.files.every((r) => r.header_palette_preserved === true));
check('dimensions_and_c4_preserved', structural.files.every((r) => r.gx_format === 'C4' && ((r.dimensions[0] === 312 || r.dimensions[0] === 320) && r.dimensions[1] === 48)));
check('visual_pass_23_of_23', visual.valid === true && visual.asset_count === 23 && visual.passed_count === 23 && visual.failed_count === 0);
check('korean_lines_one_or_two', map.entries.every((r) => r.line_count >= 1 && r.line_count <= 2 && /[가-힣]/.test(r.translation_ko)));
check('no_japanese_in_translation', map.entries.every((r) => !/[\u3040-\u30ff\u4e00-\u9fff]/.test(r.translation_ko)));
check('codex_internal_only', map.translation_policy === 'Codex internal model only' && map.external_translation_services_used.length === 0 && map.entries.every((r) => r.provenance === 'Codex internal model' && r.external_translation_used === false));

for (const row of manifest.files) {
  const name = path.basename(row.physical_path);
  const source = fs.readFileSync(path.join(sourceRoot, name));
  const payload = fs.readFileSync(path.join(payloadRoot, name));
  check(`${name}:source_hash`, sha(source) === row.source_sha256, { expected: row.source_sha256, actual: sha(source) });
  check(`${name}:payload_hash`, sha(payload) === row.payload_sha256, { expected: row.payload_sha256, actual: sha(payload) });
  check(`${name}:changed`, !source.equals(payload));
  check(`${name}:size_preserved`, source.length === payload.length && payload.length === row.size_bytes);
}

const aggregate = crypto.createHash('sha256');
for (const name of actualNames) {
  aggregate.update(name, 'utf8');
  aggregate.update(fs.readFileSync(path.join(payloadRoot, name)));
}
const aggregateSha = aggregate.digest('hex').toUpperCase();
check('payload_aggregate_hash', aggregateSha === manifest.payload_aggregate_sha256 && aggregateSha === structural.payload_aggregate_sha256, aggregateSha);

for (const contact of ['before_contact_sheet.png', 'after_contact_sheet.png']) {
  const bytes = fs.readFileSync(path.join(base, contact));
  const recorded = contact.startsWith('before') ? visual.before_contact_sheet.sha256 : visual.after_contact_sheet.sha256;
  check(`${contact}:hash`, sha(bytes) === recorded, { recorded, actual: sha(bytes) });
}

const expectedSet = new Set(expectedNames);
const findUnexpectedCopies = (start) => {
  const hits = [];
  if (!fs.existsSync(start)) return hits;
  const stack = [start];
  while (stack.length) {
    const dir = stack.pop();
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) stack.push(full);
      else if (expectedSet.has(entry.name)) hits.push(path.relative(root, full).replaceAll('\\', '/'));
    }
  }
  return hits;
};
const stagingHits = findUnexpectedCopies(path.join(root, 'work/final_runtime_staging'));
const releaseHits = findUnexpectedCopies(path.join(root, 'outputs/Arc_Rise_Fantasia_Korean_Patch_v1.0'));
check('not_written_to_staging', stagingHits.length === 0, stagingHits);
check('not_written_to_release', releaseHits.length === 0, releaseHits);

const report = {
  schema: 'arf-endroll-wtm-final-verification-v1',
  valid: errors.length === 0,
  checked_file_count: 23,
  passed_check_count: checks.filter((x) => x.passed).length,
  failed_check_count: errors.length,
  payload_aggregate_sha256: aggregateSha,
  errors,
  checks,
};
fs.writeFileSync(path.join(base, 'verification_summary.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ valid: report.valid, passed: report.passed_check_count, failed: report.failed_check_count, payload_aggregate_sha256: aggregateSha }, null, 2));
if (!report.valid) process.exitCode = 1;
