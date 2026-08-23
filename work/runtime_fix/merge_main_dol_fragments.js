const fs = require('fs');
const crypto = require('crypto');
const probe = JSON.parse(fs.readFileSync('work/catalog/text_probe_10.json', 'utf8'));
const dol = fs.readFileSync('work/disc_extracted/DATA/sys/main.dol');
const byOffset = new Map(probe.records.map((r) => [r.offset, r]));
const files = [
  'main_dol_priority_fragment.jsonl',
  'main_dol_lower_fragment.jsonl',
  'main_dol_upper_fragment.jsonl',
  'main_dol_map_fragment.jsonl',
  'main_dol_area_fragment.jsonl',
];
const merged = new Map();
const conflicts = [];
for (const file of files) {
  for (const line of fs.readFileSync('work/runtime_fix/' + file, 'utf8').trim().split(/\r?\n/)) {
    if (!line) continue;
    const row = JSON.parse(line);
    if (merged.has(row.offset)) {
      if (merged.get(row.offset).translation_ko !== row.translation_ko) {
        conflicts.push({
          offset: row.offset,
          offset_hex: `0x${row.offset.toString(16).toUpperCase().padStart(8, '0')}`,
          kept: merged.get(row.offset).translation_ko,
          alternate: row.translation_ko,
          alternate_file: file,
          resolution: row.offset === 0x3c9e96 ? 'kept_neutral_particle_safe_wording' : 'kept_priority_fragment',
        });
      }
    } else {
      merged.set(row.offset, row);
    }
  }
}

function est(s) {
  let n = 0;
  let cursor = 0;
  for (const match of s.matchAll(/<\$[0-9A-Fa-f]{2}>/g)) {
    for (const c of s.slice(cursor, match.index)) n += c.codePointAt(0) <= 0x7f ? 1 : 2;
    n += 1;
    cursor = match.index + match[0].length;
  }
  for (const c of s.slice(cursor)) n += c.codePointAt(0) <= 0x7f ? 1 : 2;
  return n;
}
function tokens(s) {
  return s.match(/%(?:\d+\$)?[-+#0 .\dhlL]*[diouxXeEfFgGaAcspn%]/g) || [];
}

const validationErrors = [];
const out = [...merged.values()].sort((a, b) => a.offset - b.offset).map((row) => {
  // Some reviewed rows deliberately combine adjacent probe fragments into one
  // semantic fixed-width unit (for example a control byte between two map
  // labels).  Such rows carry their own source identity and must not be
  // rejected merely because the older probe catalog split them.
  const probeSrc = byOffset.get(row.offset);
  const src = probeSrc || {
    byte_length: row.byte_length,
    capacity_to_nul: row.capacity_to_nul,
    text: row.source_text,
    raw_hex: row.source_raw_hex,
  };
  if (!Number.isInteger(src.byte_length) || !Number.isInteger(src.capacity_to_nul) ||
      typeof src.text !== 'string' || typeof src.raw_hex !== 'string') {
    throw new Error(`source identity missing at 0x${row.offset.toString(16)}`);
  }
  const actualRaw = dol.subarray(row.offset, row.offset + src.byte_length).toString('hex').toUpperCase();
  if (actualRaw !== src.raw_hex.toUpperCase()) validationErrors.push({ offset: row.offset, error: 'source_raw_mismatch' });
  const targetBytes = est(row.translation_ko);
  if (targetBytes > src.capacity_to_nul) validationErrors.push({ offset: row.offset, error: 'target_over_capacity', targetBytes, capacity: src.capacity_to_nul });
  if (JSON.stringify(tokens(src.text)) !== JSON.stringify(tokens(row.translation_ko))) validationErrors.push({ offset: row.offset, error: 'printf_placeholder_mismatch' });
  return {
    schema: 'arf-main-dol-translation-v1',
    file: 'DATA/sys/main.dol',
    file_sha256: probe.source_sha256.toUpperCase(),
    offset: row.offset,
    offset_hex: `0x${row.offset.toString(16).toUpperCase().padStart(8, '0')}`,
    byte_length: src.byte_length,
    capacity_to_nul: src.capacity_to_nul,
    source_encoding: 'EUC-JP',
    source_text: src.text,
    source_raw_hex: src.raw_hex.toUpperCase(),
    translation_ko: row.translation_ko,
    estimated_target_bytes: targetBytes,
    context: row.context || '런타임 사용자 표시 문자열',
    lane: row.lane || 'runtime_ui',
    visibility: 'runtime_user_visible',
    provenance: 'Codex internal model',
    external_translation_used: false,
  };
});

const lowerReport = JSON.parse(fs.readFileSync('work/runtime_fix/main_dol_lower_fragment_report.json', 'utf8'));
const lowerReasons = new Map(lowerReport.exclusions.map((x) => [x.offset, x.reason]));
const areaReport = JSON.parse(fs.readFileSync('work/runtime_fix/main_dol_area_fragment_report.json', 'utf8'));
const mapReport = JSON.parse(fs.readFileSync('work/runtime_fix/main_dol_map_fragment_report.json', 'utf8'));
const explicitReasons = new Map();
for (const x of [...areaReport.excluded, ...mapReport.excluded]) explicitReasons.set(Number.parseInt(x.offset_hex.slice(2), 16), x.reason);
function upperReason(r) {
  if (lowerReasons.has(r.offset)) return lowerReasons.get(r.offset);
  if (explicitReasons.has(r.offset)) return explicitReasons.get(r.offset);
  if (r.offset === 0x3d3937 || r.offset === 0x3d88ce) return 'false_positive_binary_candidate';
  if (/（テスト）|デバッグ用|ＴＥＳＴ|テストマップ|戦闘サンプル|モデルビュアー|マップ確認|エンカウントエフェクト/.test(r.text)) return 'unavailable_test_or_debug_menu';
  if (/予備枠/.test(r.text)) return 'reserved_internal_slot';
  return 'developer_log_assert_or_runtime_diagnostic';
}
const validCandidates = probe.records.filter((r) => r.offset >= 0x3c64f7 && r.offset <= 0x3f1dd9);
const selectedOffsets = new Set(out.map((r) => r.offset));
const selectedSpans = out.map((r) => [r.offset, r.offset + r.byte_length]);
const coveredBySelectedSpan = (r) => selectedSpans.some(([start, end]) =>
  start <= r.offset && r.offset + r.byte_length <= end
);
const exclusions = validCandidates.filter((r) => !coveredBySelectedSpan(r)).map((r) => ({
  offset: r.offset,
  offset_hex: `0x${r.offset.toString(16).toUpperCase().padStart(8, '0')}`,
  source_text: r.text,
  byte_length: r.byte_length,
  reason: upperReason(r),
}));
const reasonCounts = {};
for (const x of exclusions) reasonCounts[x.reason] = (reasonCounts[x.reason] || 0) + 1;
const laneCounts = {};
for (const x of out) laneCounts[x.lane] = (laneCounts[x.lane] || 0) + 1;

fs.writeFileSync('work/runtime_fix/main_dol_translations.jsonl', out.map((x) => JSON.stringify(x)).join('\n') + '\n', 'utf8');
fs.writeFileSync('work/runtime_fix/main_dol_exclusions.jsonl', exclusions.map((x) => JSON.stringify(x)).join('\n') + '\n', 'utf8');

const report = {
  schema: 'arf-main-dol-complete-user-visible-audit-v1',
  source_file: 'work/disc_extracted/DATA/sys/main.dol',
  source_size: dol.length,
  source_sha256: crypto.createHash('sha256').update(dol).digest('hex').toUpperCase(),
  audited_offset_start: '0x003C64F7',
  audited_offset_end: '0x003F1DD9',
  candidate_count: validCandidates.length,
  user_visible_translated_count: out.length,
  excluded_debug_internal_count: exclusions.length,
  unresolved_count: validationErrors.length,
  accounting_valid: out.length + exclusions.length === validCandidates.length,
  lane_counts: laneCounts,
  exclusion_counts_by_reason: reasonCounts,
  merge_conflicts: conflicts,
  validation: {
    original_raw_match_count: validCandidates.filter((r) => dol.subarray(r.offset, r.offset + r.byte_length).toString('hex').toUpperCase() === r.raw_hex.toUpperCase()).length,
    original_raw_mismatch_count: validCandidates.filter((r) => dol.subarray(r.offset, r.offset + r.byte_length).toString('hex').toUpperCase() !== r.raw_hex.toUpperCase()).length,
    estimated_capacity_overflow_count: validationErrors.filter((x) => x.error === 'target_over_capacity').length,
    printf_placeholder_mismatch_count: validationErrors.filter((x) => x.error === 'printf_placeholder_mismatch').length,
    newline_mismatch_count: out.filter((x) => (x.source_text.match(/\n/g) || []).length !== (x.translation_ko.match(/\n/g) || []).length).length,
    duplicate_offset_count: out.length - selectedOffsets.size,
    errors: validationErrors,
  },
  translation_provenance: 'Codex internal model only; no external translation service or external generative model used',
  outputs: {
    translations: 'work/runtime_fix/main_dol_translations.jsonl',
    exclusions: 'work/runtime_fix/main_dol_exclusions.jsonl',
  },
};
fs.writeFileSync('work/runtime_fix/main_dol_translation_report.json', JSON.stringify(report, null, 2) + '\n', 'utf8');
fs.writeFileSync('work/runtime_fix/main_dol_merge_conflicts.json', JSON.stringify({ row_count: out.length, conflict_count: conflicts.length, conflicts }, null, 2) + '\n', 'utf8');
console.log(JSON.stringify(report, null, 2));
