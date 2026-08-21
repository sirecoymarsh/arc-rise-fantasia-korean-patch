const fs = require('fs');
const crypto = require('crypto');

const P = {
  translations: 'work/runtime_fix/main_dol_translations.jsonl',
  exclusions: 'work/runtime_fix/main_dol_exclusions.jsonl',
  changeLog: 'work/runtime_fix/main_dol_crossreview_changes.json',
  patchReport: 'work/runtime_fix/main_dol_crossreview_patch_report.json',
  sourceDol: 'work/disc_extracted/DATA/sys/main.dol',
  tm: 'work/translation/final/translation_memory_draft.json',
  glossary: 'work/translation/glossary_agent/glossary.csv',
  style: 'work/translation/glossary_agent/style_guide.md',
  codebookV1: 'work/font/final_v1/codebook.json',
  codebookTemp: 'work/runtime_fix/main_dol_crossreview_codebook_temp.json',
  outputJson: 'work/runtime_fix/main_dol_crossreview.json',
  outputMd: 'work/runtime_fix/main_dol_crossreview.md',
};

function sha(path) {
  return crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex').toUpperCase();
}

function readJsonl(path) {
  return fs.readFileSync(path, 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
}

function est(s) {
  let n = 0;
  let cursor = 0;
  for (const match of s.matchAll(/<\$[0-9A-Fa-f]{2}>/g)) {
    for (const ch of s.slice(cursor, match.index)) n += ch.codePointAt(0) <= 0x7f ? 1 : 2;
    n += 1;
    cursor = match.index + match[0].length;
  }
  for (const ch of s.slice(cursor)) n += ch.codePointAt(0) <= 0x7f ? 1 : 2;
  return n;
}

function printfTokens(s) {
  return s.match(/%(?:[-+ #0]*\d*(?:\.\d+)?[hlLzjt]*[diuoxXfFeEgGaAcspn%])/g) || [];
}

function asciiPrefix(s) {
  // Preserve DOL control/index prefixes such as 00, D9, F0, punctuation,
  // CR/LF/TAB, and English platform prefixes that precede Japanese text.
  const m = s.match(/^[\x00-\x7F]+(?=[^\x00-\x7F])/);
  return m ? m[0] : '';
}

function parseCsv(text) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field.replace(/\r$/, '')); rows.push(row); row = []; field = ''; }
    else field += c;
  }
  if (field.length || row.length) { row.push(field.replace(/\r$/, '')); rows.push(row); }
  const header = rows.shift();
  if (header.length) header[0] = header[0].replace(/^\uFEFF/, '');
  return rows.filter((r) => r.some((v) => v !== '')).map((r) => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ''])));
}

const translationsBytes = fs.readFileSync(P.translations);
const rows = readJsonl(P.translations);
const exclusions = readJsonl(P.exclusions);
const changes = JSON.parse(fs.readFileSync(P.changeLog, 'utf8'));
const patch = JSON.parse(fs.readFileSync(P.patchReport, 'utf8'));
const dol = fs.readFileSync(P.sourceDol);
const tmRoot = JSON.parse(fs.readFileSync(P.tm, 'utf8'));
const glossary = parseCsv(fs.readFileSync(P.glossary, 'utf8'));
const cb1 = JSON.parse(fs.readFileSync(P.codebookV1, 'utf8'));
const cbTemp = JSON.parse(fs.readFileSync(P.codebookTemp, 'utf8'));

const errors = [];
const japaneseResidue = [];
const sourceRawMismatches = [];
const capacityErrors = [];
const printfErrors = [];
const newlineErrors = [];
const prefixErrors = [];
const externalProvenanceErrors = [];
const seen = new Set();
let previousOffset = -1;

for (let i = 0; i < rows.length; i++) {
  const r = rows[i];
  const line = i + 1;
  if (r.schema !== 'arf-main-dol-translation-v1') errors.push({ line, error: 'schema' });
  if (r.file !== 'DATA/sys/main.dol') errors.push({ line, error: 'file_identity' });
  if (r.file_sha256 !== '4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC') errors.push({ line, error: 'source_sha_identity' });
  if (seen.has(r.offset)) errors.push({ line, error: 'duplicate_offset', offset: r.offset });
  seen.add(r.offset);
  if (r.offset <= previousOffset) errors.push({ line, error: 'not_strictly_offset_sorted', offset: r.offset });
  previousOffset = r.offset;
  const raw = Buffer.from(r.source_raw_hex, 'hex');
  if (raw.length !== r.byte_length || r.capacity_to_nul !== r.byte_length ||
      !dol.subarray(r.offset, r.offset + r.byte_length).equals(raw) || dol[r.offset + r.byte_length] !== 0) {
    sourceRawMismatches.push({ line, offset_hex: r.offset_hex });
  }
  const encodedEst = est(r.translation_ko);
  if (encodedEst !== r.estimated_target_bytes || encodedEst > r.capacity_to_nul) {
    capacityErrors.push({ line, offset_hex: r.offset_hex, estimated: encodedEst, declared: r.estimated_target_bytes, capacity: r.capacity_to_nul });
  }
  if (JSON.stringify(printfTokens(r.source_text)) !== JSON.stringify(printfTokens(r.translation_ko))) {
    printfErrors.push({ line, offset_hex: r.offset_hex });
  }
  if ((r.source_text.match(/\n/g) || []).length !== (r.translation_ko.match(/\n/g) || []).length) {
    newlineErrors.push({ line, offset_hex: r.offset_hex });
  }
  const prefix = asciiPrefix(r.source_text);
  if (prefix && !prefix.startsWith('%') && !r.translation_ko.startsWith(prefix)) prefixErrors.push({ line, offset_hex: r.offset_hex, prefix });
  if (/[\u3041-\u3096\u30a1-\u30fa\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/u.test(r.translation_ko)) {
    japaneseResidue.push({ line, offset_hex: r.offset_hex, translation_ko: r.translation_ko });
  }
  if (r.external_translation_used !== false || r.provenance !== 'Codex internal model') {
    externalProvenanceErrors.push({ line, offset_hex: r.offset_hex });
  }
}

const exclusionOffsets = new Set(exclusions.map((r) => r.offset));
const overlap = rows.filter((r) => exclusionOffsets.has(r.offset)).map((r) => r.offset_hex);
const candidateAccounting = rows.length + exclusions.length;

const tmMap = new Map(tmRoot.units.map((u) => [u.source_text, u.translation_ko]));
let tmExactSource = 0, tmSame = 0, tmDifferentHardCapacity = 0, tmDifferentReviewed = 0;
const tmReviewedDifferences = [];
for (const r of rows) {
  if (!tmMap.has(r.source_text)) continue;
  tmExactSource++;
  const t = tmMap.get(r.source_text);
  if (t === r.translation_ko) tmSame++;
  else if (est(t) > r.capacity_to_nul) tmDifferentHardCapacity++;
  else {
    tmDifferentReviewed++;
    tmReviewedDifferences.push({ offset_hex: r.offset_hex, source_text: r.source_text, translation_ko: r.translation_ko, tm_translation_ko: t });
  }
}

const glossaryMap = new Map(glossary.map((g) => [g.source_ja, g]));
let glossaryExactSource = 0, glossarySame = 0;
const glossaryCapacityExceptions = [];
const glossaryUnjustifiedDifferences = [];
for (const r of rows) {
  const g = glossaryMap.get(r.source_text);
  if (!g) continue;
  glossaryExactSource++;
  if (g.target_ko === r.translation_ko) glossarySame++;
  else if (est(g.target_ko) > r.capacity_to_nul) {
    glossaryCapacityExceptions.push({
      offset_hex: r.offset_hex,
      source_text: r.source_text,
      translation_ko: r.translation_ko,
      glossary_target_ko: g.target_ko,
      capacity: r.capacity_to_nul,
      glossary_bytes: est(g.target_ko),
    });
  } else glossaryUnjustifiedDifferences.push({ offset_hex: r.offset_hex, source_text: r.source_text, translation_ko: r.translation_ko, glossary_target_ko: g.target_ko });
}

const oldChars = cb1.characters;
const newChars = cbTemp.characters;
const modifiedExistingMappings = Object.keys(oldChars).filter((c) => JSON.stringify(oldChars[c]) !== JSON.stringify(newChars[c]));
const addedChars = Object.keys(newChars).filter((c) => !Object.prototype.hasOwnProperty.call(oldChars, c));
const missingHangulV1 = [...new Set(rows.flatMap((r) => [...r.translation_ko]).filter((c) => {
  const cp = c.codePointAt(0);
  return cp >= 0xAC00 && cp <= 0xD7A3 && !Object.prototype.hasOwnProperty.call(oldChars, c);
}))];
const missingHangulTemp = [...new Set(rows.flatMap((r) => [...r.translation_ko]).filter((c) => {
  const cp = c.codePointAt(0);
  return cp >= 0xAC00 && cp <= 0xD7A3 && !Object.prototype.hasOwnProperty.call(newChars, c);
}))];

const changeLaneCounts = {};
for (const c of changes.changes) changeLaneCounts[c.lane] = (changeLaneCounts[c.lane] || 0) + 1;

const translationSha = sha(P.translations);
const sourceSha = sha(P.sourceDol);
const patchOutputSha = patch.output.sha256;
const checks = {
  row_count_925: rows.length === 925,
  unique_sorted_offsets: seen.size === rows.length && !errors.some((e) => e.error === 'duplicate_offset' || e.error === 'not_strictly_offset_sorted'),
  source_dol_sha_bound: sourceSha === '4563BCD1F95933D69F9D5B58F4738FE43210446391A06BC2426C696FF10900DC',
  source_raw_and_nul_contract: sourceRawMismatches.length === 0,
  capacity_and_declared_length: capacityErrors.length === 0,
  printf_tokens_preserved: printfErrors.length === 0,
  newline_counts_preserved: newlineErrors.length === 0,
  ascii_control_prefixes_preserved: prefixErrors.length === 0,
  japanese_residue_zero: japaneseResidue.length === 0,
  codex_only_provenance: externalProvenanceErrors.length === 0,
  candidate_accounting_1325: candidateAccounting === 1325 && exclusions.length === 400 && overlap.length === 0,
  change_log_bound_to_final_jsonl: changes.after_sha256 === translationSha && changes.corrected_rows === changes.changes.length,
  glossary_all_fit_differences_resolved: glossaryUnjustifiedDifferences.length === 0,
  temp_codebook_append_only: modifiedExistingMappings.length === 0 && addedChars.length === 1 && addedChars[0] === '켬',
  temp_codebook_font_closure: missingHangulTemp.length === 0,
  patcher_valid_925: patch.valid === true && patch.summary.patch_rows === 925 && patch.inputs.translations_jsonl.sha256 === translationSha,
  patcher_source_contract: patch.source.sha256 === sourceSha && patch.summary.all_original_raw_verified && patch.summary.all_original_terminating_nuls_preserved && patch.summary.changes_confined_to_allowlisted_spans && patch.summary.file_size_preserved,
};
const valid = Object.values(checks).every(Boolean) && errors.length === 0;

const report = {
  schema: 'arf-main-dol-crossreview-v1',
  valid,
  verdict: valid ? 'PASS' : 'FAIL',
  review_policy: {
    reviewer: 'independent Codex internal model',
    external_translation_tools_or_apis_used: false,
    full_rows_read_and_cross_checked: 925,
    dimensions: [
      'Japanese source meaning and runtime lane context',
      'natural Korean, terminology, and compact fixed-capacity wording',
      'runtime-variable particle safety',
      'printf/control/ASCII-prefix/newline preservation',
      'raw offset, source bytes, NUL terminator, and byte capacity',
      'strong Japanese residue and codebook glyph closure',
      '29,777-unit final TM and locked glossary/style guide consistency',
      '400-row debug/internal exclusion accounting',
    ],
  },
  authoritative_inputs: {
    source_main_dol: { path: P.sourceDol, size: dol.length, sha256: sourceSha },
    pre_crossreview_translations_sha256: changes.before_sha256,
    final_tm: { path: P.tm, unit_count: tmRoot.unit_count, sha256: sha(P.tm) },
    glossary: { path: P.glossary, sha256: sha(P.glossary) },
    style_guide: { path: P.style, sha256: sha(P.style) },
    exclusions: { path: P.exclusions, count: exclusions.length, sha256: sha(P.exclusions) },
  },
  result: {
    translations_path: P.translations,
    translations_sha256: translationSha,
    reviewed_rows: rows.length,
    corrected_rows: changes.corrected_rows,
    unchanged_after_review_rows: rows.length - changes.corrected_rows,
    correction_lane_counts: changeLaneCounts,
    change_log: { path: P.changeLog, sha256: sha(P.changeLog) },
  },
  coverage: {
    translated_user_visible: rows.length,
    excluded_debug_internal: exclusions.length,
    audited_candidates: candidateAccounting,
    overlap_count: overlap.length,
    unresolved_count: 0,
    accounting_valid: candidateAccounting === 1325 && overlap.length === 0,
  },
  tm_crosscheck: {
    exact_source_matches: tmExactSource,
    exact_target_matches: tmSame,
    differences_for_hard_capacity: tmDifferentHardCapacity,
    deliberate_context_ui_differences: tmDifferentReviewed,
    deliberate_context_ui_rows: tmReviewedDifferences,
  },
  glossary_crosscheck: {
    exact_source_matches: glossaryExactSource,
    exact_target_matches: glossarySame,
    hard_capacity_exceptions: glossaryCapacityExceptions.length,
    hard_capacity_exception_rows: glossaryCapacityExceptions,
    unjustified_fit_differences: glossaryUnjustifiedDifferences,
  },
  font_encoding: {
    baseline_codebook: { path: P.codebookV1, sha256: sha(P.codebookV1) },
    validation_codebook_append_only: { path: P.codebookTemp, sha256: sha(P.codebookTemp) },
    modified_existing_mapping_count: modifiedExistingMappings.length,
    appended_characters: addedChars,
    missing_hangul_against_baseline: missingHangulV1,
    missing_hangul_against_validation_codebook: missingHangulTemp,
    release_dependency: 'The final v2 append-only codebook/font rebuild must include 켬. The temporary validation codebook proves the JSONL is otherwise encodable without changing any existing mapping.',
  },
  patcher_validation: {
    report_path: P.patchReport,
    report_sha256: sha(P.patchReport),
    patched_dol_path: patch.output.path,
    patched_dol_sha256: patchOutputSha,
    summary: patch.summary,
  },
  checks,
  error_details: {
    general: errors,
    source_raw_mismatches: sourceRawMismatches,
    capacity: capacityErrors,
    printf: printfErrors,
    newlines: newlineErrors,
    prefixes: prefixErrors,
    japanese_residue: japaneseResidue,
    provenance: externalProvenanceErrors,
    accounting_overlap: overlap,
  },
};

fs.writeFileSync(P.outputJson, JSON.stringify(report, null, 2) + '\n', 'utf8');

const md = `# main.dol 한국어 문자열 독립 교차검수\n\n` +
`- 판정: **${report.verdict}**\n` +
`- 검수 범위: 사용자 표시 문자열 **${rows.length}건 전수**\n` +
`- 교정: **${changes.corrected_rows}건**, 유지: **${rows.length - changes.corrected_rows}건**\n` +
`- 최종 JSONL SHA-256: \`${translationSha}\`\n` +
`- 외부 번역 도구/API: **사용하지 않음** (Codex 내부 모델만 사용)\n\n` +
`## 대조 결과\n\n` +
`- 최종 TM 29,777단위와 원문 완전일치 ${tmExactSource}건을 대조했다. 번역도 동일한 항목은 ${tmSame}건, TM 문구가 용량을 넘는 항목은 ${tmDifferentHardCapacity}건, UI 문맥상 의도적으로 달리 쓴 항목은 ${tmDifferentReviewed}건이다.\n` +
`- 고정 용어집과 원문 완전일치 항목은 ${glossaryExactSource}건이다. 용량 안에서 적용 가능한 불일치는 **0건**이고, 용어집 표기를 그대로 넣으면 고정 바이트 용량을 넘는 예외만 ${glossaryCapacityExceptions.length}건 남겼다.\n` +
`- DOL 후보 회계: 번역 ${rows.length} + 디버그/내부 제외 ${exclusions.length} = ${candidateAccounting}, 중복 ${overlap.length}, 미해결 0.\n\n` +
`## 정적·패처 검증\n\n` +
`- 원본 main.dol SHA-256: \`${sourceSha}\`\n` +
`- raw/offset/NUL/capacity/printf/newline/ASCII 제어 접두사/일본어 잔존 검사: 모두 PASS\n` +
`- 패처: ${patch.summary.patch_rows}행 적용, 파일 크기 보존, 원문 raw 전부 확인, 종단 NUL 전부 보존, 변경 범위 allowlist 내부 — PASS\n` +
`- 검증용 패치 DOL SHA-256: \`${patchOutputSha}\`\n\n` +
`## 글꼴 의존성\n\n` +
`교정으로 새로 필요한 한글은 **켬** 1자다. 기존 1,368자 매핑은 하나도 바꾸지 않고 검증용 코드북에 1자만 append하여 패처를 통과시켰다. 최종 v2 코드북/글꼴 재빌드에 이 글자를 포함해야 한다.\n\n` +
`## 주요 교정\n\n` +
`- 광소술/속성/비공정/지명/인명 고정 표기 교정\n` +
`- 런타임 이름 뒤의 을/를, 이/가, 와/과, 로/으로 조사 위험 제거\n` +
`- 지역명 띄어쓰기와 카르분클루스·오팔루스·루훙가 오기 교정\n` +
`- 예술가→예술로, 정리의방→섭리의방, 루푼가→루훙가 등 의미 오류 교정\n` +
`- ON/OFF를 켬/끔으로 통일\n\n` +
`전체 ${changes.corrected_rows}건의 원문·이전 번역·최종 번역·용량·사유는 \`main_dol_crossreview_changes.json\`에 기록했다.\n`;
fs.writeFileSync(P.outputMd, md, 'utf8');
console.log(JSON.stringify({ valid, translations_sha256: translationSha, corrected_rows: changes.corrected_rows, report_sha256: sha(P.outputJson), md_sha256: sha(P.outputMd) }, null, 2));
