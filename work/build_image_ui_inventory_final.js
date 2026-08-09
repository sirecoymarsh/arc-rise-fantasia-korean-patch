const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const DISC = path.join(ROOT, 'work', 'disc_extracted', 'DATA', 'files');
const ENTRIES_CSV = path.join(ROOT, 'work', 'research', 'rtdp_agent', 'audit', 'entries.csv');
const OUT_JSON = path.join(ROOT, 'work', 'image_ui_inventory_final.json');
const OUT_MD = path.join(ROOT, 'work', 'image_ui_plan_final.md');

const GX_FORMAT_NAMES = {
  0x00: 'I4', 0x01: 'I8', 0x02: 'IA4', 0x03: 'IA8', 0x04: 'RGB565',
  0x05: 'RGB5A3', 0x06: 'RGBA32', 0x08: 'C4', 0x09: 'C8',
  0x0a: 'C14X2', 0x0e: 'CMPR',
};
const PALETTE_NAMES = {0: 'none', 1: 'RGB565', 2: 'RGB5A3', 3: 'IA8'};

function posix(p) { return p.replace(/\\/g, '/'); }
function relDisc(p) { return posix(path.relative(DISC, p)); }
function discPath(rel) { return `work/disc_extracted/DATA/files/${posix(rel)}`; }
function listFiles(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, {withFileTypes: true})) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...listFiles(p));
    else if (e.isFile()) out.push(p);
  }
  return out;
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
  const head = rows.shift();
  return rows.filter(r => r.length > 1).map(r => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ''])));
}

function wtmdMeta(buf) {
  if (!buf || buf.length < 16 || buf.subarray(0, 4).toString('ascii') !== 'WTMD') return null;
  const gx = buf[12], pal = buf[13];
  return {
    magic: 'WTMD', width: buf.readUInt16BE(8), height: buf.readUInt16BE(10),
    dimensions: `${buf.readUInt16BE(8)}x${buf.readUInt16BE(10)}`,
    gx_format_code: `0x${gx.toString(16).padStart(2, '0').toUpperCase()}`,
    gx_format_name: GX_FORMAT_NAMES[gx] || 'unknown',
    palette_format_code: `0x${pal.toString(16).padStart(2, '0').toUpperCase()}`,
    palette_format_name: PALETTE_NAMES[pal] || 'unknown',
  };
}

function lz10Prefix(buf, want = 32) {
  if (buf.length < 5 || buf[0] !== 0x10) return null;
  const declared = buf[1] | (buf[2] << 8) | (buf[3] << 16);
  const out = [];
  let ip = 4;
  while (ip < buf.length && out.length < Math.min(want, declared)) {
    const flags = buf[ip++];
    for (let bit = 7; bit >= 0 && ip < buf.length && out.length < Math.min(want, declared); bit--) {
      if ((flags & (1 << bit)) === 0) out.push(buf[ip++]);
      else {
        if (ip + 1 >= buf.length) break;
        const a = buf[ip++], b = buf[ip++];
        const len = (a >> 4) + 3;
        const disp = ((a & 0x0f) << 8) | b;
        const src = out.length - disp - 1;
        if (src < 0) return {declared_size: declared, prefix: Buffer.from(out), malformed_prefix: true};
        for (let j = 0; j < len && out.length < Math.min(want, declared); j++) out.push(out[src + j]);
      }
    }
  }
  return {declared_size: declared, prefix: Buffer.from(out), malformed_prefix: false};
}

function classificationForCxd(rel) {
  const n = path.posix.basename(posix(rel));
  const lower = posix(rel).toLowerCase();
  if (/^interface\/tex_loc_title_/.test(lower)) return ['location_title_card', 'P0', 'likely', true, 'replace_baked_text'];
  if (/^interface\/tex_casino_intro_/.test(lower)) return ['casino_instruction_card', 'P0', 'likely', true, 'replace_baked_text'];
  if (/^interface\/if_casino_/.test(lower)) return ['casino_ui_sheet', 'P0', 'likely', true, 'inspect_then_replace_text_regions'];
  if (/^interface\/if_(poker|slot|resident)_/.test(lower)) return ['minigame_ui_sheet', 'P0', 'likely', true, 'inspect_then_replace_text_regions'];
  if (/^interface\/data_map_/.test(lower)) return ['map_ui_texture', 'P1', 'unknown', true, 'inspect_for_baked_labels'];
  if (/^interface\/tex_indoor_/.test(lower)) return ['environment_texture_signage_pass', 'P2', 'unknown', false, 'inspect_for_japanese_signage'];
  if (/^interface\/tex_(stand|ubody|face|mface|vface|weapon)/.test(lower)) return ['character_or_equipment_art', 'P3', 'no', false, 'exclude_unless_visual_pass_finds_text'];
  if (/^minigame\//.test(lower)) return ['minigame_texture_container', 'P1', 'unknown', true, 'inspect_for_baked_labels'];
  if (/^(char)\//.test(lower)) return ['character_texture', 'P3', 'no', false, 'exclude_unless_visual_pass_finds_text'];
  if (/^(event|map|world)\//.test(lower)) {
    if (/(title|logo|moji|message|banner|sign|board|poster|notice|tutorial)/i.test(n)) return ['scene_text_texture', 'P1', 'likely', true, 'inspect_then_replace_text_regions'];
    return ['scene_or_map_texture', 'P2', 'unknown', false, 'inspect_for_japanese_signage'];
  }
  return ['opaque_cxd_texture_candidate', 'P2', 'unknown', false, 'inspect_before_scope_decision'];
}

function nestedClass(physical, name, chain) {
  const p = posix(physical).toLowerCase(), n = name.toLowerCase(), c = chain.toLowerCase();
  if (/^euc28-[0-8]\.wtm$/.test(n)) return ['font_glyph_atlas', 'P0', 'yes', true, 'rebuild_korean_glyph_atlas_preserving_wtmd_layout'];
  if (/font/.test(n)) return ['font_or_numeric_atlas', 'P1', 'unknown', true, 'inspect_glyph_coverage_then_rebuild_if_needed'];
  if (/title_logo/.test(n)) return ['title_logo', 'P0', 'no', true, 'optional_korean_logo_typesetting'];
  if (/title_(pressanybutton|newgame|continue)/.test(n)) return ['title_menu_label', 'P0', 'no', true, 'replace_baked_english_with_korean'];
  if (p === 'btl/btl_gameover.vol') return ['game_over_composite', 'P1', 'no', true, 'replace_only_if_full_korean_ui_scope_requires'];
  if (/^sys\/system\.vol$/.test(p) && n === 'nowloading.wtm') return ['loading_label', 'P0', 'no', true, 'replace_baked_english_with_korean'];
  if (/^sys\/system\.vol$/.test(p) && /(button_icon|mapicon|itemicon|element|secret|map_pt|heart|glare|shadow)/.test(n)) return ['shared_icon_or_effect', 'P3', 'no', false, 'retain_unless_visual_pass_finds_text'];
  if (/^interface\/msgfrm\.vol$/.test(p)) return ['dialogue_frame_or_face', 'P3', 'no', false, 'retain_frame_geometry'];
  const likelyJp = /(moji|renkei|syugeki|tekisyu|hyousyou|selectcopin|comand|tactics|charaselect|targetinfo)/.test(n);
  const uiText = /(moji|title|logo|press|newgame|continue|result|win|lose|gameover|dealer|player|card_(stand|hit|doubledown)|odds|rank|stamina_overheat|wiiremocon|critical|guest|ready|dead|help|next|getitems|getexp|getskil|levelup|targetinfo|button|comand|command|tactics|turn_|general_|ap_|hp_|tp_|rp_|lv_|stock|open)/.test(n);
  if (p.startsWith('btl/') && uiText) return ['battle_baked_ui_label', 'P0', likelyJp ? 'likely' : 'unknown', true, 'replace_text_region_preserving_atlas_coordinates'];
  if (p.startsWith('minigame/') && uiText) return ['minigame_baked_ui_label', 'P0', likelyJp ? 'likely' : 'unknown', true, 'replace_text_region_preserving_atlas_coordinates'];
  if (p.startsWith('map/')) return ['map_ui_or_environment_texture', 'P1', 'unknown', false, 'inspect_for_baked_labels_or_signage'];
  if (p.startsWith('event/') && uiText) return ['event_baked_text_texture', 'P1', likelyJp ? 'likely' : 'unknown', true, 'inspect_then_replace_text_regions'];
  if (p.startsWith('event/')) return ['event_effect_or_scene_texture', 'P3', 'no', false, 'exclude_unless_visual_pass_finds_text'];
  if (p.startsWith('char/')) return ['character_texture', 'P3', 'no', false, 'exclude_unless_visual_pass_finds_text'];
  if (uiText) return ['baked_ui_label', 'P1', likelyJp ? 'likely' : 'unknown', true, 'inspect_then_replace_text_regions'];
  return ['icon_effect_or_background_texture', 'P3', 'no', false, 'retain_unless_visual_pass_finds_text'];
}

function directWtmClass(rel) {
  const l = posix(rel).toLowerCase(), n = path.posix.basename(l);
  if (/^sys\/strap[ab]_jp\.wtm$/.test(l)) return ['wii_safety_screen', 'P0', 'yes', true, 'typeset_korean_safety_text_on_preserved_canvas'];
  if (/^event\/endroll\/.+\.wtm$/.test(l)) return ['ending_roll_raster_piece', 'P1', 'unknown', true, 'inspect_for_credit_text_then_typeset'];
  if (n === 'criware.wtm') return ['middleware_logo', 'P3', 'no', false, 'retain'];
  if (n === 'homebtnicon.wtm') return ['home_button_icon', 'P3', 'no', false, 'retain'];
  if (l.startsWith('_sasaki/')) return ['developer_or_viewer_fixture', 'P3', 'no', false, 'exclude_from_release_scope'];
  return ['standalone_texture', 'P2', 'unknown', false, 'inspect_before_scope_decision'];
}

function methodFor(role, action) {
  if (action.includes('retain') || action.includes('exclude')) return 'No edit planned; retain byte-identically unless the later visual pass overturns the classification.';
  if (role === 'font_glyph_atlas' || role === 'font_or_numeric_atlas') return 'Edit glyph cells only; preserve canvas, palette, GX format, offsets, and atlas lookup contract; replace the same RTDP member.';
  return 'Decode non-destructively, clean only the text region, typeset Korean at the original scale, preserve alpha/palette/GX format/canvas and atlas coordinates, then replace the same leaf and rebuild the same container.';
}

const allFiles = listFiles(DISC);
const assets = [];
let id = 1;
function add(rec) { assets.push({id: `IMG-${String(id++).padStart(5, '0')}`, status: 'planned_not_modified', ...rec}); }

for (const file of allFiles.filter(f => f.toLowerCase().endsWith('.cxd')).sort()) {
  const rel = relDisc(file), buf = fs.readFileSync(file), lz = lz10Prefix(buf);
  const meta = lz ? wtmdMeta(lz.prefix) : wtmdMeta(buf);
  const innerMagic = lz && lz.prefix.length >= 4 ? lz.prefix.subarray(0, 4).toString('ascii') : buf.subarray(0, 4).toString('ascii');
  const [role, priority, japanese, target, action] = classificationForCxd(rel);
  add({record_type: 'physical_cxd', physical_path: discPath(rel), asset_path: discPath(rel), role, priority,
    japanese_text: japanese, koreanization_target: target, evidence: ['filename_semantics', 'physical_file_catalog', 'binary_prefix_metadata_only'],
    storage: {outer_format: 'CXD', compression: lz ? 'Nintendo LZ10' : 'not_detected', compressed_bytes: buf.length,
      declared_uncompressed_bytes: lz?.declared_size ?? null, inner_magic: innerMagic, wtmd: meta},
    localization_action: action, localization_method: methodFor(role, action), reinsertion_target: discPath(rel),
    notes: ['No raster decode or visual confirmation was performed in this inventory pass.']});
}

for (const file of allFiles.filter(f => f.toLowerCase().endsWith('.wtm')).sort()) {
  const rel = relDisc(file), buf = fs.readFileSync(file), meta = wtmdMeta(buf);
  const [role, priority, japanese, target, action] = directWtmClass(rel);
  add({record_type: 'physical_wtm', physical_path: discPath(rel), asset_path: discPath(rel), role, priority,
    japanese_text: japanese, koreanization_target: target, evidence: ['filename_semantics', 'WTMD_header_metadata'],
    storage: {outer_format: 'WTMD', file_bytes: buf.length, wtmd: meta}, localization_action: action,
    localization_method: methodFor(role, action), reinsertion_target: discPath(rel),
    notes: ['Dimensions and GX metadata come from the WTMD header; pixels were not rendered.']});
}

for (const file of allFiles.filter(f => f.toLowerCase().endsWith('.tpl')).sort()) {
  const rel = relDisc(file), st = fs.statSync(file);
  add({record_type: 'physical_tpl', physical_path: discPath(rel), asset_path: discPath(rel), role: 'developer_or_viewer_tpl',
    priority: 'P3', japanese_text: 'no', koreanization_target: false, evidence: ['_sasaki_path', 'physical_file_catalog'],
    storage: {outer_format: 'TPL', file_bytes: st.size, dimensions: null}, localization_action: 'exclude_from_release_scope',
    localization_method: 'No edit planned.', reinsertion_target: discPath(rel), notes: ['Pixel dimensions deferred; no TPL decode was run.']});
}

const rows = parseCsv(fs.readFileSync(ENTRIES_CSV, 'utf8'));
for (const r of rows.filter(r => r.decoded_magic === 'WTMD')) {
  const physical = posix(r.physical_archive), name = r.name, chain = posix(r.archive_identity);
  const prefix = Buffer.from(r.decoded_prefix_hex || '', 'hex');
  const meta = wtmdMeta(prefix);
  const [role, priority, japanese, target, action] = nestedClass(physical, name, chain);
  const selector = `${chain}::${String(r.entry_index).padStart(4, '0')}:${name}`;
  add({record_type: 'nested_wtm', physical_path: discPath(physical), asset_path: `${discPath(physical)}::${selector}`,
    archive_identity: chain, entry_index: Number(r.entry_index), member_name: name, role, priority,
    japanese_text: japanese, koreanization_target: target, evidence: ['RTDP_inventory_member_name', 'decoded_WTMD_prefix_metadata', 'filename_semantics'],
    storage: {outer_format: 'RTDP/VOL chain', member_format: 'WTMD', member_bytes: Number(r.size), wtmd: meta},
    localization_action: action, localization_method: methodFor(role, action),
    reinsertion_target: `${discPath(physical)} :: ${chain} :: entry ${r.entry_index} (${name})`,
    notes: ['Nested dimensions are read from the catalogued decoded prefix; pixels were not rendered.']});
}

for (const r of rows.filter(r => r.decoded_magic === 'TPL')) {
  const physical = posix(r.physical_archive), chain = posix(r.archive_identity), name = r.name;
  add({record_type: 'nested_tpl', physical_path: discPath(physical), asset_path: `${discPath(physical)}::${chain}::${r.entry_index}:${name}`,
    archive_identity: chain, entry_index: Number(r.entry_index), member_name: name, role: 'title_effect_texture', priority: 'P2',
    japanese_text: 'unknown', koreanization_target: false, evidence: ['RTDP_inventory_member_name', 'decoded_TPL_magic'],
    storage: {outer_format: 'RTDP/VOL', member_format: 'TPL', member_bytes: Number(r.size), dimensions: null},
    localization_action: 'inspect_if_title_effect_contains_text', localization_method: 'If text is found, preserve TPL GX format, palette, mip levels, dimensions, and member size contract when replacing the same member.',
    reinsertion_target: `${discPath(physical)} :: entry ${r.entry_index} (${name})`, notes: ['No TPL raster decode was run.']});
}

const systemBanner = path.join(DISC, 'Sys', 'system.vol');
add({record_type: 'nested_wibn', physical_path: discPath('Sys/system.vol'), asset_path: `${discPath('Sys/system.vol')}::0047:banner.bin`,
  archive_identity: 'Sys/system.vol', entry_index: 47, member_name: 'banner.bin', role: 'wii_save_banner', priority: 'P0',
  japanese_text: 'likely', koreanization_target: true, evidence: ['system_vol_inventory_entry', 'confirmed_WIBN_magic', 'banner_member_name'],
  storage: {outer_format: 'RTDP/VOL', member_format: 'WIBN', member_bytes: 56992, dimensions: 'multi-image container; deferred'},
  localization_action: 'inspect_banner_and_icon_frames_then_replace_text_regions',
  localization_method: 'Edit only banner/icon image planes that contain text; preserve WIBN header, frame count, pixel format, metadata, and the RTDP member contract.',
  reinsertion_target: `${discPath('Sys/system.vol')} :: entry 47 (banner.bin)`, notes: ['WIBN magic was observed; no frame decode was run.']});

const opening = path.join(DISC, 'opening.bnr');
if (fs.existsSync(opening)) add({record_type: 'physical_bnr', physical_path: discPath('opening.bnr'), asset_path: discPath('opening.bnr'),
  role: 'wii_channel_banner_package', priority: 'P0', japanese_text: 'likely', koreanization_target: true,
  evidence: ['confirmed_IMET_at_0x40', 'confirmed_IMD5_at_0x680', 'embedded_banner.bin_icon.bin_sound.bin_names'],
  storage: {outer_format: 'Wii banner package', file_bytes: fs.statSync(opening).size, magic_offsets: {IMET: '0x40', IMD5: '0x680'}, dimensions: 'multi-resource container; deferred'},
  localization_action: 'inspect_channel_banner_and_icon_then_replace_text_regions',
  localization_method: 'Unpack the banner package, edit only text-bearing image/layout resources, preserve animation/audio/layout resources, rebuild IMET/IMD5 metadata, and replace opening.bnr.',
  reinsertion_target: discPath('opening.bnr'), notes: ['Signatures were located without unpacking or rendering the banner.']});

for (const file of allFiles.filter(f => f.toLowerCase().endsWith('.sfd')).sort()) {
  const rel = relDisc(file), st = fs.statSync(file);
  const titleLike = /(^|\/)(ie_logo|mmv|ray_op|ray_ed)/i.test(posix(rel));
  add({record_type: 'physical_sfd', physical_path: discPath(rel), asset_path: discPath(rel), role: titleLike ? 'logo_opening_or_ending_movie' : 'event_movie',
    priority: titleLike ? 'P1' : 'P2', japanese_text: 'unknown', koreanization_target: false,
    evidence: ['movie_file_catalog', 'filename_semantics'], storage: {outer_format: 'CRI SFD movie', file_bytes: st.size, dimensions: null},
    localization_action: 'inspect_for_baked_japanese_subtitles_or_credits',
    localization_method: 'Only if baked text is confirmed: create a Korean overlay or re-encode with the original frame size/rate and audio mux contract, then replace the same SFD.',
    reinsertion_target: discPath(rel), notes: ['No movie decode, frame sampling, or playback was performed.']});
}

for (const file of allFiles.filter(f => /Hbm[\\/]homeBtn(?:_[A-Z]{3})?\.arc$/i.test(f)).sort()) {
  const rel = relDisc(file), jp = /Hbm\/homeBtn\.arc$/i.test(posix(rel));
  add({record_type: 'physical_arc', physical_path: discPath(rel), asset_path: discPath(rel), role: 'wii_home_button_overlay',
    priority: jp ? 'P1' : 'P3', japanese_text: jp ? 'likely' : 'no', koreanization_target: jp,
    evidence: ['Hbm_locale_filename', 'physical_file_catalog'], storage: {outer_format: 'Wii ARC', file_bytes: fs.statSync(file).size, dimensions: 'multi-resource container; deferred'},
    localization_action: jp ? 'inspect_japanese_home_menu_overlay_resources' : 'retain_non_japanese_locale_fallback',
    localization_method: jp ? 'Unpack ARC, edit only Japanese text-bearing textures/layout strings, preserve BRLYT/BRLAN/resource names, and rebuild the same ARC.' : 'No edit planned.',
    reinsertion_target: discPath(rel), notes: ['No ARC unpack or render was run.']});
}

const tutorial = path.join(DISC, 'Btl', 'btl_tutorial.vld');
if (fs.existsSync(tutorial)) add({record_type: 'opaque_ui_candidate', physical_path: discPath('Btl/btl_tutorial.vld'), asset_path: discPath('Btl/btl_tutorial.vld'),
  role: 'battle_tutorial_container', priority: 'P1', japanese_text: 'unknown', koreanization_target: false,
  evidence: ['tutorial_filename', 'physical_file_catalog'], storage: {outer_format: 'VLD', file_bytes: fs.statSync(tutorial).size, dimensions: null},
  localization_action: 'inspect_structure_for_image_members_after_text_table_work',
  localization_method: 'If raster members are discovered, inventory them before editing and preserve VLD offsets/alignment during reinsertion.',
  reinsertion_target: discPath('Btl/btl_tutorial.vld'), notes: ['No VLD extraction was run in this pass.']});

const countBy = key => Object.fromEntries([...assets.reduce((m, a) => m.set(a[key], (m.get(a[key]) || 0) + 1), new Map())].sort());
const groups = [
  {id: 'G-LOC-TITLE', pattern: 'interface/tex_loc_title_*_wtm.cxd', members: assets.filter(a => a.record_type === 'physical_cxd' && /interface\/tex_loc_title_/.test(a.physical_path)).map(a => a.physical_path)},
  {id: 'G-CASINO-INTRO', pattern: 'interface/tex_casino_intro_*_wtm.cxd', members: assets.filter(a => a.record_type === 'physical_cxd' && /interface\/tex_casino_intro_/.test(a.physical_path)).map(a => a.physical_path)},
  {id: 'G-DATA-MAP', pattern: 'interface/data_map_*_vol.cxd', members: assets.filter(a => a.record_type === 'physical_cxd' && /interface\/data_map_/.test(a.physical_path)).map(a => a.physical_path)},
  {id: 'G-INDOOR', pattern: 'interface/tex_indoor_*_wtm.cxd', members: assets.filter(a => a.record_type === 'physical_cxd' && /interface\/tex_indoor_/.test(a.physical_path)).map(a => a.physical_path)},
  {id: 'G-PORTRAIT-BODY-WEAPON', pattern: 'interface/tex_{stand,ubody,face,mface,vface,weapon}*', members: assets.filter(a => a.record_type === 'physical_cxd' && /interface\/tex_(stand|ubody|face|mface|vface|weapon)/.test(a.physical_path)).map(a => a.physical_path)},
  {id: 'G-ENDROLL-PHYSICAL-WTM', pattern: 'Event/endroll/*.wtm', members: assets.filter(a => a.record_type === 'physical_wtm' && /Event\/endroll\//.test(a.physical_path)).map(a => a.physical_path)},
];

const inventory = {
  schema: 'arf-image-ui-inventory-v1', generated_date: '2026-08-04',
  scope: 'Discovery-only inventory of image-based UI, logos, title/menu labels, texture banners, rasterized credits/signage candidates, and their reinsertion containers.',
  source_roots: ['work/disc_extracted/DATA/files', 'work/catalog/disc_inventory.json', 'work/discovery/system_vol_inventory.json', 'work/research/rtdp_agent/audit/entries.csv', 'work/pristine'],
  policy: {discovery_only: true, image_modification_executed: false, reinsertion_executed: false, visual_validation_executed: false, external_web_or_model_used: false,
    japanese_text_status_meaning: {yes: 'filename/container evidence is direct enough to treat Japanese raster text as present', likely: 'strong semantic evidence; visual confirmation deferred', unknown: 'must be visually inspected later', no: 'semantics indicate non-Japanese or non-text art; visual pass may overturn'}},
  format_notes: {
    WTMD: 'Header-confirmed proprietary texture wrapper. Width/height are big-endian at 0x08/0x0A; GX/palette codes at 0x0C/0x0D.',
    CXD: 'Most sampled files are Nintendo LZ10 wrappers; inventory records the declared uncompressed size and inner prefix magic without writing decompressed files.',
    RTDP_VOL: 'Nested members are addressed by physical archive, archive_identity chain, entry index, and member name from the existing audit catalog.',
    TPL: 'Nintendo texture container. Pixel metadata was intentionally deferred because no TPL decode was run.',
    Wii_banner: 'opening.bnr contains IMET/IMD5 and banner.bin/icon.bin/sound.bin resource names; Sys/system.vol::banner.bin begins with WIBN.',
    SFD: 'CRI movie container; frame inspection and baked-subtitle detection are deferred.'
  },
  summary: {total_records: assets.length, by_record_type: countBy('record_type'), by_priority: countBy('priority'), by_japanese_text: countBy('japanese_text'), koreanization_targets: assets.filter(a => a.koreanization_target).length,
    grouped_series: Object.fromEntries(groups.map(g => [g.id, g.members.length]))},
  groups, assets,
  deferred_questions: [
    'Which likely/unknown records actually contain Japanese or English baked text at 100% scale?',
    'Which CXD assets are single WTMD leaves versus compressed RTDP/layout containers requiring nested replacement?',
    'Do event/endroll WTMs contain rasterized credit text or only decorative/portrait fragments?',
    'Do SFD movies contain baked Japanese subtitles/credits, or are all subtitles rendered from translated script data?',
    'Which data_map and tex_indoor textures contain place labels or diegetic signage?',
    'Does the Japanese Home Button ARC need Korean raster/layout work, or can a system-provided localized overlay be reused?'
  ]
};

fs.writeFileSync(OUT_JSON, JSON.stringify(inventory, null, 2) + '\n', 'utf8');

const loc = groups.find(g => g.id === 'G-LOC-TITLE').members.length;
const casino = groups.find(g => g.id === 'G-CASINO-INTRO').members.length;
const maps = groups.find(g => g.id === 'G-DATA-MAP').members.length;
const indoor = groups.find(g => g.id === 'G-INDOOR').members.length;
const excludedArt = groups.find(g => g.id === 'G-PORTRAIT-BODY-WEAPON').members.length;
const md = `# Arc Rise Fantasia 이미지 기반 UI 한국어화 계획 (발견 전용)\n\n` +
`## 이번 패스의 경계\n\n- 실행한 것: 추출 파일과 기존 카탈로그를 이용한 경로/컨테이너/헤더 메타데이터 인벤토리.\n- 실행하지 않은 것: 이미지 디코드·추출, 픽셀 수정, 재삽입, 게임 실행, 시각 검증, 최종 검증.\n- 외부 웹·번역 모델·API 사용: 없음. 번역 문안은 이후 Codex 내부 모델로만 작성한다.\n- 일본어 포함 여부가 \`likely\`/\`unknown\`인 항목은 파일명·컨테이너 의미에 따른 분류이며 픽셀 판독 결과가 아니다.\n\n` +
`## 인벤토리 요약\n\n- 총 레코드: **${assets.length}**\n- 실제 한국어화 후보 플래그: **${inventory.summary.koreanization_targets}**\n- 우선순위: ${Object.entries(inventory.summary.by_priority).map(([k,v]) => `\`${k}\` ${v}`).join(', ')}\n- 형식: ${Object.entries(inventory.summary.by_record_type).map(([k,v]) => `\`${k}\` ${v}`).join(', ')}\n- 일본어 상태: ${Object.entries(inventory.summary.by_japanese_text).map(([k,v]) => `\`${k}\` ${v}`).join(', ')}\n- 주요 연속군: 장소 타이틀 ${loc}, 카지노 소개 ${casino}, 지도 UI ${maps}, 실내/간판 후보 ${indoor}, 인물·장비 계열 조건부 제외 ${excludedArt}.\n\n` +
`상세 레코드는 \`work/image_ui_inventory_final.json\`의 \`assets\`에 있으며, 각 항목마다 물리 경로, 내부 멤버 체인, 바이트 크기, 가능한 WTMD 크기/GX 형식, 일본어 상태, 한국어화 방식, 재삽입 대상을 기록했다.\n\n` +
`## 우선순위 실행안\n\n` +
`### P0 — 반드시 먼저 다룰 표면\n\n1. **Wii 채널/세이브 배너**\n   - \`opening.bnr\`: IMET/IMD5 및 \`banner.bin\`/\`icon.bin\`/\`sound.bin\` 리소스명이 확인된 채널 배너 패키지.\n   - \`Sys/system.vol::0047:banner.bin\`: \`WIBN\` 매직이 확인된 세이브 배너.\n2. **부팅 경고 화면**\n   - \`Sys/strapA_jp.wtm\`, \`Sys/strapB_jp.wtm\`: 파일명상 일본어 경고 화면이며 두 파일 모두 WTMD 640x448.\n3. **타이틀 로고와 메뉴 라벨**\n   - \`Title/title.vol\` 및 중복 배치된 \`Sys/title.vol\` 안의 \`title_logo.wtm\`, \`title_pressanybutton.wtm\`, \`title_newgame01/02.wtm\`, \`title_continue01/02.wtm\`.\n4. **장소명 타이틀 카드**\n   - \`interface/tex_loc_title_*_wtm.cxd\` ${loc}개. 같은 캔버스와 GX 텍스처 형식을 유지하면서 한국어 장소명으로 교체한다.\n5. **카지노/미니게임 안내 및 배틀 UI 아틀라스**\n   - 카지노 소개 ${casino}개, \`if_casino_*\`, \`if_poker_vol.cxd\`, \`if_slot_vol.cxd\`, \`if_resident_vol.cxd\`.\n   - \`Btl/btl_usual.vol\`의 \`*_moji.wtm\`, 결과/명령/연계/레벨업 계열.\n   - \`minigame/mg_blackjack.vol\`, \`minigame/mg_copin.vol\`의 타이틀·결과·선택·확률·조작 라벨.\n6. **공용 로딩/글꼴 자산**\n   - \`Sys/system.vol::nowloading.wtm\`과 \`EUC28-0..8.wtm\`. 글꼴은 일반 UI 이미지와 분리해 글리프 좌표 계약을 보존한다.\n\n` +
`### P1 — 게임 진행 중 반복 노출 표면\n\n- \`interface/data_map_*_vol.cxd\` ${maps}개: 지도명/범례가 비트맵인지 확인 후 텍스트 영역만 교체.\n- \`Btl/btl_gameover.vol\`: GAME OVER 합성용 WTMD 멤버 12개. 전체 UI 한국어화 범위에 포함할지 결정.\n- \`Event/endroll/*.wtm\`: ${groups.find(g => g.id === 'G-ENDROLL-PHYSICAL-WTM').members.length}개. 크레딧 글자 조각인지 장식인지 후속 시각 판독.\n- 일본어 \`Hbm/homeBtn.arc\`: 시스템 제공 로컬라이즈 가능 여부를 먼저 확인하고 필요할 때만 수정.\n- 오프닝/엔딩/로고 SFD: 프레임에 구운 일본어 자막·크레딧이 실제로 있을 때만 영상 작업 대상으로 승격.\n\n` +
`### P2/P3 — 조건부 시각 탐색 및 제외군\n\n- \`interface/tex_indoor_*\` ${indoor}개와 Event/Map/world CXD는 간판·포스터·표지판을 찾는 환경 텍스처 패스 대상으로 둔다.\n- \`tex_stand_*\`, \`tex_ubody_*\`, 얼굴·무기 텍스처 ${excludedArt}개는 파일명상 비문자 미술 자산이므로 기본 제외하되, 후속 콘택트시트에서 문자가 발견될 때만 승격한다.\n- \`_sasaki\` TPL/WTM은 개발·뷰어용으로 판단하여 배포 범위에서 제외한다.\n\n` +
`## 형식별 작업 방식\n\n` +
`### WTMD\n- 헤더의 캔버스 크기, GX 형식, 팔레트 형식, 이미지/팔레트 오프셋을 그대로 유지한다.\n- C4/C8 등 팔레트 텍스처는 기존 팔레트 한도와 알파를 보존하고, 필요한 경우 동일 포맷 안에서 색을 재배치한다.\n- 아틀라스는 셀 좌표와 UV 계약을 변경하지 않는다.\n\n` +
`### CXD (LZ10 래퍼)\n- 먼저 무변경 디코드/재압축 경로를 확정한 뒤 텍스트가 있는 WTMD 또는 내부 RTDP 멤버만 교체한다.\n- 파일명, 내부 매직, 선언 압축 해제 크기, 정렬을 기록해 원래 CXD 위치로 되돌린다.\n\n` +
`### RTDP/VOL\n- \`physical_archive + archive_identity + entry_index + member_name\`을 재삽입 키로 사용한다.\n- 중복 파일명(예: \`e.wtm\`, \`reserved_file\`)이 있으므로 이름만으로 교체하지 않는다.\n- 기존 아카이브 정렬/간격과 예외적 템플릿을 보존한다.\n\n` +
`### TPL / BRRES / ARC\n- GX 텍스처 형식, 팔레트, 밉맵, BRLYT/BRLAN 리소스명과 애니메이션 참조를 보존한다.\n- 타이틀의 \`title_flear.tpl\`은 글자 포함 여부가 확인될 때만 수정한다.\n\n` +
`### BNR/WIBN\n- 배너·아이콘 이미지, 애니메이션, 사운드와 메타데이터를 분리해 취급한다.\n- 이미지 텍스트만 수정하고 IMET/IMD5 또는 WIBN 구조와 프레임 계약을 유지한다.\n\n` +
`### SFD\n- 구운 일본어가 확인될 때만 원본 해상도/프레임률/오디오 멀티플렉싱을 고정한 한국어 오버레이 또는 재인코딩을 검토한다.\n\n` +
`## 후속 실행 순서 (현재는 미실행)\n\n1. P0 후보를 무손상 디코드해 원본 100% 크기 콘택트시트를 만든다.\n2. 각 이미지에 \`Japanese=yes/no\`, 번역 문자열, 글꼴, 정렬, 안전영역, 재삽입 키를 확정한다.\n3. Codex 내부 모델로만 짧은 UI 문안을 번역하고 고유명사 표기와 일치시킨다.\n4. 원본 캔버스에서 배경 복원 후 한국어 조판본을 만든다.\n5. 형식별 동일 컨테이너에 재삽입하고 변경 허용 목록을 고정한다.\n6. 모든 이미지 수정이 끝난 마지막 단계에서만 정적/시각/런타임 검증을 한 번에 수행한다.\n\n` +
`## 마지막 검증에서 확인할 항목 (지금은 실행하지 않음)\n\n- 변경 대상 외 파일 해시 불변, 각 컨테이너의 엔트리 순서/정렬/오프셋 계약.\n- WTMD/TPL의 크기·GX 형식·팔레트·알파·아틀라스 셀 좌표.\n- 100% 크기에서 일본어 잔존, 잘림, 번짐, 배경 복원 흔적, 대비 부족.\n- 실제 게임의 부팅 경고, 채널/세이브 배너, 타이틀, 장소 입장, 카지노, 배틀 결과, 로딩, 엔딩 크레딧.\n- SFD/ARC/BNR을 수정한 경우 애니메이션·오디오·레이아웃 참조 정상 여부.\n\n` +
`## 현재 결론\n\n이 문서는 발견·계획 산출물이다. 이미지 수정·삽입·검증은 한 건도 실행하지 않았으며, 다음 단계는 JSON의 P0 후보부터 시각 판독하는 것이다.\n`;

fs.writeFileSync(OUT_MD, md, 'utf8');
console.log(JSON.stringify(inventory.summary, null, 2));

