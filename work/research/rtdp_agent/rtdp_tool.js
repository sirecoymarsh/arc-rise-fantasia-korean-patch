#!/usr/bin/env node
'use strict';

/*
 * Arc Rise Fantasia (Wii) RTDP archive research tool.
 *
 * Evidence baseline:
 *   work/tools/DolphinTextureExtraction-tool/lib/AuroraLip/Archives/Formats/RTDP.cs
 *
 * The AuroraLip reader establishes the on-disc structure used here:
 *   0x00  "RTDP"
 *   0x04  u32be end-of-header / data base
 *   0x08  u32be entry count
 *   0x0c  u32be archive size
 *   0x20  count records of { char name[32], u32be size, u32be rel_offset }
 *   data  every stored payload byte XOR 0x55
 *
 * This script is deliberately conservative.  It can inventory archives,
 * extract decoded payloads, and rebuild a fixed-layout archive.  Repacking
 * rejects size changes; it is a byte-exact no-op proof, not yet a resizing
 * production writer.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const XOR_KEY = 0x55;
const RECORD_SIZE = 40;
const TABLE_OFFSET = 0x20;

function die(message) {
  process.stderr.write(`ERROR: ${message}\n`);
  process.exitCode = 1;
}

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function xor55(buffer) {
  const out = Buffer.allocUnsafe(buffer.length);
  for (let i = 0; i < buffer.length; i += 1) out[i] = buffer[i] ^ XOR_KEY;
  return out;
}

function alignUp(value, alignment) {
  return Math.ceil(value / alignment) * alignment;
}

function readName(raw) {
  const zero = raw.indexOf(0);
  const used = raw.subarray(0, zero === -1 ? raw.length : zero);
  return used.toString('latin1');
}

function printableAscii(buffer) {
  if (!buffer.length) return false;
  for (const byte of buffer) {
    if (byte < 0x20 || byte > 0x7e) return false;
  }
  return true;
}

function magicLabel(buffer) {
  if (!buffer.length) return 'empty';
  const signatures = [
    ['RTDP', Buffer.from('RTDP')],
    ['BRRES', Buffer.from('bres')],
    ['BSCR', Buffer.from('bscr')],
    ['SWDB', Buffer.from('swdb')],
    ['SEDB', Buffer.from('sedb')],
    ['Yaz0', Buffer.from('Yaz0')],
    ['RARC', Buffer.from('RARC')],
    ['RIFF', Buffer.from('RIFF')],
    ['OggS', Buffer.from('OggS')],
    ['PNG', Buffer.from([0x89, 0x50, 0x4e, 0x47])],
    ['TPL', Buffer.from([0x00, 0x20, 0xaf, 0x30])],
    ['U8', Buffer.from([0x55, 0xaa, 0x38, 0x2d])],
    ['WTMD', Buffer.from('WTMD')],
    ['BTEF', Buffer.from('BTEF')],
    ['BTEM', Buffer.from('BTEM')],
    ['RVLX', Buffer.from('RVLX')],
    ['SFXB', Buffer.from('sfxb')],
    ['SSCR', Buffer.from('SSCR')],
    ['SCMP', Buffer.from('SCMP')],
    ['WIBN', Buffer.from('WIBN')],
    ['TREA', Buffer.from('trea')],
  ];
  for (const [label, signature] of signatures) {
    if (buffer.length >= signature.length && buffer.subarray(0, signature.length).equals(signature)) return label;
  }
  const first4 = buffer.subarray(0, Math.min(4, buffer.length));
  if (first4.length === 4 && printableAscii(first4)) return `ASCII:${first4.toString('ascii')}`;
  return `HEX:${first4.toString('hex')}`;
}

function parseRtdp(buffer, sourceLabel) {
  if (buffer.length < TABLE_OFFSET) throw new Error(`${sourceLabel}: shorter than 0x20-byte RTDP header`);
  if (buffer.subarray(0, 4).toString('ascii') !== 'RTDP') throw new Error(`${sourceLabel}: missing RTDP magic`);

  const eoh = buffer.readUInt32BE(0x04);
  const entryCount = buffer.readUInt32BE(0x08);
  const sizeField = buffer.readUInt32BE(0x0c);
  const tableEnd = TABLE_OFFSET + entryCount * RECORD_SIZE;
  if (tableEnd > buffer.length) throw new Error(`${sourceLabel}: entry table extends beyond archive`);
  if (eoh < tableEnd || eoh > buffer.length) {
    throw new Error(`${sourceLabel}: invalid end-of-header 0x${eoh.toString(16)} (table end 0x${tableEnd.toString(16)})`);
  }

  const entries = [];
  for (let index = 0; index < entryCount; index += 1) {
    const recordOffset = TABLE_OFFSET + index * RECORD_SIZE;
    const nameRaw = Buffer.from(buffer.subarray(recordOffset, recordOffset + 32));
    const size = buffer.readUInt32BE(recordOffset + 32);
    const relativeOffset = buffer.readUInt32BE(recordOffset + 36);
    const absoluteOffset = eoh + relativeOffset;
    const endOffset = absoluteOffset + size;
    if (endOffset > buffer.length) {
      throw new Error(`${sourceLabel}: entry ${index} (${readName(nameRaw)}) ends at 0x${endOffset.toString(16)}, beyond 0x${buffer.length.toString(16)}`);
    }
    entries.push({
      index,
      recordOffset,
      nameRaw,
      name: readName(nameRaw),
      size,
      relativeOffset,
      absoluteOffset,
      endOffset,
    });
  }

  return {
    sourceLabel,
    eoh,
    entryCount,
    sizeField,
    tableEnd,
    headerUnknownHex: buffer.subarray(0x10, 0x20).toString('hex'),
    headerPaddingHex: buffer.subarray(tableEnd, eoh).toString('hex'),
    fileSize: buffer.length,
    entries,
  };
}

function isSjisLead(byte) {
  return (byte >= 0x81 && byte <= 0x9f) || (byte >= 0xe0 && byte <= 0xfc);
}

function isSjisTrail(byte) {
  return (byte >= 0x40 && byte <= 0x7e) || (byte >= 0x80 && byte <= 0xfc);
}

function nextEncodedUnit(buffer, offset, encoding) {
  const byte = buffer[offset];
  if (byte >= 0x20 && byte <= 0x7e) return 1;
  if (byte === 0x09 || byte === 0x0a || byte === 0x0d) return 1;

  if (encoding === 'shift_jis') {
    if (byte >= 0xa1 && byte <= 0xdf) return 1;
    if (isSjisLead(byte) && offset + 1 < buffer.length && isSjisTrail(buffer[offset + 1]) && buffer[offset + 1] !== 0x7f) return 2;
    return 0;
  }

  if (encoding === 'euc-jp') {
    if (byte === 0x8e && offset + 1 < buffer.length && buffer[offset + 1] >= 0xa1 && buffer[offset + 1] <= 0xdf) return 2;
    if (byte === 0x8f && offset + 2 < buffer.length && buffer[offset + 1] >= 0xa1 && buffer[offset + 1] <= 0xfe && buffer[offset + 2] >= 0xa1 && buffer[offset + 2] <= 0xfe) return 3;
    if (byte >= 0xa1 && byte <= 0xfe && offset + 1 < buffer.length && buffer[offset + 1] >= 0xa1 && buffer[offset + 1] <= 0xfe) return 2;
    return 0;
  }

  return 0;
}

function textStats(text) {
  const japanese = text.match(/[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/gu) || [];
  const hiragana = text.match(/[\u3040-\u309f]/gu) || [];
  const halfwidth = text.match(/[\uff61-\uff9f]/gu) || [];
  const replacement = text.match(/\ufffd/gu) || [];
  return {
    japanese: japanese.length,
    hiragana: hiragana.length,
    halfwidth: halfwidth.length,
    replacement: replacement.length,
  };
}

function extractEncodedStrings(buffer, encoding, options = {}) {
  const minJapanese = options.minJapanese ?? 2;
  const minChars = options.minChars ?? 3;
  const sampleLimit = options.sampleLimit ?? 12;
  const decoder = new TextDecoder(encoding, { fatal: true });
  const samples = [];
  let stringCount = 0;
  let japaneseChars = 0;
  let hiraganaChars = 0;
  let halfwidthChars = 0;
  let nulTerminatedCount = 0;

  let cursor = 0;
  while (cursor < buffer.length) {
    let unit = nextEncodedUnit(buffer, cursor, encoding);
    if (!unit) {
      cursor += 1;
      continue;
    }
    const start = cursor;
    while (cursor < buffer.length && (unit = nextEncodedUnit(buffer, cursor, encoding)) > 0) cursor += unit;
    const end = cursor;
    if (end - start < minChars) continue;
    try {
      const text = decoder.decode(buffer.subarray(start, end));
      const stats = textStats(text);
      if (stats.japanese < minJapanese || stats.replacement) continue;
      // Correct EUC-JP dialogue is rich in full-width kana.  The same bytes
      // misread as Shift-JIS tend to become a wall of half-width kana.
      const quality = stats.japanese + stats.hiragana * 2 - stats.halfwidth * 2;
      if (quality < minJapanese) continue;
      stringCount += 1;
      japaneseChars += stats.japanese;
      hiraganaChars += stats.hiragana;
      halfwidthChars += stats.halfwidth;
      if (end < buffer.length && buffer[end] === 0) nulTerminatedCount += 1;
      if (samples.length < sampleLimit) {
        samples.push({
          offset: start,
          byteLength: end - start,
          text: text.replace(/[\r\n\t]+/g, ' ').slice(0, 240),
          japaneseChars: stats.japanese,
          hiraganaChars: stats.hiragana,
          halfwidthChars: stats.halfwidth,
          terminatedByNul: end < buffer.length && buffer[end] === 0,
        });
      }
    } catch {
      // The unit scanner is strict enough that this is unusual, but a bad
      // decoder sequence is simply not a candidate string.
    }
  }

  return { encoding, stringCount, japaneseChars, hiraganaChars, halfwidthChars, nulTerminatedCount, samples };
}

function detectJapaneseText(buffer) {
  const euc = extractEncodedStrings(buffer, 'euc-jp');
  const sjis = extractEncodedStrings(buffer, 'shift_jis');
  const eucScore = euc.japaneseChars + euc.hiraganaChars * 2 - euc.halfwidthChars * 2;
  const sjisScore = sjis.japaneseChars + sjis.hiraganaChars * 2 - sjis.halfwidthChars * 2;
  const best = eucScore >= sjisScore ? euc : sjis;
  const confidence = best.stringCount >= 3 && best.hiraganaChars >= 3 ? 'high'
    : best.stringCount >= 1 && best.hiraganaChars >= 1 ? 'medium'
      : best.stringCount >= 1 ? 'low' : 'none';
  return {
    verdict: best.stringCount ? best.encoding : null,
    confidence,
    eucJp: euc,
    shiftJis: sjis,
  };
}

function extOf(name) {
  const extension = path.extname(name).toLowerCase();
  return extension || '(none)';
}

function shouldTextScan(name, magic, size) {
  if (!size) return false;
  const extension = extOf(name);
  const assetMagics = new Set(['BRRES', 'WTMD', 'BTEF', 'SWDB', 'SEDB', 'RTDP', 'TPL']);
  if (assetMagics.has(magic)) return false;
  const likely = new Set([
    '.bin', '.bscr', '.bmg', '.dat', '.evt', '.ini', '.lst', '.msg', '.scr',
    '.scn', '.tbl', '.text', '.txt', '.csv', '.xml', '.json', '.vld',
  ]);
  if (likely.has(extension)) return true;
  if (magic === 'BSCR') return true;
  return false;
}

function isKnownMagic(label) {
  return new Set([
    'RTDP', 'BRRES', 'BSCR', 'SWDB', 'SEDB', 'Yaz0', 'RARC', 'RIFF', 'OggS',
    'PNG', 'TPL', 'U8', 'WTMD', 'BTEF', 'BTEM', 'RVLX', 'SFXB', 'SSCR',
    'SCMP', 'WIBN', 'TREA',
  ]).has(label);
}

function walkFiles(root, predicate) {
  const out = [];
  const stack = [root];
  while (stack.length) {
    const current = stack.pop();
    const children = fs.readdirSync(current, { withFileTypes: true })
      .sort((a, b) => a.name.localeCompare(b.name, 'en'));
    for (let i = children.length - 1; i >= 0; i -= 1) {
      const child = children[i];
      const full = path.join(current, child.name);
      if (child.isDirectory()) stack.push(full);
      else if (child.isFile() && predicate(full)) out.push(full);
    }
  }
  return out.sort((a, b) => a.localeCompare(b, 'en'));
}

function csvEscape(value) {
  if (value === null || value === undefined) return '';
  const string = typeof value === 'object' ? JSON.stringify(value) : String(value);
  return /[",\r\n]/.test(string) ? `"${string.replace(/"/g, '""')}"` : string;
}

function writeCsv(filePath, rows, columns) {
  const lines = [columns.join(',')];
  for (const row of rows) lines.push(columns.map((column) => csvEscape(row[column])).join(','));
  fs.writeFileSync(filePath, `${lines.join('\n')}\n`, 'utf8');
}

function safeLeaf(name) {
  const leaf = path.basename(name.replace(/\\/g, '/')) || 'unnamed';
  const cleaned = leaf.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').replace(/[. ]+$/g, '') || 'unnamed';
  return cleaned.slice(0, 120);
}

function complementRanges(fileSize, covered) {
  const merged = [];
  for (const item of covered.filter((range) => range.end > range.start).sort((a, b) => a.start - b.start || a.end - b.end)) {
    const start = Math.max(0, Math.min(fileSize, item.start));
    const end = Math.max(start, Math.min(fileSize, item.end));
    const last = merged[merged.length - 1];
    if (last && start <= last.end) last.end = Math.max(last.end, end);
    else merged.push({ start, end });
  }
  const gaps = [];
  let cursor = 0;
  for (const range of merged) {
    if (cursor < range.start) gaps.push({ start: cursor, end: range.start });
    cursor = Math.max(cursor, range.end);
  }
  if (cursor < fileSize) gaps.push({ start: cursor, end: fileSize });
  return gaps;
}

function extractArchive(archivePath, outputDirectory) {
  const original = fs.readFileSync(archivePath);
  const parsed = parseRtdp(original, archivePath);
  fs.mkdirSync(outputDirectory, { recursive: true });
  const payloadDirectory = path.join(outputDirectory, 'payloads');
  fs.mkdirSync(payloadDirectory, { recursive: true });

  const manifestEntries = [];
  for (const entry of parsed.entries) {
    const stored = original.subarray(entry.absoluteOffset, entry.endOffset);
    const decoded = xor55(stored);
    const fileName = `${String(entry.index).padStart(4, '0')}__${safeLeaf(entry.name)}`;
    fs.writeFileSync(path.join(payloadDirectory, fileName), decoded);
    manifestEntries.push({
      index: entry.index,
      name: entry.name,
      nameRawHex: entry.nameRaw.toString('hex'),
      recordOffset: entry.recordOffset,
      size: entry.size,
      relativeOffset: entry.relativeOffset,
      absoluteOffset: entry.absoluteOffset,
      endOffset: entry.endOffset,
      payloadFile: `payloads/${fileName}`,
      storedSha256: sha256(stored),
      decodedSha256: sha256(decoded),
      decodedMagic: magicLabel(decoded),
    });
  }

  const opaqueRanges = complementRanges(
    original.length,
    parsed.entries.map((entry) => ({ start: entry.absoluteOffset, end: entry.endOffset })),
  );
  const opaqueParts = [];
  let opaqueOffset = 0;
  const opaqueManifest = [];
  for (const range of opaqueRanges) {
    const bytes = original.subarray(range.start, range.end);
    opaqueParts.push(bytes);
    opaqueManifest.push({
      archiveOffset: range.start,
      length: bytes.length,
      opaqueOffset,
      sha256: sha256(bytes),
    });
    opaqueOffset += bytes.length;
  }
  const opaque = Buffer.concat(opaqueParts);
  fs.writeFileSync(path.join(outputDirectory, 'opaque.bin'), opaque);

  const manifest = {
    format: 'RTDP-fixed-layout-extraction-v1',
    sourceArchive: path.resolve(archivePath),
    sourceArchiveSha256: sha256(original),
    sourceArchiveSize: original.length,
    xorKey: '0x55',
    eoh: parsed.eoh,
    entryCount: parsed.entryCount,
    sizeField: parsed.sizeField,
    headerUnknownHex: parsed.headerUnknownHex,
    entries: manifestEntries,
    opaqueFile: 'opaque.bin',
    opaqueSha256: sha256(opaque),
    opaqueRanges: opaqueManifest,
    repackConstraint: 'Every decoded payload must retain its original byte length. Offsets/order/header/opaque bytes are preserved exactly.',
  };
  fs.writeFileSync(path.join(outputDirectory, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  return manifest;
}

function repackArchive(extractionDirectory, outputPath) {
  const manifestPath = path.join(extractionDirectory, 'manifest.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  if (manifest.format !== 'RTDP-fixed-layout-extraction-v1') throw new Error(`Unsupported manifest format: ${manifest.format}`);
  if (manifest.xorKey !== '0x55') throw new Error(`Unsupported XOR key: ${manifest.xorKey}`);

  const opaque = fs.readFileSync(path.join(extractionDirectory, manifest.opaqueFile));
  if (sha256(opaque) !== manifest.opaqueSha256) throw new Error('opaque.bin SHA-256 mismatch');
  const rebuilt = Buffer.alloc(manifest.sourceArchiveSize, 0);
  for (const range of manifest.opaqueRanges) {
    const bytes = opaque.subarray(range.opaqueOffset, range.opaqueOffset + range.length);
    if (bytes.length !== range.length || sha256(bytes) !== range.sha256) throw new Error(`Opaque range at 0x${range.archiveOffset.toString(16)} is corrupt`);
    bytes.copy(rebuilt, range.archiveOffset);
  }

  for (const entry of manifest.entries) {
    const decodedPath = path.join(extractionDirectory, ...entry.payloadFile.split('/'));
    const decoded = fs.readFileSync(decodedPath);
    if (decoded.length !== entry.size) {
      throw new Error(`Entry ${entry.index} ${entry.name}: size changed ${entry.size} -> ${decoded.length}; fixed-layout repack refuses resizing`);
    }
    xor55(decoded).copy(rebuilt, entry.absoluteOffset);
  }

  const parsed = parseRtdp(rebuilt, `${outputPath} (rebuilt)`);
  if (parsed.entryCount !== manifest.entryCount || parsed.eoh !== manifest.eoh || parsed.sizeField !== manifest.sizeField) {
    throw new Error('Rebuilt header no longer matches manifest');
  }
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, rebuilt);
  return {
    outputPath: path.resolve(outputPath),
    size: rebuilt.length,
    sha256: sha256(rebuilt),
    expectedSha256: manifest.sourceArchiveSha256,
    byteExact: sha256(rebuilt) === manifest.sourceArchiveSha256,
  };
}

function summarizeCounter(map) {
  return [...map.entries()]
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count || a.key.localeCompare(b.key, 'en'));
}

function increment(map, key, amount = 1) {
  map.set(key, (map.get(key) || 0) + amount);
}

function auditRoot(root, outputDirectory) {
  const rootAbsolute = path.resolve(root);
  const physical = walkFiles(rootAbsolute, (file) => file.toLowerCase().endsWith('.vol'));
  fs.mkdirSync(outputDirectory, { recursive: true });

  const archiveRows = [];
  const entryRows = [];
  const textCandidates = [];
  const scriptPayloads = [];
  const localizationPayloads = [];
  const errors = [];
  const extensionCounts = new Map();
  const decodedMagicCounts = new Map();
  const storedMagicCounts = new Map();
  const headerUnknownCounts = new Map();
  const eohDeltaCounts = new Map();
  const alignmentCounts = new Map();
  let nestedArchiveCount = 0;
  let xorDecodedKnownMagic = 0;
  let rawKnownMagic = 0;
  let nonAsciiEntryNameCount = 0;
  let unterminatedEntryNameCount = 0;

  function auditArchiveBuffer(buffer, context, depth) {
    const parsed = parseRtdp(buffer, context.archiveIdentity);
    const minimumEoh20 = alignUp(parsed.tableEnd, 0x20);
    const nonEmpty = parsed.entries.filter((entry) => entry.size > 0);
    const offsetsNondecreasing = nonEmpty.every((entry, index) => index === 0 || entry.relativeOffset >= nonEmpty[index - 1].relativeOffset);
    const sortedByOffset = [...nonEmpty].sort((a, b) => a.absoluteOffset - b.absoluteOffset || a.endOffset - b.endOffset);
    const overlaps = [];
    for (let i = 1; i < sortedByOffset.length; i += 1) {
      if (sortedByOffset[i].absoluteOffset < sortedByOffset[i - 1].endOffset) {
        overlaps.push([sortedByOffset[i - 1].index, sortedByOffset[i].index]);
      }
    }
    const duplicateNames = parsed.entries.length - new Set(parsed.entries.map((entry) => entry.name)).size;
    const standardLinks = [];
    for (let i = 1; i < sortedByOffset.length; i += 1) {
      standardLinks.push(sortedByOffset[i].absoluteOffset === alignUp(sortedByOffset[i - 1].endOffset, 0x20));
    }
    const expectedStandardEnd = sortedByOffset.length
      ? alignUp(sortedByOffset[sortedByOffset.length - 1].endOffset, 0x20)
      : parsed.eoh;
    const paddingRanges = [];
    if (parsed.tableEnd < parsed.eoh) paddingRanges.push([parsed.tableEnd, parsed.eoh]);
    if (sortedByOffset.length) {
      if (parsed.eoh < sortedByOffset[0].absoluteOffset) paddingRanges.push([parsed.eoh, sortedByOffset[0].absoluteOffset]);
      for (let i = 1; i < sortedByOffset.length; i += 1) {
        if (sortedByOffset[i - 1].endOffset < sortedByOffset[i].absoluteOffset) {
          paddingRanges.push([sortedByOffset[i - 1].endOffset, sortedByOffset[i].absoluteOffset]);
        }
      }
      if (sortedByOffset[sortedByOffset.length - 1].endOffset < parsed.fileSize) {
        paddingRanges.push([sortedByOffset[sortedByOffset.length - 1].endOffset, parsed.fileSize]);
      }
    } else if (parsed.eoh < parsed.fileSize) {
      paddingRanges.push([parsed.eoh, parsed.fileSize]);
    }
    let nonzeroPaddingBytes = 0;
    let paddingBytes = 0;
    for (const [start, end] of paddingRanges) {
      paddingBytes += end - start;
      for (let offset = start; offset < end; offset += 1) if (buffer[offset] !== 0) nonzeroPaddingBytes += 1;
    }
    const archiveRow = {
      physical_archive: context.physicalRelative,
      archive_identity: context.archiveIdentity,
      nesting_depth: depth,
      container_entry: context.containerEntry || '',
      file_size: parsed.fileSize,
      sha256: sha256(buffer),
      eoh: parsed.eoh,
      eoh_hex: `0x${parsed.eoh.toString(16)}`,
      table_end: parsed.tableEnd,
      minimum_eoh_align20: minimumEoh20,
      eoh_minus_minimum: parsed.eoh - minimumEoh20,
      entry_count: parsed.entryCount,
      size_field: parsed.sizeField,
      size_matches: parsed.sizeField === parsed.fileSize,
      eoh_aligned_0x20: parsed.eoh % 0x20 === 0,
      header_unknown_hex: parsed.headerUnknownHex,
      offsets_nondecreasing: offsetsNondecreasing,
      overlapping_pairs: overlaps,
      duplicate_name_count: duplicateNames,
      reserved_entry_count: parsed.entries.filter((entry) => entry.name === 'reserved_file').length,
      padding_range_count: paddingRanges.length,
      padding_byte_count: paddingBytes,
      nonzero_padding_byte_count: nonzeroPaddingBytes,
      standard_align20_packing: parsed.eoh === minimumEoh20
        && (!sortedByOffset.length || sortedByOffset[0].relativeOffset === 0)
        && standardLinks.every(Boolean)
        && parsed.fileSize === expectedStandardEnd,
    };
    archiveRows.push(archiveRow);
    increment(headerUnknownCounts, parsed.headerUnknownHex);
    increment(eohDeltaCounts, String(parsed.eoh - minimumEoh20));

    for (const entry of parsed.entries) {
      const stored = buffer.subarray(entry.absoluteOffset, entry.endOffset);
      const decoded = xor55(stored);
      const storedMagic = magicLabel(stored);
      const decodedMagic = magicLabel(decoded);
      const extension = extOf(entry.name);
      const alignment = entry.size ? (entry.relativeOffset % 0x20 === 0 ? '0x20' : entry.relativeOffset % 0x10 === 0 ? '0x10' : entry.relativeOffset % 4 === 0 ? '0x04' : 'unaligned') : 'zero-size';
      increment(extensionCounts, extension);
      increment(decodedMagicCounts, decodedMagic);
      increment(storedMagicCounts, storedMagic);
      increment(alignmentCounts, alignment);
      if (isKnownMagic(decodedMagic)) xorDecodedKnownMagic += 1;
      if (isKnownMagic(storedMagic)) rawKnownMagic += 1;
      const nameUsed = entry.nameRaw.indexOf(0) === -1 ? entry.nameRaw : entry.nameRaw.subarray(0, entry.nameRaw.indexOf(0));
      if (!printableAscii(nameUsed)) nonAsciiEntryNameCount += 1;
      if (entry.nameRaw.indexOf(0) === -1) unterminatedEntryNameCount += 1;

      const next = parsed.entries[entry.index + 1];
      const entryIdentity = `${context.archiveIdentity}::${String(entry.index).padStart(4, '0')}:${entry.name}`;
      const row = {
        physical_archive: context.physicalRelative,
        archive_identity: context.archiveIdentity,
        nesting_depth: depth,
        entry_index: entry.index,
        entry_identity: entryIdentity,
        name: entry.name,
        name_raw_hex: entry.nameRaw.toString('hex'),
        extension,
        record_offset: entry.recordOffset,
        size: entry.size,
        relative_offset: entry.relativeOffset,
        absolute_offset_in_container: entry.absoluteOffset,
        end_offset_in_container: entry.endOffset,
        next_table_entry_gap: next ? next.absoluteOffset - entry.endOffset : parsed.fileSize - entry.endOffset,
        offset_alignment: alignment,
        xor_key: '0x55',
        stored_prefix_hex: stored.subarray(0, 16).toString('hex'),
        decoded_prefix_hex: decoded.subarray(0, 16).toString('hex'),
        stored_magic: storedMagic,
        decoded_magic: decodedMagic,
        stored_sha256: sha256(stored),
        decoded_sha256: sha256(decoded),
      };
      entryRows.push(row);

      let text = null;
      if (shouldTextScan(entry.name, decodedMagic, decoded.length)) {
        text = detectJapaneseText(decoded);
        if (text.verdict) {
          textCandidates.push({
            physicalArchive: context.physicalRelative,
            archiveIdentity: context.archiveIdentity,
            nestingDepth: depth,
            entryIndex: entry.index,
            entryIdentity,
            name: entry.name,
            size: entry.size,
            decodedMagic,
            encoding: text.verdict,
            confidence: text.confidence,
            eucJpStringCount: text.eucJp.stringCount,
            eucJpJapaneseChars: text.eucJp.japaneseChars,
            eucJpHiraganaChars: text.eucJp.hiraganaChars,
            eucJpNulTerminatedCount: text.eucJp.nulTerminatedCount,
            shiftJisStringCount: text.shiftJis.stringCount,
            shiftJisJapaneseChars: text.shiftJis.japaneseChars,
            shiftJisHiraganaChars: text.shiftJis.hiraganaChars,
            shiftJisNulTerminatedCount: text.shiftJis.nulTerminatedCount,
            samples: (text.verdict === 'euc-jp' ? text.eucJp : text.shiftJis).samples,
          });
        }
      }

      if (decodedMagic === 'BSCR') {
        const detected = text && text.verdict ? text : null;
        const preferred = detected
          ? (detected.verdict === 'euc-jp' ? detected.eucJp : detected.shiftJis)
          : null;
        scriptPayloads.push({
          physicalArchive: context.physicalRelative,
          archiveIdentity: context.archiveIdentity,
          nestingDepth: depth,
          entryIndex: entry.index,
          entryIdentity,
          name: entry.name,
          size: entry.size,
          decodedMagic,
          formatClass: 'BSCR scenario/event script',
          encoding: detected ? detected.verdict : 'euc-jp (corpus inference; no Japanese string present)',
          confidence: detected ? detected.confidence : 'structural',
          stringCount: preferred ? preferred.stringCount : 0,
          japaneseChars: preferred ? preferred.japaneseChars : 0,
          nulTerminatedCount: preferred ? preferred.nulTerminatedCount : 0,
          samples: preferred ? preferred.samples : [],
        });
      }

      const bestEuc = text && text.verdict === 'euc-jp' ? text.eucJp : null;
      const sampledNulTerminated = bestEuc
        ? bestEuc.samples.filter((sample) => sample.terminatedByNul).length
        : 0;
      const strongTable = bestEuc
        && ['.bin', '.dat'].includes(extension)
        && sampledNulTerminated >= 3
        && bestEuc.japaneseChars >= 10;
      const partyName = /^btl_stat_party\d{2}b?\.bin$/i.test(entry.name)
        && bestEuc && bestEuc.nulTerminatedCount >= 1;
      const fieldEmbedded = entry.name.toLowerCase() === 'fld000.bin'
        && bestEuc && bestEuc.nulTerminatedCount >= 1;
      if (decodedMagic !== 'BSCR' && (strongTable || partyName || fieldEmbedded)) {
        const candidateClass = partyName ? 'embedded battle party display name'
          : fieldEmbedded ? 'embedded field/resource labels'
            : 'localized data/string table';
        localizationPayloads.push({
          physicalArchive: context.physicalRelative,
          archiveIdentity: context.archiveIdentity,
          nestingDepth: depth,
          entryIndex: entry.index,
          entryIdentity,
          name: entry.name,
          size: entry.size,
          decodedMagic,
          formatClass: candidateClass,
          encoding: 'euc-jp',
          confidence: strongTable ? 'high' : 'targeted',
          stringCount: bestEuc.stringCount,
          japaneseChars: bestEuc.japaneseChars,
          nulTerminatedCount: bestEuc.nulTerminatedCount,
          samples: bestEuc.samples,
        });
      }

      if (decodedMagic === 'RTDP' && decoded.length >= TABLE_OFFSET && depth < 8) {
        nestedArchiveCount += 1;
        auditArchiveBuffer(decoded, {
          physicalRelative: context.physicalRelative,
          archiveIdentity: entryIdentity,
          containerEntry: entryIdentity,
        }, depth + 1);
      }
    }
  }

  for (const file of physical) {
    const relative = path.relative(rootAbsolute, file);
    try {
      const buffer = fs.readFileSync(file);
      auditArchiveBuffer(buffer, {
        physicalRelative: relative,
        archiveIdentity: relative,
        containerEntry: '',
      }, 0);
    } catch (error) {
      errors.push({ physicalArchive: relative, error: error.stack || String(error) });
    }
  }

  textCandidates.sort((a, b) => {
    const confidenceRank = { high: 0, medium: 1, low: 2 };
    return (confidenceRank[a.confidence] ?? 9) - (confidenceRank[b.confidence] ?? 9)
      || b.eucJpJapaneseChars - a.eucJpJapaneseChars
      || a.entryIdentity.localeCompare(b.entryIdentity, 'en');
  });
  localizationPayloads.push(...scriptPayloads);
  localizationPayloads.sort((a, b) => a.entryIdentity.localeCompare(b.entryIdentity, 'en'));
  scriptPayloads.sort((a, b) => a.entryIdentity.localeCompare(b.entryIdentity, 'en'));

  const summary = {
    generatedAt: new Date().toISOString(),
    root: rootAbsolute,
    evidenceParser: path.resolve('work/tools/DolphinTextureExtraction-tool/lib/AuroraLip/Archives/Formats/RTDP.cs'),
    physicalVolCount: physical.length,
    parsedArchiveCountIncludingNested: archiveRows.length,
    nestedArchiveCount,
    entryCountIncludingNested: entryRows.length,
    nonEmptyEntryCount: entryRows.filter((row) => row.size > 0).length,
    zeroSizeEntryCount: entryRows.filter((row) => row.size === 0).length,
    parseErrorCount: errors.length,
    sizeMismatchCount: archiveRows.filter((row) => !row.size_matches).length,
    eohUnalignedCount: archiveRows.filter((row) => !row.eoh_aligned_0x20).length,
    offsetsNotNondecreasingCount: archiveRows.filter((row) => !row.offsets_nondecreasing).length,
    archivesWithOverlaps: archiveRows.filter((row) => row.overlapping_pairs.length).length,
    textCandidateCount: textCandidates.length,
    highConfidenceTextCandidateCount: textCandidates.filter((candidate) => candidate.confidence === 'high').length,
    eucJpCandidateCount: textCandidates.filter((candidate) => candidate.encoding === 'euc-jp').length,
    shiftJisCandidateCount: textCandidates.filter((candidate) => candidate.encoding === 'shift_jis').length,
    scriptPayloadCount: scriptPayloads.length,
    scriptPayloadsWithDetectedJapanese: scriptPayloads.filter((candidate) => candidate.japaneseChars > 0).length,
    vettedLocalizationPayloadCount: localizationPayloads.length,
    vettedNonScriptLocalizationPayloadCount: localizationPayloads.length - scriptPayloads.length,
    nonAsciiEntryNameCount,
    unterminatedEntryNameCount,
    archivesWithDuplicateNames: archiveRows.filter((row) => row.duplicate_name_count > 0).length,
    archivesWithNonzeroPadding: archiveRows.filter((row) => row.nonzero_padding_byte_count > 0).length,
    standardAlign20PackedArchiveCount: archiveRows.filter((row) => row.standard_align20_packing).length,
    xorEvidence: {
      key: '0x55',
      knownDecodedMagicCount: xorDecodedKnownMagic,
      knownStoredMagicCount: rawKnownMagic,
      note: 'All payload prefixes/hashes are reported both as stored and after bytewise XOR 0x55. Nested .vol payloads become RTDP only after XOR.',
    },
    entryExtensions: summarizeCounter(extensionCounts),
    decodedMagics: summarizeCounter(decodedMagicCounts),
    storedMagics: summarizeCounter(storedMagicCounts),
    headerUnknownValues: summarizeCounter(headerUnknownCounts),
    eohMinusAlignedTableEnd: summarizeCounter(eohDeltaCounts),
    entryOffsetAlignment: summarizeCounter(alignmentCounts),
  };

  fs.writeFileSync(path.join(outputDirectory, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`, 'utf8');
  fs.writeFileSync(path.join(outputDirectory, 'archives.json'), `${JSON.stringify(archiveRows, null, 2)}\n`, 'utf8');
  fs.writeFileSync(path.join(outputDirectory, 'entries.json'), `${JSON.stringify(entryRows, null, 2)}\n`, 'utf8');
  fs.writeFileSync(path.join(outputDirectory, 'text_candidates.json'), `${JSON.stringify(textCandidates, null, 2)}\n`, 'utf8');
  fs.writeFileSync(path.join(outputDirectory, 'script_payloads.json'), `${JSON.stringify(scriptPayloads, null, 2)}\n`, 'utf8');
  fs.writeFileSync(path.join(outputDirectory, 'localization_payloads.json'), `${JSON.stringify(localizationPayloads, null, 2)}\n`, 'utf8');
  fs.writeFileSync(path.join(outputDirectory, 'errors.json'), `${JSON.stringify(errors, null, 2)}\n`, 'utf8');

  writeCsv(path.join(outputDirectory, 'archives.csv'), archiveRows, [
    'physical_archive', 'archive_identity', 'nesting_depth', 'container_entry', 'file_size', 'sha256',
    'eoh', 'eoh_hex', 'table_end', 'minimum_eoh_align20', 'eoh_minus_minimum', 'entry_count',
    'size_field', 'size_matches', 'eoh_aligned_0x20', 'header_unknown_hex',
    'offsets_nondecreasing', 'overlapping_pairs', 'duplicate_name_count', 'reserved_entry_count',
    'padding_range_count', 'padding_byte_count', 'nonzero_padding_byte_count', 'standard_align20_packing',
  ]);
  writeCsv(path.join(outputDirectory, 'entries.csv'), entryRows, [
    'physical_archive', 'archive_identity', 'nesting_depth', 'entry_index', 'entry_identity', 'name',
    'name_raw_hex', 'extension', 'record_offset', 'size', 'relative_offset',
    'absolute_offset_in_container', 'end_offset_in_container', 'next_table_entry_gap',
    'offset_alignment', 'xor_key', 'stored_prefix_hex', 'decoded_prefix_hex', 'stored_magic',
    'decoded_magic', 'stored_sha256', 'decoded_sha256',
  ]);
  writeCsv(path.join(outputDirectory, 'text_candidates.csv'), textCandidates.map((candidate) => ({
    ...candidate,
    samples: candidate.samples.map((sample) => `0x${sample.offset.toString(16)}:${sample.text}`).join(' | '),
  })), [
    'physicalArchive', 'archiveIdentity', 'nestingDepth', 'entryIndex', 'entryIdentity', 'name',
    'size', 'decodedMagic', 'encoding', 'confidence', 'eucJpStringCount', 'eucJpJapaneseChars',
    'eucJpHiraganaChars', 'eucJpNulTerminatedCount', 'shiftJisStringCount', 'shiftJisJapaneseChars', 'shiftJisHiraganaChars', 'shiftJisNulTerminatedCount',
    'samples',
  ]);
  writeCsv(path.join(outputDirectory, 'script_payloads.csv'), scriptPayloads.map((candidate) => ({
    ...candidate,
    samples: candidate.samples.map((sample) => `0x${sample.offset.toString(16)}:${sample.text}`).join(' | '),
  })), [
    'physicalArchive', 'archiveIdentity', 'nestingDepth', 'entryIndex', 'entryIdentity', 'name',
    'size', 'decodedMagic', 'formatClass', 'encoding', 'confidence', 'stringCount',
    'japaneseChars', 'nulTerminatedCount', 'samples',
  ]);
  writeCsv(path.join(outputDirectory, 'localization_payloads.csv'), localizationPayloads.map((candidate) => ({
    ...candidate,
    samples: candidate.samples.map((sample) => `0x${sample.offset.toString(16)}:${sample.text}`).join(' | '),
  })), [
    'physicalArchive', 'archiveIdentity', 'nestingDepth', 'entryIndex', 'entryIdentity', 'name',
    'size', 'decodedMagic', 'formatClass', 'encoding', 'confidence', 'stringCount',
    'japaneseChars', 'nulTerminatedCount', 'samples',
  ]);

  return summary;
}

function usage() {
  process.stdout.write([
    'Usage:',
    '  node rtdp_tool.js audit <DATA/files root> <output directory>',
    '  node rtdp_tool.js extract <archive.vol> <output directory>',
    '  node rtdp_tool.js repack <extraction directory> <output.vol>',
    '  node rtdp_tool.js inspect <archive.vol>',
    '',
    'All extraction/repack operations leave the source archive untouched.',
    'Repack is intentionally fixed-layout and refuses changed payload sizes.',
    '',
  ].join('\n'));
}

function main() {
  const [command, arg1, arg2] = process.argv.slice(2);
  if (!command || command === '--help' || command === '-h') {
    usage();
    return;
  }
  if (command === 'audit') {
    if (!arg1 || !arg2) throw new Error('audit requires a root and output directory');
    const summary = auditRoot(arg1, arg2);
    process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
    return;
  }
  if (command === 'extract') {
    if (!arg1 || !arg2) throw new Error('extract requires an archive and output directory');
    const manifest = extractArchive(arg1, arg2);
    process.stdout.write(`${JSON.stringify({
      archive: manifest.sourceArchive,
      sha256: manifest.sourceArchiveSha256,
      size: manifest.sourceArchiveSize,
      entryCount: manifest.entryCount,
      outputDirectory: path.resolve(arg2),
    }, null, 2)}\n`);
    return;
  }
  if (command === 'repack') {
    if (!arg1 || !arg2) throw new Error('repack requires an extraction directory and output archive');
    process.stdout.write(`${JSON.stringify(repackArchive(arg1, arg2), null, 2)}\n`);
    return;
  }
  if (command === 'inspect') {
    if (!arg1) throw new Error('inspect requires an archive');
    const buffer = fs.readFileSync(arg1);
    const parsed = parseRtdp(buffer, arg1);
    const view = {
      archive: path.resolve(arg1),
      sha256: sha256(buffer),
      fileSize: parsed.fileSize,
      eoh: parsed.eoh,
      entryCount: parsed.entryCount,
      sizeField: parsed.sizeField,
      headerUnknownHex: parsed.headerUnknownHex,
      entries: parsed.entries.map((entry) => {
        const stored = buffer.subarray(entry.absoluteOffset, entry.endOffset);
        const decoded = xor55(stored);
        return {
          index: entry.index,
          name: entry.name,
          size: entry.size,
          relativeOffset: entry.relativeOffset,
          absoluteOffset: entry.absoluteOffset,
          storedMagic: magicLabel(stored),
          decodedMagic: magicLabel(decoded),
          decodedSha256: sha256(decoded),
        };
      }),
    };
    process.stdout.write(`${JSON.stringify(view, null, 2)}\n`);
    return;
  }
  throw new Error(`Unknown command: ${command}`);
}

try {
  main();
} catch (error) {
  die(error.stack || String(error));
}
