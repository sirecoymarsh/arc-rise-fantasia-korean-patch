#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {
  compressLz10,
  decodeRtdpEntries,
  decompressLz10,
  parseRtdp,
  rebuildRtdp,
  sha256,
} = require('./container_agent/container_tool.js');

const ROOT = path.resolve(process.cwd());
const SOURCE_HEADER = path.join(ROOT, 'work/research/table_agent/btl_usual_entries/btl_enemy.vlh');
const SOURCE_VLD = path.join(ROOT, 'work/disc_extracted/DATA/files/Btl/btl_enemy.vld');
const STAGED_BTL_USUAL = path.join(ROOT, 'work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_usual.vol');
const CURRENT_BTL_USUAL = path.join(ROOT, 'work/battle_enemy_application/base_btl_usual_before_enemy.vol');
const CATALOG = path.join(ROOT, 'work/translation/battle_enemy/battle_enemy_catalog.json');
const SKILL_TRANSLATIONS = path.join(ROOT, 'work/translation/battle_enemy/battle_enemy_skill_translations.json');
const MONSTER_BOOK = path.join(ROOT, 'work/final_system_table_application/replacement_catalogs/monster_book.json');
const CODEBOOK = path.join(ROOT, 'work/font/final_v3/codebook.json');
const OUTPUT_DIR = path.join(ROOT, 'work/battle_enemy_application');
const ENTRY_DIR = path.join(OUTPUT_DIR, 'repacked_entries');
const OUTPUT_VLD = path.join(OUTPUT_DIR, 'btl_enemy.vld');
const OUTPUT_USUAL = path.join(OUTPUT_DIR, 'btl_usual.vol');
const OUTPUT_REPORT = path.join(OUTPUT_DIR, 'application_report.json');
const ALIGNMENT = 0x800;

function assert(condition, message, details) {
  if (!condition) {
    const suffix = details === undefined ? '' : `\n${JSON.stringify(details, null, 2)}`;
    throw new Error(`${message}${suffix}`);
  }
}
function hash(buffer) { return crypto.createHash('sha256').update(buffer).digest('hex').toUpperCase(); }
function fileHash(file) {
  const h = crypto.createHash('sha256');
  const fd = fs.openSync(file, 'r');
  const chunk = Buffer.alloc(1024 * 1024);
  try {
    while (true) {
      const got = fs.readSync(fd, chunk, 0, chunk.length, null);
      if (!got) break;
      h.update(chunk.subarray(0, got));
    }
  } finally { fs.closeSync(fd); }
  return h.digest('hex').toUpperCase();
}
function alignUp(value, alignment) { return Math.ceil(value / alignment) * alignment; }
function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); }
function encodeText(text, codebook) {
  const parts = [];
  const chars = codebook.characters;
  for (let index = 0; index < text.length;) {
    if (text.startsWith('<$', index)) {
      const end = text.indexOf('>', index + 2);
      assert(end === index + 4, `malformed control marker in ${JSON.stringify(text)}`);
      const value = text.slice(index + 2, end);
      assert(/^[0-9A-Fa-f]{2}$/.test(value), `bad control byte ${value}`);
      parts.push(Buffer.from([parseInt(value, 16)]));
      index = end + 1;
      continue;
    }
    const cp = text.codePointAt(index);
    const char = String.fromCodePoint(cp);
    index += char.length;
    if (chars[char]) {
      parts.push(Buffer.from(chars[char].bytes_hex, 'hex'));
    } else {
      assert(cp <= 0x7F, `character missing from codebook: ${JSON.stringify(char)} in ${JSON.stringify(text)}`);
      parts.push(Buffer.from([cp]));
    }
  }
  return Buffer.concat(parts);
}
function parseHeader(header, vldSize) {
  assert(header.subarray(0, 4).toString('ascii') === 'RVLX', 'bad RVLX magic');
  const headerSize = header.readUInt32BE(4);
  const count = header.readUInt32BE(8);
  const declared = header.readUInt32BE(12);
  assert(headerSize === header.length, 'RVLX header size mismatch');
  assert(declared === headerSize + vldSize, 'RVLX declared total mismatch', { declared, headerSize, vldSize });
  assert(0x20 + count * 8 <= headerSize, 'RVLX entry table overflow');
  const entries = [];
  for (let index = 0; index < count; index += 1) {
    const recordOffset = 0x20 + index * 8;
    const size = header.readUInt32BE(recordOffset);
    const offset = header.readUInt32BE(recordOffset + 4);
    const nextOffset = index + 1 < count ? header.readUInt32BE(recordOffset + 12) : vldSize;
    assert(offset + size <= nextOffset && nextOffset <= vldSize, `RVLX entry ${index} range invalid`);
    entries.push({ index, recordOffset, size, offset, slotSize: nextOffset - offset });
  }
  return { headerSize, count, declared, entries };
}
function fieldRaw(data, offset, capacity) {
  const slot = data.subarray(offset, offset + capacity);
  const nul = slot.indexOf(0);
  assert(nul >= 0, `unterminated source field at 0x${offset.toString(16)}`);
  return slot.subarray(0, nul);
}
function writeField(data, unit, encoded) {
  assert(encoded.length < unit.capacity, `${unit.id}: ${encoded.length} bytes does not fit capacity ${unit.capacity}`);
  const sourceRaw = fieldRaw(data, unit.offset, unit.capacity);
  assert(sourceRaw.toString('hex').toUpperCase() === unit.raw_hex, `${unit.id}: source bytes differ from catalog`);
  data.fill(0, unit.offset, unit.offset + unit.capacity);
  encoded.copy(data, unit.offset);
}
function diffOutsideAllowed(before, after, allowedRanges) {
  const mask = new Uint8Array(before.length);
  for (const [start, end] of allowedRanges) mask.fill(1, start, end);
  let changed = 0;
  let outside = 0;
  for (let i = 0; i < before.length; i += 1) {
    if (before[i] !== after[i]) {
      changed += 1;
      if (!mask[i]) outside += 1;
    }
  }
  return { changedBytes: changed, changedOutsideAllowed: outside };
}

function main() {
  for (const file of [SOURCE_HEADER, SOURCE_VLD, CATALOG, SKILL_TRANSLATIONS, MONSTER_BOOK, CODEBOOK]) {
    assert(fs.existsSync(file), `missing input ${file}`);
  }
  fs.mkdirSync(ENTRY_DIR, { recursive: true });
  const sourceHeader = fs.readFileSync(SOURCE_HEADER);
  if (!fs.existsSync(CURRENT_BTL_USUAL)) {
    assert(fs.existsSync(STAGED_BTL_USUAL), `missing input ${STAGED_BTL_USUAL}`);
    const staged = fs.readFileSync(STAGED_BTL_USUAL);
    const stagedParsed = parseRtdp(staged, STAGED_BTL_USUAL);
    const stagedPayloads = decodeRtdpEntries(staged, stagedParsed);
    const headerIndex = stagedParsed.entries.findIndex(entry => entry.name === 'btl_enemy.vlh');
    assert(headerIndex >= 0 && stagedPayloads[headerIndex].equals(sourceHeader),
      'cannot bootstrap battle base: staged btl_enemy.vlh is already modified');
    fs.writeFileSync(CURRENT_BTL_USUAL, staged);
  }
  assert(fs.existsSync(CURRENT_BTL_USUAL), `missing battle base ${CURRENT_BTL_USUAL}`);
  const sourceVldSize = fs.statSync(SOURCE_VLD).size;
  const headerInfo = parseHeader(sourceHeader, sourceVldSize);
  const catalog = readJson(CATALOG);
  assert(catalog.entry_count === headerInfo.count, 'catalog/header entry count mismatch');
  const catalogPayloads = new Map(catalog.payloads.map(row => [row.index, row]));
  const unitsByEntry = new Map();
  for (const unit of catalog.units) {
    const match = /^btl_enemy:(\d+):/.exec(unit.id);
    assert(match, `bad catalog unit id ${unit.id}`);
    const index = Number(match[1]);
    if (!unitsByEntry.has(index)) unitsByEntry.set(index, []);
    unitsByEntry.get(index).push(unit);
  }
  const skillDoc = readJson(SKILL_TRANSLATIONS);
  const skills = new Map();
  for (const row of skillDoc.translations) {
    const source = row.source_text.replaceAll('<$15>', '\x15');
    assert(!skills.has(source), `duplicate skill translation ${JSON.stringify(source)}`);
    skills.set(source, row.translation_ko);
  }
  const codebook = readJson(CODEBOOK);
  const monsterDoc = readJson(MONSTER_BOOK);
  const monsterNames = new Map();
  for (const unit of monsterDoc.units) {
    if (unit.field === 'name' && unit.record < 269) monsterNames.set(unit.record, unit);
  }
  assert(monsterNames.size === 269, 'missing monster-book name mappings');

  const sourceFd = fs.openSync(SOURCE_VLD, 'r');
  const rows = [];
  let totalUnits = 0;
  try {
    for (const entry of headerInfo.entries) {
      const slot = Buffer.alloc(entry.slotSize);
      const got = fs.readSync(sourceFd, slot, 0, slot.length, entry.offset);
      assert(got === slot.length, `short VLD read at entry ${entry.index}`);
      for (let i = entry.size; i < slot.length; i += 1) assert(slot[i] === 0, `nonzero VLD slot padding at entry ${entry.index} +0x${i.toString(16)}`);
      const packed = slot.subarray(0, entry.size);
      const payloadCatalog = catalogPayloads.get(entry.index);
      assert(payloadCatalog && payloadCatalog.packed_sha256 === hash(packed), `entry ${entry.index}: packed hash mismatch`);
      const sourceUnpacked = decompressLz10(packed, `btl_enemy[${entry.index}]`);
      assert(payloadCatalog.unpacked_sha256 === hash(sourceUnpacked), `entry ${entry.index}: unpacked hash mismatch`);
      const modified = Buffer.from(sourceUnpacked);
      const units = unitsByEntry.get(entry.index) || [];
      const allowed = [];
      let nameCount = 0;
      let partCount = 0;
      let skillCount = 0;
      for (const unit of units) {
        if (unit.field === 'display_name') {
          nameCount += 1;
          const safeUnit = { ...unit, capacity: 35 };
          assert(unit.offset === 0x180, `entry ${entry.index}: unexpected name offset`);
          assert(sourceUnpacked[unit.offset + 35] === modified[unit.offset + 35], 'pre-edit metadata mismatch');
          let encoded;
          if (entry.index < 269) {
            const mapped = monsterNames.get(entry.index);
            assert(mapped.source_text === unit.source_text, `entry ${entry.index}: monster-book source mismatch`, { enemy: unit.source_text, book: mapped.source_text });
            encoded = Buffer.from(mapped.replacement_hex, 'hex');
          } else {
            assert(unit.source_text === 'レイストーン', 'unexpected final enemy name');
            encoded = encodeText('레이 스톤', codebook);
          }
          writeField(modified, safeUnit, encoded);
          allowed.push([unit.offset, unit.offset + 35]);
          assert(modified[unit.offset + 35] === sourceUnpacked[unit.offset + 35], `entry ${entry.index}: name metadata changed`);
        } else if (unit.field === 'skill_name' || unit.field === 'part_name') {
          if (unit.field === 'skill_name') skillCount += 1;
          else partCount += 1;
          const target = skills.get(unit.source_text);
          assert(target !== undefined, `${unit.id}: missing skill translation for ${JSON.stringify(unit.source_text)}`);
          const encoded = encodeText(target, codebook);
          if (unit.source_text.charCodeAt(0) === 0x15) {
            assert(encoded[0] === 0x15 && encoded[1] === parseInt(unit.raw_hex.slice(2, 4), 16) && encoded[2] === parseInt(unit.raw_hex.slice(4, 6), 16), `${unit.id}: elemental prefix mismatch`);
          }
          writeField(modified, unit, encoded);
          allowed.push([unit.offset, unit.offset + unit.capacity]);
        }
      }
      assert(nameCount === 1, `entry ${entry.index}: expected one display name`);
      assert(partCount === payloadCatalog.part_name_count, `entry ${entry.index}: part-name count mismatch`);
      assert(skillCount === payloadCatalog.skill_count, `entry ${entry.index}: skill count mismatch`);
      totalUnits += nameCount + partCount + skillCount;
      const confinement = diffOutsideAllowed(sourceUnpacked, modified, allowed);
      assert(confinement.changedOutsideAllowed === 0, `entry ${entry.index}: bytes changed outside text fields`);
      const repacked = compressLz10(modified, { alignment: 4 });
      const verified = decompressLz10(repacked, `btl_enemy[${entry.index}] rebuilt`);
      assert(verified.equals(modified), `entry ${entry.index}: recompression roundtrip mismatch`);
      const entryPath = path.join(ENTRY_DIR, `entry_${String(entry.index).padStart(3, '0')}.lz10`);
      fs.writeFileSync(entryPath, repacked);
      rows.push({
        index: entry.index,
        display_name_source: units.find(u => u.field === 'display_name').source_text,
        part_name_count: partCount,
        skill_count: skillCount,
        source_offset: entry.offset,
        source_packed_size: entry.size,
        source_slot_size: entry.slotSize,
        output_packed_size: repacked.length,
        fits_source_slot: repacked.length <= entry.slotSize,
        source_packed_sha256: hash(packed),
        output_packed_sha256: hash(repacked),
        source_unpacked_sha256: hash(sourceUnpacked),
        output_unpacked_sha256: hash(modified),
        ...confinement,
        entry_path: path.relative(ROOT, entryPath).replaceAll('\\', '/'),
      });
      if (entry.index % 10 === 0) process.stdout.write(`${entry.index}/${headerInfo.count} ${rows.at(-1).display_name_source} skills=${skillCount} packed=${repacked.length}\n`);
    }
  } finally { fs.closeSync(sourceFd); }
  assert(totalUnits === catalog.unit_count, `applied unit count ${totalUnits} != catalog ${catalog.unit_count}`);

  const preserveOffsets = rows.every(row => row.fits_source_slot);
  const newHeader = Buffer.from(sourceHeader);
  let outputVldSize;
  if (preserveOffsets) {
    outputVldSize = sourceVldSize;
    for (const row of rows) {
      row.output_offset = row.source_offset;
      newHeader.writeUInt32BE(row.output_packed_size, 0x20 + row.index * 8);
    }
  } else {
    let cursor = 0;
    for (const row of rows) {
      row.output_offset = cursor;
      newHeader.writeUInt32BE(row.output_packed_size, 0x20 + row.index * 8);
      newHeader.writeUInt32BE(cursor, 0x24 + row.index * 8);
      cursor = alignUp(cursor + row.output_packed_size, ALIGNMENT);
    }
    outputVldSize = cursor;
    newHeader.writeUInt32BE(newHeader.length + outputVldSize, 0x0C);
  }
  const outFd = fs.openSync(OUTPUT_VLD, 'w+');
  try {
    fs.ftruncateSync(outFd, outputVldSize);
    for (const row of rows) {
      const packed = fs.readFileSync(path.join(ROOT, row.entry_path));
      const wrote = fs.writeSync(outFd, packed, 0, packed.length, row.output_offset);
      assert(wrote === packed.length, `short VLD write at entry ${row.index}`);
    }
  } finally { fs.closeSync(outFd); }
  const rereadFd = fs.openSync(OUTPUT_VLD, 'r');
  try {
    for (const row of rows) {
      const packed = Buffer.alloc(row.output_packed_size);
      assert(fs.readSync(rereadFd, packed, 0, packed.length, row.output_offset) === packed.length, `short final VLD read ${row.index}`);
      assert(hash(packed) === row.output_packed_sha256, `final VLD entry hash mismatch ${row.index}`);
    }
  } finally { fs.closeSync(rereadFd); }

  fs.rmSync(ENTRY_DIR, { recursive: true, force: true });
  for (const row of rows) delete row.entry_path;

  const currentUsual = fs.readFileSync(CURRENT_BTL_USUAL);
  const parsedUsual = parseRtdp(currentUsual, CURRENT_BTL_USUAL);
  const usualPayloads = decodeRtdpEntries(currentUsual, parsedUsual);
  const enemyHeaderIndex = parsedUsual.entries.findIndex(entry => entry.name === 'btl_enemy.vlh');
  assert(enemyHeaderIndex >= 0, 'btl_enemy.vlh not found in btl_usual.vol');
  assert(usualPayloads[enemyHeaderIndex].equals(sourceHeader), 'current btl_usual enemy header differs from pristine source');
  usualPayloads[enemyHeaderIndex] = newHeader;
  const usualResult = rebuildRtdp(currentUsual, usualPayloads, { sourceLabel: CURRENT_BTL_USUAL });
  fs.writeFileSync(OUTPUT_USUAL, usualResult.buffer);
  const usualAgain = decodeRtdpEntries(usualResult.buffer, parseRtdp(usualResult.buffer, OUTPUT_USUAL));
  assert(usualAgain[enemyHeaderIndex].equals(newHeader), 'rebuilt btl_usual header extraction mismatch');

  const report = {
    schema: 'arf-btl-enemy-application-v1',
    game_id: 'RPJJ99',
    translation_engine_policy: 'Codex internal model only',
    external_translation_models_or_apis_used: false,
    source: {
      header: path.relative(ROOT, SOURCE_HEADER).replaceAll('\\', '/'),
      header_sha256: hash(sourceHeader),
      vld: path.relative(ROOT, SOURCE_VLD).replaceAll('\\', '/'),
      vld_size: sourceVldSize,
      vld_sha256: fileHash(SOURCE_VLD),
      current_btl_usual_sha256: hash(currentUsual),
    },
    output: {
      header_sha256: hash(newHeader),
      vld: path.relative(ROOT, OUTPUT_VLD).replaceAll('\\', '/'),
      vld_size: outputVldSize,
      vld_sha256: fileHash(OUTPUT_VLD),
      btl_usual: path.relative(ROOT, OUTPUT_USUAL).replaceAll('\\', '/'),
      btl_usual_size: usualResult.buffer.length,
      btl_usual_sha256: hash(usualResult.buffer),
    },
    counts: {
      entries: rows.length,
      display_names: catalog.display_name_count,
      part_names: catalog.part_name_count,
      skill_names: catalog.skill_name_count,
      total_units: totalUnits,
      entries_fitting_source_slots: rows.filter(row => row.fits_source_slot).length,
      changed_outside_allowed_bytes: rows.reduce((sum, row) => sum + row.changedOutsideAllowed, 0),
    },
    layout_policy: preserveOffsets ? 'preserve-original-0x800-slots' : 'canonical-0x800-repack',
    repacked_entry_temp_files_cleaned: true,
    btl_usual_rebuild: usualResult.report,
    entries: rows,
    valid: true,
    error_count: 0,
    errors: [],
  };
  fs.writeFileSync(OUTPUT_REPORT, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({ output: report.output, counts: report.counts, layout_policy: report.layout_policy, valid: true }, null, 2)}\n`);
}

try { main(); } catch (error) { process.stderr.write(`${error.stack || error}\n`); process.exitCode = 1; }
