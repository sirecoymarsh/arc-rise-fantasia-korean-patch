#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {
  parseRtdp,
  decodeRtdpEntries,
  rebuildRtdp,
  decompressLz10,
  rebuildCxdPayload,
  sha256,
} = require('./container_agent/container_tool');

function assert(condition, message, details) {
  if (!condition) throw new Error(message + (details === undefined ? '' : '\n' + JSON.stringify(details, null, 2)));
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
}

function readTranslations(file) {
  const lines = fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '').trimEnd().split(/\r?\n/);
  assert(lines.shift() === 'map_code\ttranslation_ko_escaped', 'unexpected TSV header');
  const out = new Map();
  for (const line of lines) {
    const tab = line.indexOf('\t');
    assert(tab > 0, 'invalid TSV row', line);
    const code = line.slice(0, tab);
    const text = line.slice(tab + 1).replaceAll('\\n', '\n');
    assert(!out.has(code), 'duplicate map code ' + code);
    assert(text.split('\n').length === 9, code + ': expected exactly 9 display lines');
    out.set(code, text);
  }
  return out;
}

function encodeText(text, codebook) {
  const out = [];
  for (const char of text) {
    const rec = codebook.characters[char];
    if (rec) {
      out.push(...Buffer.from(rec.bytes_hex, 'hex'));
    } else {
      const cp = char.codePointAt(0);
      assert(cp <= 0x7f, 'character missing from codebook: ' + JSON.stringify(char));
      out.push(cp);
    }
  }
  return Buffer.from(out);
}

function hashFile(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex').toUpperCase();
}

function main() {
  const rootIndex = process.argv.indexOf('--root');
  const root = path.resolve(rootIndex >= 0 ? process.argv[rootIndex + 1] : process.cwd());
  const outputDir = path.join(root, 'work/map_info_application');
  const sourceDir = path.join(root, 'work/disc_extracted/DATA/files/interface');
  const catalogPath = path.join(root, 'work/translation/map_info_description_catalog.json');
  const translationsPath = path.join(root, 'work/translation/map_info/map_info_description_translations.tsv');
  const codebookPath = path.join(root, 'work/font/final_v3/codebook.json');
  const catalog = readJson(catalogPath);
  const translations = readTranslations(translationsPath);
  const codebook = readJson(codebookPath);
  assert(translations.size === 36, 'expected 36 map translations');
  const byFile = new Map();
  for (const row of catalog.rows) {
    if (!byFile.has(row.file)) byFile.set(row.file, []);
    byFile.get(row.file).push(row);
  }
  assert(byFile.size === 36, 'expected 36 map CXD files');
  fs.mkdirSync(path.join(outputDir, 'files/interface'), { recursive: true });

  const reports = [];
  for (const [fileName, rows] of [...byFile].sort()) {
    const match = /^data_map_([a-z0-9]+)_vol\.cxd$/.exec(fileName);
    assert(match, 'unexpected map file ' + fileName);
    const code = match[1];
    const translation = translations.get(code);
    assert(translation !== undefined, 'missing translation for ' + code);
    assert(rows.length === 2, code + ': expected .dat and .txt members');

    const sourcePath = path.join(sourceDir, fileName);
    const sourcePacked = fs.readFileSync(sourcePath);
    const sourceUnpacked = decompressLz10(sourcePacked, sourcePath);
    const parsed = parseRtdp(sourceUnpacked, sourcePath + '::lz10');
    const payloads = decodeRtdpEntries(sourceUnpacked, parsed);
    const approved = Buffer.alloc(sourceUnpacked.length);
    const memberReports = [];

    for (const row of rows) {
      const entry = parsed.entries[row.index];
      assert(entry && entry.name === row.member, code + ': catalog/member mismatch', { row, entry });
      const sourcePayload = payloads[row.index];
      assert(sourcePayload.length === row.size, code + ': member size mismatch');
      assert(sourcePayload.subarray(0, Buffer.from(row.raw_hex, 'hex').length).equals(Buffer.from(row.raw_hex, 'hex')), code + ': source raw mismatch');
      const eol = row.member.endsWith('.txt') ? '\r\n' : '\n';
      const targetRaw = encodeText(translation.split('\n').join(eol) + eol, codebook);
      assert(targetRaw.length < sourcePayload.length || (row.member.endsWith('.txt') && targetRaw.length <= sourcePayload.length), code + '/' + row.member + ': target does not fit', { targetBytes: targetRaw.length, capacity: sourcePayload.length });
      const replacement = Buffer.alloc(sourcePayload.length);
      targetRaw.copy(replacement);
      payloads[row.index] = replacement;
      approved.fill(1, entry.absoluteOffset, entry.endOffset);
      memberReports.push({
        member: row.member,
        entry_index: row.index,
        capacity: sourcePayload.length,
        source_used_bytes: row.used_bytes,
        target_used_bytes: targetRaw.length,
        headroom_bytes: sourcePayload.length - targetRaw.length,
        line_count: 9,
        source_sha256: sha256(sourcePayload).toUpperCase(),
        target_sha256: sha256(replacement).toUpperCase(),
      });
    }

    const rebuiltRtdp = rebuildRtdp(sourceUnpacked, payloads, { sourceLabel: sourcePath + '::lz10' });
    const newUnpacked = rebuiltRtdp.buffer;
    assert(newUnpacked.length === sourceUnpacked.length, code + ': unpacked RTDP size changed');
    let outside = 0;
    for (let i = 0; i < newUnpacked.length; i += 1) if (newUnpacked[i] !== sourceUnpacked[i] && !approved[i]) outside += 1;
    assert(outside === 0, code + ': bytes changed outside description members: ' + outside);

    const wrapped = rebuildCxdPayload(sourcePacked, newUnpacked, {
      sourceLabel: sourcePath,
      expectedUnpackedSha256: sha256(sourceUnpacked),
    });
    let outputPacked = wrapped.buffer;
    let paddedToSourceSize = false;
    if (outputPacked.length <= sourcePacked.length) {
      const padded = Buffer.alloc(sourcePacked.length);
      outputPacked.copy(padded);
      outputPacked = padded;
      paddedToSourceSize = true;
    }
    assert(decompressLz10(outputPacked, fileName + ' verify').equals(newUnpacked), code + ': final CXD decode mismatch');
    const outputPath = path.join(outputDir, 'files/interface', fileName);
    fs.writeFileSync(outputPath, outputPacked);
    reports.push({
      map_code: code,
      source_path: sourcePath,
      output_path: outputPath,
      source_packed_size: sourcePacked.length,
      output_packed_size: outputPacked.length,
      physical_size_preserved: outputPacked.length === sourcePacked.length,
      compressed_stream_padded_to_source_size: paddedToSourceSize,
      source_packed_sha256: hashFile(sourcePath),
      output_packed_sha256: hashFile(outputPath),
      source_unpacked_sha256: sha256(sourceUnpacked).toUpperCase(),
      output_unpacked_sha256: sha256(newUnpacked).toUpperCase(),
      changed_outside_description_members: outside,
      rtdp_policy: rebuiltRtdp.report.policy,
      members: memberReports,
    });
  }

  const report = {
    schema: 'arf-map-info-description-application-v1',
    game_id: 'RPJJ99',
    translator_model: 'Codex internal',
    inputs: {
      catalog_path: catalogPath,
      catalog_sha256: hashFile(catalogPath),
      translations_path: translationsPath,
      translations_sha256: hashFile(translationsPath),
      codebook_path: codebookPath,
      codebook_sha256: hashFile(codebookPath),
    },
    counts: {
      map_files: reports.length,
      description_members: reports.reduce((n, r) => n + r.members.length, 0),
      display_descriptions: translations.size,
      size_preserved_files: reports.filter(r => r.physical_size_preserved).length,
      resized_files: reports.filter(r => !r.physical_size_preserved).length,
      changed_outside_description_members: reports.reduce((n, r) => n + r.changed_outside_description_members, 0),
    },
    invariants: {
      all_36_descriptions_translated: reports.length === 36,
      dat_and_txt_both_translated: reports.every(r => r.members.length === 2),
      all_targets_fit_member_capacities: true,
      all_members_fixed_size: true,
      all_unpacked_bytes_outside_description_members_source_identical: true,
      all_outputs_decompress_to_requested_rtdp: true,
    },
    files: reports,
    valid: true,
  };
  fs.writeFileSync(path.join(outputDir, 'application_report.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  process.stdout.write(JSON.stringify({ outputDir, ...report.counts, valid: true }, null, 2) + '\n');
}

main();
