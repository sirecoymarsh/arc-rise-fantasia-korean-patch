const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = process.cwd();
const rel = (p) => p.replaceAll('\\', '/');
const read = (p) => fs.readFileSync(p);
const json = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));
const sha256 = (b) => crypto.createHash('sha256').update(b).digest('hex').toUpperCase();
const hex = (n, width = 0) => `0x${n.toString(16).toUpperCase().padStart(width, '0')}`;
const eucjp = new TextDecoder('euc-jp');

function statEvidence(p) {
  const b = read(p);
  return { path: rel(p), size_bytes: b.length, sha256: sha256(b) };
}

function encodeUtf16BE(s) {
  const le = Buffer.from(s, 'utf16le');
  const out = Buffer.alloc(le.length);
  for (let i = 0; i + 1 < le.length; i += 2) {
    out[i] = le[i + 1];
    out[i + 1] = le[i];
  }
  return out;
}

function parseU8(p) {
  const b = read(p);
  if (b.readUInt32BE(0) !== 0x55aa382d) throw new Error(`not U8: ${p}`);
  const root = b.readUInt32BE(4);
  const count = b.readUInt32BE(root + 8);
  const strings = root + count * 12;
  const nodes = [];
  for (let i = 0; i < count; i += 1) {
    const no = root + i * 12;
    const typeName = b.readUInt32BE(no);
    const type = typeName >>> 24;
    const nameOffset = typeName & 0xffffff;
    let end = strings + nameOffset;
    while (end < b.length && b[end] !== 0) end += 1;
    nodes.push({
      index: i,
      type,
      name: b.subarray(strings + nameOffset, end).toString('utf8'),
      offset: b.readUInt32BE(no + 4),
      size: b.readUInt32BE(no + 8),
    });
  }
  const stack = [{ end: nodes[0].size, path: '' }];
  for (let i = 1; i < nodes.length; i += 1) {
    while (stack.length && i >= stack.at(-1).end) stack.pop();
    const n = nodes[i];
    const parent = stack.at(-1)?.path || '';
    n.path = `${parent ? `${parent}/` : ''}${n.name}`;
    if (n.type === 1) stack.push({ end: n.size, path: n.path });
  }
  return { bytes: b, root_offset: root, node_count: count, nodes };
}

function parseBrfntCmaps(b) {
  const cmaps = [];
  for (let off = 0; off <= b.length - 20; off += 4) {
    if (b.subarray(off, off + 4).toString('ascii') !== 'CMAP') continue;
    const size = b.readUInt32BE(off + 4);
    const codeBegin = b.readUInt16BE(off + 8);
    const codeEnd = b.readUInt16BE(off + 10);
    const method = b.readUInt16BE(off + 12);
    const next = b.readUInt32BE(off + 16);
    const mapped = [];
    if (method === 0) {
      const firstGlyph = b.readUInt16BE(off + 20);
      for (let cp = codeBegin; cp <= codeEnd; cp += 1) mapped.push(cp);
      void firstGlyph;
    } else if (method === 1) {
      for (let cp = codeBegin; cp <= codeEnd; cp += 1) {
        const glyph = b.readUInt16BE(off + 20 + (cp - codeBegin) * 2);
        if (glyph !== 0xffff) mapped.push(cp);
      }
    } else if (method === 2) {
      const count = b.readUInt16BE(off + 20);
      for (let i = 0; i < count; i += 1) mapped.push(b.readUInt16BE(off + 22 + i * 4));
    }
    cmaps.push({
      section_offset: off,
      section_offset_hex: hex(off),
      section_size: size,
      section_size_hex: hex(size),
      code_begin: codeBegin,
      code_begin_hex: `U+${codeBegin.toString(16).toUpperCase().padStart(4, '0')}`,
      code_end: codeEnd,
      code_end_hex: `U+${codeEnd.toString(16).toUpperCase().padStart(4, '0')}`,
      mapping_method: method,
      next_pointer: next,
      next_pointer_hex: hex(next),
      mapped_codepoints: mapped.map((cp) => `U+${cp.toString(16).toUpperCase().padStart(4, '0')}`),
      mapped_count: mapped.length,
      mapped_hangul_syllable_count: mapped.filter((cp) => cp >= 0xac00 && cp <= 0xd7a3).length,
    });
    off += size - 4;
  }
  return cmaps;
}

// Current pipeline evidence.
const probePath = 'work/catalog/text_probe_10.json';
const catalogPath = 'work/catalog/text_v2/text_catalog.json';
const catalogSummaryPath = 'work/catalog/text_v2/text_catalog_summary.json';
const stagingPath = 'work/final_runtime_staging/staging_manifest.json';
const reinsertionPath = 'work/image_ui_final/reinsertion_manifest.json';
const imageExclusionsPath = 'work/image_ui_final/reports/image_exclusions.json';
const probe = json(probePath);
const catalog = json(catalogPath);
const catalogSummary = json(catalogSummaryPath);
const staging = json(stagingPath);
const reinsertion = json(reinsertionPath);
const stagedPaths = staging.static_validation.staged_files.map((x) => x.physical_path);
const stagedSet = new Set(stagedPaths);
const stagingRoots = {};
for (const p of stagedPaths) stagingRoots[p.split('/')[0]] = (stagingRoots[p.split('/')[0]] || 0) + 1;
const catalogPaths = [...new Set(catalog.records.map((r) => r.physical_path))];

// DOL mapping and exact player-facing records. The audit uses only original bytes/raw probe data;
// the JSONL supplies the already-reviewed visibility/lane offset set, not target translations.
const dolPath = 'work/disc_extracted/DATA/sys/main.dol';
const dol = read(dolPath);
const selectedLines = fs.readFileSync('work/runtime_fix/main_dol_translations.jsonl', 'utf8')
  .trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
const probeByOffset = new Map(probe.records.map((r) => [r.offset, r]));
const dolSection = {
  type: 'data',
  data_index_zero_based: 4,
  overall_dol_section_index_zero_based: 11,
  file_start: 0x3c5c00,
  file_end_exclusive: 0x3e50a0,
  ram_start: 0x803c9b00,
  ram_end_exclusive: 0x803e8fa0,
};
function dolRecord(offset, lane = undefined) {
  const r = probeByOffset.get(offset);
  if (!r) throw new Error(`DOL probe offset missing: ${hex(offset)}`);
  const raw = Buffer.from(r.raw_hex, 'hex');
  if (!dol.subarray(offset, offset + raw.length).equals(raw)) throw new Error(`DOL bytes mismatch: ${hex(offset)}`);
  const ram = dolSection.ram_start + (offset - dolSection.file_start);
  return {
    lane,
    file_offset: offset,
    file_offset_hex: hex(offset, 8),
    ram_address: ram,
    ram_address_hex: hex(ram, 8),
    byte_length: r.byte_length,
    capacity_to_nul: r.capacity_to_nul,
    source_encoding: 'EUC-JP',
    source_text_jp: eucjp.decode(raw),
    raw_hex: r.raw_hex.toUpperCase(),
    raw_sha256: sha256(raw),
  };
}
const confirmedDol = selectedLines.map((x) => dolRecord(x.offset, x.lane));
const initialDol = confirmedDol.filter((r) => r.lane === 'initial_setup');
const laneCounts = {};
for (const r of confirmedDol) laneCounts[r.lane] = (laneCounts[r.lane] || 0) + 1;

const deferredVisibleRanges = [
  { start: 0x3d15c1, end: 0x3d1c9b, label: 'casino_poker_dictionary_and_shared_ui' },
  { start: 0x3d1e4c, end: 0x3d216b, label: 'map_names_route_labels_and_story_lines' },
  { start: 0x3d2636, end: 0x3d27d9, label: 'copin_race_ui_and_announcer' },
  { start: 0x3d2ca0, end: 0x3d2ca0, label: 'monster_dictionary_unlock_notification' },
];
const confirmedOffsets = new Set(confirmedDol.map((r) => r.file_offset));
const deferredDol = [];
for (const range of deferredVisibleRanges) {
  for (const r of probe.records.filter((x) => x.offset >= range.start && x.offset <= range.end)) {
    if (confirmedOffsets.has(r.offset)) continue;
    deferredDol.push({ ...dolRecord(r.offset, 'deferred_player_facing'), range: range.label });
  }
}

// HBM CSV exact first-column strings.
const hbmCsvSpecs = {
  'Hbm/home.csv': [
    '接続する順番に\r\n①ボタンと②ボタンを\r\n同時に押してください。',
    '切断中・・・',
    'Wiiメニューにもどりますか？\r\n（保存していない内容は失われます）',
    'リセットしますか？\r\n（保存していない内容は失われます）',
  ],
  'Hbm/home_nosave.csv': [
    '接続する順番に\r\n①ボタンと②ボタンを\r\n同時に押してください。',
    '切断中・・・',
    'Wiiメニューにもどりますか？',
    'リセットしますか？',
  ],
};
const hbmCsvFiles = [];
for (const [physicalPath, strings] of Object.entries(hbmCsvSpecs)) {
  const p = `work/disc_extracted/DATA/files/${physicalPath}`;
  const b = read(p);
  const records = strings.map((text) => {
    const raw = encodeUtf16BE(text);
    const offset = b.indexOf(raw);
    if (offset < 0) throw new Error(`HBM string missing: ${physicalPath}: ${text}`);
    return {
      byte_offset: offset,
      byte_offset_hex: hex(offset),
      byte_length: raw.length,
      source_encoding: 'UTF-16BE',
      source_text_jp: text,
      raw_hex: raw.toString('hex').toUpperCase(),
      raw_sha256: sha256(raw),
    };
  });
  hbmCsvFiles.push({
    physical_path: physicalPath,
    source_path: rel(p),
    source_size: b.length,
    source_sha256: sha256(b),
    bom_hex: b.subarray(0, 2).toString('hex').toUpperCase(),
    staged_in_current_655: stagedSet.has(physicalPath),
    records,
  });
}

// HBM base archive: 18 baked Japanese text TPL members plus a font that has no Hangul mappings.
const homeBtnPhysical = 'Hbm/homeBtn.arc';
const homeBtnPath = `work/disc_extracted/DATA/files/${homeBtnPhysical}`;
const homeBtn = parseU8(homeBtnPath);
const homeTextureText = {
  'tx_btn_00.tpl': 'とじる',
  'tx_btn_L_00.tpl': 'Wiiメニューへ',
  'tx_btn_L_11.tpl': 'リセット',
  'tx_cntrl_00.tpl': 'Wiiリモコンの設定',
  'tx_cntrl_01.tpl': 'Wiiリモコンの設定をとじる',
  'tx_msgBtn_00.tpl': 'はい',
  'tx_msgBtn_01.tpl': 'いいえ',
  'tx_optnBtn_10.tpl': 'ON',
  'tx_optnBtn_11.tpl': 'OFF',
  'tx_optnBtn_20.tpl': 'つなぎなおす',
  'tx_optn_00.tpl': '音量',
  'tx_optn_10.tpl': '振動',
  'tx_optn_20.tpl': '接続',
  'tx_plyr_00.tpl': '1P',
  'tx_plyr_01.tpl': '2P',
  'tx_plyr_02.tpl': '3P',
  'tx_plyr_03.tpl': '4P',
  'tx_ttl_wrd_a.tpl': 'HOMEボタンメニュー',
};
const homeTextures = homeBtn.nodes.filter((n) => !n.type && Object.hasOwn(homeTextureText, n.name)).map((n) => {
  const member = homeBtn.bytes.subarray(n.offset, n.offset + n.size);
  const imageHeader = n.offset + 0x14;
  const height = homeBtn.bytes.readUInt16BE(imageHeader);
  const width = homeBtn.bytes.readUInt16BE(imageHeader + 2);
  const gxFormat = homeBtn.bytes.readUInt32BE(imageHeader + 4);
  const imageDataRelative = homeBtn.bytes.readUInt32BE(imageHeader + 8);
  return {
    member_path: n.path,
    member_index: n.index,
    archive_offset: n.offset,
    archive_offset_hex: hex(n.offset),
    size_bytes: n.size,
    sha256: sha256(member),
    tpl_width: width,
    tpl_height: height,
    tpl_gx_format: gxFormat,
    tpl_gx_format_name: gxFormat === 0 ? 'I4' : 'UNKNOWN',
    tpl_image_data_relative_offset: imageDataRelative,
    tpl_image_data_relative_offset_hex: hex(imageDataRelative),
    tpl_image_data_archive_offset_hex: hex(n.offset + imageDataRelative),
    visible_source_text_jp: homeTextureText[n.name],
  };
}).sort((a, b) => a.member_index - b.member_index);
const fontNode = homeBtn.nodes.find((n) => !n.type && n.name?.endsWith('.brfnt'));
const fontBytes = homeBtn.bytes.subarray(fontNode.offset, fontNode.offset + fontNode.size);
const fontCmaps = parseBrfntCmaps(fontBytes);
const allMappedCodepoints = [...new Set(fontCmaps.flatMap((x) => x.mapped_codepoints))];
const hbmArchive = {
  physical_path: homeBtnPhysical,
  source_path: rel(homeBtnPath),
  source_size: homeBtn.bytes.length,
  source_sha256: sha256(homeBtn.bytes),
  archive_format: 'Nintendo U8',
  u8_root_offset_hex: hex(homeBtn.root_offset),
  u8_node_count: homeBtn.node_count,
  staged_in_current_655: stagedSet.has(homeBtnPhysical),
  language_specific_texture_count: homeTextures.length,
  language_specific_textures: homeTextures,
  dynamic_text_font: {
    member_path: fontNode.path,
    member_index: fontNode.index,
    archive_offset: fontNode.offset,
    archive_offset_hex: hex(fontNode.offset),
    size_bytes: fontNode.size,
    sha256: sha256(fontBytes),
    cmap_sections: fontCmaps,
    unique_mapped_codepoint_count: allMappedCodepoints.length,
    mapped_hangul_syllable_count: fontCmaps.reduce((n, x) => n + x.mapped_hangul_syllable_count, 0),
    audit_conclusion: 'No mapped Hangul syllables; Korean CSV text requires a Korean-capable rebuilt/injected BRFNT member.',
  },
  visual_evidence: statEvidence('work/runtime_fix/audit_renders/hbm/homebtn_jp_eng_contact_sheet.png'),
};

// End-roll baked dialogue WTM files.
const endrollManifest = json('work/runtime_fix/audit_renders/endroll_wtm_manifest.json');
const endrollText = [
  'やっほー!!\nラルク、起きる時間だよー!!',
  '起きろってば、おきろー!!',
  '……ん',
  'お前が目覚める時に合わせて\n我々のメッセージを残しておく',
  'お前が寂しがるといけないんでな。\n気の利いたモーニングコールだろ？',
  'ソニアの計算だと\nあなたが目覚めるのはおよそ５００年後よ',
  'お前が眠ってから大変だったぜ。\nま、アルス坊やが頑張ってくれてな',
  '今度はましな皇帝になれそうだぜ',
  '我らも全力でサポートするつもりだ',
  '私は５年たったら\n眠りについてちゃうけどね',
  '希望がある限り、人は前に向かって\n歩いて行くことが出来る',
  'あなたが目覚める約束の日まで\n私たちは必死で生き抜いてみせる',
  'みんな……',
  'だから、安心していいよ',
  'ラルクが目覚めたとき\nラルクは独りぼっちじゃないよ',
  '私たちの心を受け継いだ誰かが\n必ずラルクを迎えてくれるわ',
  '約束する。この人の世を\n５００年後のお前に託すことを',
  '――そろそろ時間だ',
  'じゃあな、ラルク。\nお前は最高の相棒だったぜ',
  'ばいば～い！　また未来でね！',
  'お姉さんのこと\n忘れちゃダ・メ・ヨ',
  'さらばだ。\nお前と共に在れたことを誇りに思う',
  '……リフィアは……\nリフィアはどうしたんだ……',
];
const endroll = endrollManifest.map((x, i) => ({
  ...x,
  staged_in_current_655: stagedSet.has(x.physical_path),
  visible_source_text_jp_visual_transcription: endrollText[i],
}));

// Runtime screenshot evidence is JPEG data despite the historical .png extension.
const runtimeScreenshotPath = 'work/runtime_validation/runtime_initial_settings_japanese_before_fix.png';
const runtimeScreenshot = {
  ...statEvidence(runtimeScreenshotPath),
  detected_media_type: 'image/jpeg',
  width: 642,
  height: 512,
  visible_japanese_examples: [
    '初期設定', '設定終了', 'コントローラ', 'ヌンチャク', '振動', '字幕', 'カーソル記憶',
    'カメラ回転', '通常', '反転', '文字速度', '遅い', '普通', '早い', '瞬間', 'ＢＧＭ音量',
    'ＳＥ音量', '音声音量', 'フリッカーレベル', '使用するコントローラを設定します',
  ],
};

const definiteGapPaths = [
  'DATA/sys/main.dol',
  ...hbmCsvFiles.map((x) => `DATA/files/${x.physical_path}`),
  `DATA/files/${homeBtnPhysical}`,
  ...endroll.map((x) => `DATA/files/${x.physical_path}`),
];

const audit = {
  schema: 'arf-runtime-ui-gap-audit-v1',
  generated_at: new Date().toISOString(),
  game_id: 'RPJJ99',
  task: 'Initial-settings Japanese residue root-cause and pipeline-boundary audit',
  audit_only_snapshot: true,
  baseline_or_game_payload_modified_by_this_audit: false,
  translation_performed_by_this_audit: false,
  translation_policy: 'Codex internal model only',
  external_translation_services_used: [],
  verdict: {
    status: 'FAIL_INCOMPLETE_LOCALIZATION_BOUNDARY',
    summary: 'The initial-settings UI is compiled into DATA/sys/main.dol, which the text catalog and 655-file runtime staging never included. Additional definite omissions exist in the Wii HOME overlay and 23 end-roll dialogue textures.',
    completion_claim_allowed: false,
  },
  runtime_evidence: {
    initial_settings_japanese: runtimeScreenshot,
    korean_strap_control: {
      ...statEvidence('work/runtime_validation/runtime_boot_korean.png'),
      detected_media_type: 'image/jpeg',
      width: 642,
      height: 512,
    },
  },
  current_pipeline_snapshot: {
    evidence_files: [
      statEvidence(probePath), statEvidence(catalogPath), statEvidence(catalogSummaryPath),
      statEvidence(stagingPath), statEvidence(reinsertionPath), statEvidence(imageExclusionsPath),
    ],
    catalog: {
      source_root: catalog.source_root,
      record_count: catalog.record_count,
      physical_source_count: catalogSummary.physical_source_count,
      surface_counts: Object.fromEntries(Object.entries(catalogSummary.statistics).filter(([k]) => k.startsWith('surface:'))),
      contains_main_dol: catalogPaths.some((p) => /main\.dol/i.test(p)),
      contains_hbm: catalogPaths.some((p) => /^Hbm\//i.test(p)),
      structural_reason_main_dol_was_dropped: 'Catalog source_root is DATA/files; main.dol resides in sibling DATA/sys.',
    },
    staging: {
      staged_physical_files: staging.counts.staged_physical_files,
      riivolution_file_rules: staging.counts.riivolution_file_rules,
      roots: stagingRoots,
      contains_main_dol: stagedPaths.some((p) => /main\.dol/i.test(p)),
      contains_hbm: stagedPaths.some((p) => /^Hbm\//i.test(p)),
      contains_endroll_wtm: stagedPaths.some((p) => /^Event\/endroll\/.*\.wtm$/i.test(p)),
    },
    image_lane: {
      modified_asset_count: reinsertion.modified_asset_count,
      replacement_target_count: reinsertion.replacement_target_count,
      contains_home_button_archive: JSON.stringify(reinsertion).includes('homeBtn.arc'),
      contains_endroll_dialogue_wtm: JSON.stringify(reinsertion).includes('EV09_18_0200C_'),
    },
  },
  root_cause: [
    'text_probe_10 found 1,885 EUC-JP candidates directly in DATA/sys/main.dol, including the exact initial-settings strings visible at runtime.',
    'text_catalog_v2 was built only from DATA/files and therefore cannot carry executable-resident strings forward.',
    'final_runtime_staging is an allowlist derived from the catalog/application/image lanes; it contains neither sys/main.dol nor Hbm nor standalone Event/endroll WTM dialogue frames.',
    'The image audit treated 48 assets but did not inventory the Wii HOME U8 archive or the ending-dialogue standalone WTM sequence.',
  ],
  coverage_delta: {
    current_staged_physical_files: staging.counts.staged_physical_files,
    definite_new_physical_files: definiteGapPaths.length,
    projected_minimum_staged_physical_files_if_all_definite_gaps_are_added_without_overlap: staging.counts.staged_physical_files + definiteGapPaths.length,
    definite_text_physical_files: 3,
    definite_image_container_or_physical_files: 24,
    additional_baked_text_image_assets: homeTextures.length + endroll.length,
    definite_gap_physical_paths: definiteGapPaths,
    projection_is_provisional: true,
    provisional_reason: 'SFD video frames and opening.bnr graphics still require a complete visual sweep; the DOL probe also has untriaged candidates beyond the confirmed minimum.',
  },
  main_dol: {
    physical_path: 'DATA/sys/main.dol',
    source_path: rel(dolPath),
    source_size: dol.length,
    source_sha256: sha256(dol),
    staged_in_current_655: false,
    probe: {
      path: probePath,
      source_encoding: probe.encoding,
      candidate_count: probe.candidate_count,
      source_sha256: probe.source_sha256.toUpperCase(),
    },
    containing_section: {
      ...dolSection,
      file_start_hex: hex(dolSection.file_start),
      file_end_exclusive_hex: hex(dolSection.file_end_exclusive),
      ram_start_hex: hex(dolSection.ram_start),
      ram_end_exclusive_hex: hex(dolSection.ram_end_exclusive),
      mapping_formula: 'RAM = 0x803C9B00 + (file_offset - 0x003C5C00)',
    },
    confirmed_runtime_user_visible_minimum_count: confirmedDol.length,
    confirmed_counts_by_lane: laneCounts,
    initial_settings_record_count: initialDol.length,
    initial_settings_records: initialDol,
    confirmed_runtime_user_visible_records: confirmedDol,
    additional_deferred_player_facing_record_count: deferredDol.length,
    additional_deferred_player_facing_ranges: deferredVisibleRanges.map((x) => ({ ...x, start_hex: hex(x.start), end_hex: hex(x.end) })),
    additional_deferred_player_facing_records: deferredDol,
    untriaged_probe_candidate_count_after_confirmed_minimum: probe.candidate_count - confirmedDol.length,
    audit_limit: 'Candidate scan contains false positives, debug strings and additional visible content. Do not equate the confirmed minimum with exhaustive main.dol coverage.',
  },
  non_main_dol_definite_gaps: {
    hbm_csv_text: hbmCsvFiles,
    hbm_baked_ui_and_font: hbmArchive,
    endroll_baked_dialogue: {
      physical_file_count: endroll.length,
      files: endroll,
      visual_evidence: statEvidence('work/runtime_fix/audit_renders/endroll_contact_sheet.png'),
    },
  },
  checked_not_definite_or_not_japanese: [
    {
      physical_path: 'DATA/files/opening.bnr',
      source_size: read('work/disc_extracted/DATA/files/opening.bnr').length,
      source_sha256: sha256(read('work/disc_extracted/DATA/files/opening.bnr')),
      imet_offset_hex: '0x40',
      u8_archive_offset_hex: '0x600',
      imet_japanese_slot_text_offset_hex: '0x5C',
      imet_japanese_slot_text: 'ARC RISE FANTASIA',
      conclusion: 'No Japanese text in the populated IMET name; not a definite Japanese-text gap. Compressed banner/icon graphics remain in the visual-sweep backlog.',
    },
    {
      physical_path: 'DATA/files/Event/endroll/fin.wtm',
      conclusion: 'Stylized Latin FIN only; not Japanese text.',
    },
    {
      physical_path: 'DATA/files/Hbm/homeBtnIcon.wtm',
      conclusion: 'Symbolic HOME icon; no text found in visual inspection.',
    },
    {
      physical_path: 'DATA/files/Sys/criware.wtm',
      conclusion: 'CRIWARE logo; no Japanese localization target.',
    },
  ],
  unresolved_visual_sweep: [
    'All Movie/*.sfd streams must be sampled at scene changes/end cards to prove that no Japanese text is burned into video frames.',
    'opening.bnr banner.bin/icon.bin compressed graphics should be rendered once; its IMET text alone is not a complete graphic proof.',
    'All remaining standalone/embedded TPL/WTM/BRRES text-bearing assets outside the 48-item image lane need contact-sheet review rather than extension-based exclusion.',
  ],
  remediation_recommendations_without_translations: [
    {
      priority: 0,
      target: 'DATA/sys/main.dol',
      action: 'Add an executable-string lane keyed to the exact source hash. Preserve printf tokens/control bytes. Verify each source byte span before patching. Where Korean codebook bytes exceed the NUL capacity, relocate rodata and patch validated pointers/callsites rather than overwriting adjacent data.',
      staging: 'Add a hash-bound /sys/main.dol replacement rule (or the loader-specific equivalent) and validate actual runtime interception; DATA/files rules cannot cover it.',
    },
    {
      priority: 0,
      target: 'DATA/files/Hbm/home.csv and home_nosave.csv',
      action: 'Translate only the Japanese first column with the Codex internal model; preserve UTF-16BE BOM, CRLF, quote/tab structure, row count and all other language columns. Re-run a TSV/CSV parse and HOME overlay runtime test.',
    },
    {
      priority: 0,
      target: 'DATA/files/Hbm/homeBtn.arc',
      action: 'Rebuild the Nintendo U8 archive with Korean replacements for the 18 same-dimension I4 text textures. Inject/rebuild the BRFNT CMAP/glyph data for every Hangul character used by the CSV prompts; the original font maps zero Hangul syllables.',
    },
    {
      priority: 1,
      target: 'DATA/files/Event/endroll/EV09_18_0200C_00.wtm .. _22.wtm',
      action: 'Translate and typeset all 23 ending-dialogue frames at the original canvas dimensions and GX/palette formats, then replace the physical WTM files and validate the complete ending playback sequence.',
    },
    {
      priority: 1,
      target: 'Inventory/staging generators',
      action: 'Expand source roots from DATA/files-only to explicit files+sys+banner/media lanes. Fail the build when a known user-visible physical path has no catalog/reinsertion decision. Recompute manifest counts from the final allowlist rather than hand-maintaining 655.',
    },
  ],
  required_runtime_acceptance: [
    'Cold boot: strap/title/controller-selection/initial-settings screen show no Japanese.',
    'Every initial-settings row/value/help line and controller-change confirmation is Korean with no overflow or missing glyphs.',
    'Press HOME in a save-enabled and no-save context: all baked buttons/headings and all CSV prompts render Korean; reconnect flow and ①/② symbols remain intact.',
    'Trigger load/save/no-space/NAND-error flows and verify all executable-resident prompts.',
    'Play the ending through all 23 dialogue frames and verify Korean text, timing, alpha/palette and clipping.',
    'Re-run static hashes/structure checks and publish the updated physical-file manifest before any completion claim.',
  ],
};

fs.writeFileSync('work/runtime_fix/runtime_ui_gap_audit.json', `${JSON.stringify(audit, null, 2)}\n`, 'utf8');
console.log(JSON.stringify({
  output: 'work/runtime_fix/runtime_ui_gap_audit.json',
  definite_gap_physical_files: definiteGapPaths.length,
  projected_minimum: audit.coverage_delta.projected_minimum_staged_physical_files_if_all_definite_gaps_are_added_without_overlap,
  confirmed_dol: confirmedDol.length,
  initial_dol: initialDol.length,
  deferred_dol: deferredDol.length,
  hbm_textures: homeTextures.length,
  endroll: endroll.length,
  hbm_font_hangul: hbmArchive.dynamic_text_font.mapped_hangul_syllable_count,
}, null, 2));
