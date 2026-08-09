#!/usr/bin/env node
'use strict';

/*
 * Arc Rise Fantasia (RPJJ99) outer-container rebuilder.
 *
 * This module deliberately does not translate or interpret payload contents.
 * It only rebuilds the two container layers established by the local corpus:
 *
 *   - RTDP archives (big-endian table, XOR 0x55 payloads)
 *   - Nintendo LZ10 wrappers used by .cxd files
 *
 * Safe identity is always an entry-index path.  Names are diagnostic only;
 * duplicate and non-NUL-terminated 32-byte name fields exist in the game.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const RTDP_MAGIC = Buffer.from('RTDP', 'ascii');
const TABLE_OFFSET = 0x20;
const RECORD_SIZE = 40;
const XOR_KEY = 0x55;
const ALIGNMENT = 0x20;
const LZ10_MAX_UNPACKED = 0x00ffffff;

const GAMEOVER_SIGNATURE = Object.freeze({
  eoh: 0x800,
  entryCount: 12,
  fileSize: 0x3b000,
  headerUnknownHex: '55280021000000000000000000000000',
  names: [
    'g.wtm', 'a.wtm', 'm.wtm', 'e.wtm', 'o.wtm', 'v.wtm',
    'e.wtm', 'r.wtm', 'bokemoji1.wtm', 'bokemoji2.wtm',
    'moji.wtm', 'mojihikari.wtm',
  ],
  relativeOffsets: [
    0x00000, 0x02800, 0x05000, 0x07800, 0x0a000, 0x0c800,
    0x0f000, 0x11800, 0x14000, 0x23000, 0x32000, 0x36000,
  ],
});

class ContainerError extends Error {
  constructor(code, message, details = undefined) {
    super(`${code}: ${message}`);
    this.name = 'ContainerError';
    this.code = code;
    if (details !== undefined) this.details = details;
  }
}

function assert(condition, code, message, details = undefined) {
  if (!condition) throw new ContainerError(code, message, details);
}

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function alignUp(value, alignment) {
  assert(Number.isSafeInteger(value) && value >= 0, 'INVALID_INTEGER', `Invalid value ${value}`);
  assert(Number.isSafeInteger(alignment) && alignment > 0, 'INVALID_ALIGNMENT', `Invalid alignment ${alignment}`);
  return Math.ceil(value / alignment) * alignment;
}

function xor55(buffer) {
  const out = Buffer.allocUnsafe(buffer.length);
  for (let i = 0; i < buffer.length; i += 1) out[i] = buffer[i] ^ XOR_KEY;
  return out;
}

function readName(raw) {
  const nul = raw.indexOf(0);
  return raw.subarray(0, nul === -1 ? raw.length : nul).toString('latin1');
}

function hasMagic(buffer, magic) {
  return buffer.length >= magic.length && buffer.subarray(0, magic.length).equals(magic);
}

function parseRtdp(buffer, sourceLabel = '<buffer>') {
  assert(Buffer.isBuffer(buffer), 'INVALID_BUFFER', `${sourceLabel}: RTDP input must be a Buffer`);
  assert(buffer.length >= TABLE_OFFSET, 'RTDP_TRUNCATED_HEADER', `${sourceLabel}: shorter than 0x20 bytes`);
  assert(hasMagic(buffer, RTDP_MAGIC), 'RTDP_BAD_MAGIC', `${sourceLabel}: missing RTDP magic`);

  const eoh = buffer.readUInt32BE(0x04);
  const entryCount = buffer.readUInt32BE(0x08);
  const sizeField = buffer.readUInt32BE(0x0c);
  const tableEnd = TABLE_OFFSET + entryCount * RECORD_SIZE;
  assert(tableEnd <= buffer.length, 'RTDP_TRUNCATED_TABLE', `${sourceLabel}: table ends outside archive`, {
    tableEnd,
    fileSize: buffer.length,
  });
  assert(eoh >= tableEnd && eoh <= buffer.length, 'RTDP_BAD_EOH', `${sourceLabel}: invalid EOH`, {
    eoh,
    tableEnd,
    fileSize: buffer.length,
  });

  const entries = [];
  for (let index = 0; index < entryCount; index += 1) {
    const recordOffset = TABLE_OFFSET + index * RECORD_SIZE;
    const nameRaw = Buffer.from(buffer.subarray(recordOffset, recordOffset + 32));
    const size = buffer.readUInt32BE(recordOffset + 32);
    const relativeOffset = buffer.readUInt32BE(recordOffset + 36);
    const absoluteOffset = eoh + relativeOffset;
    const endOffset = absoluteOffset + size;
    assert(absoluteOffset <= buffer.length && endOffset <= buffer.length, 'RTDP_ENTRY_RANGE', `${sourceLabel}: entry ${index} is outside archive`, {
      index,
      name: readName(nameRaw),
      size,
      relativeOffset,
      absoluteOffset,
      endOffset,
      fileSize: buffer.length,
    });
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

  const nonEmpty = entries.filter((entry) => entry.size > 0);
  const overlaps = [];
  for (let i = 1; i < nonEmpty.length; i += 1) {
    const previous = nonEmpty[i - 1];
    const current = nonEmpty[i];
    if (current.absoluteOffset < previous.endOffset) overlaps.push([previous.index, current.index]);
  }

  return {
    sourceLabel,
    eoh,
    entryCount,
    sizeField,
    tableEnd,
    fileSize: buffer.length,
    headerUnknown: Buffer.from(buffer.subarray(0x10, 0x20)),
    headerUnknownHex: buffer.subarray(0x10, 0x20).toString('hex'),
    headerPadding: Buffer.from(buffer.subarray(tableEnd, eoh)),
    entries,
    overlaps,
  };
}

function decodeRtdpEntries(buffer, parsed = parseRtdp(buffer)) {
  return parsed.entries.map((entry) => xor55(buffer.subarray(entry.absoluteOffset, entry.endOffset)));
}

function analyzeStandardLayout(buffer, parsed = parseRtdp(buffer)) {
  const reasons = [];
  const expectedEoh = alignUp(parsed.tableEnd, ALIGNMENT);
  if (parsed.eoh !== expectedEoh) reasons.push(`EOH 0x${parsed.eoh.toString(16)} != aligned table end 0x${expectedEoh.toString(16)}`);
  if (parsed.sizeField !== parsed.fileSize) reasons.push(`size field ${parsed.sizeField} != file size ${parsed.fileSize}`);
  if (parsed.overlaps.length) reasons.push(`overlapping entries ${JSON.stringify(parsed.overlaps)}`);

  let cursor = 0;
  let seenNonEmpty = false;
  for (const entry of parsed.entries) {
    if (entry.size === 0) {
      if (entry.relativeOffset !== 0) reasons.push(`zero-size entry ${entry.index} has nonzero offset ${entry.relativeOffset}`);
      continue;
    }
    const expected = seenNonEmpty ? alignUp(cursor, ALIGNMENT) : 0;
    if (entry.relativeOffset !== expected) {
      reasons.push(`entry ${entry.index} offset 0x${entry.relativeOffset.toString(16)} != canonical 0x${expected.toString(16)}`);
    }
    cursor = entry.relativeOffset + entry.size;
    seenNonEmpty = true;
  }
  const expectedSize = parsed.eoh + alignUp(cursor, ALIGNMENT);
  if (parsed.fileSize !== expectedSize) reasons.push(`file size 0x${parsed.fileSize.toString(16)} != canonical 0x${expectedSize.toString(16)}`);

  // Corpus evidence says every standard-layout padding byte is zero.  Refuse
  // to discard a future nonzero opaque byte when compacting a resized archive.
  if (!reasons.length) {
    let dataCursor = parsed.eoh;
    for (const entry of parsed.entries) {
      if (!entry.size) continue;
      for (let i = dataCursor; i < entry.absoluteOffset; i += 1) {
        if (buffer[i] !== 0) {
          reasons.push(`nonzero opaque byte at 0x${i.toString(16)}`);
          break;
        }
      }
      if (reasons.length) break;
      dataCursor = entry.endOffset;
    }
    if (!reasons.length) {
      for (let i = dataCursor; i < buffer.length; i += 1) {
        if (buffer[i] !== 0) {
          reasons.push(`nonzero trailing opaque byte at 0x${i.toString(16)}`);
          break;
        }
      }
    }
  }

  return { standard: reasons.length === 0, reasons, expectedEoh, expectedSize };
}

/**
 * Recognize the one additional layout convention observed in the RPJJ99 map
 * corpus: a zero-length optional entry may carry the same offset as a later
 * non-empty entry.  The offset is an anchor (the insertion point the missing
 * optional payload would have occupied), not stored payload data.
 *
 * Apart from those aliases, the archive must satisfy every canonical RTDP
 * invariant: aligned table/data geometry, canonical non-empty offsets, zero
 * inter-entry/trailing padding, matching size field, and no overlaps.  Each
 * nonzero empty-entry offset must resolve unambiguously to a non-empty entry.
 */
function analyzeZeroSizeAnchorLayout(buffer, parsed = parseRtdp(buffer)) {
  const reasons = [];
  const anchors = [];
  const expectedEoh = alignUp(parsed.tableEnd, ALIGNMENT);
  if (parsed.eoh !== expectedEoh) reasons.push(`EOH 0x${parsed.eoh.toString(16)} != aligned table end 0x${expectedEoh.toString(16)}`);
  if (parsed.sizeField !== parsed.fileSize) reasons.push(`size field ${parsed.sizeField} != file size ${parsed.fileSize}`);
  if (parsed.overlaps.length) reasons.push(`overlapping entries ${JSON.stringify(parsed.overlaps)}`);

  let cursor = 0;
  let seenNonEmpty = false;
  for (const entry of parsed.entries) {
    if (entry.size === 0) continue;
    const expected = seenNonEmpty ? alignUp(cursor, ALIGNMENT) : 0;
    if (entry.relativeOffset !== expected) {
      reasons.push(`entry ${entry.index} offset 0x${entry.relativeOffset.toString(16)} != canonical 0x${expected.toString(16)}`);
    }
    cursor = entry.relativeOffset + entry.size;
    seenNonEmpty = true;
  }
  const expectedSize = parsed.eoh + alignUp(cursor, ALIGNMENT);
  if (parsed.fileSize !== expectedSize) reasons.push(`file size 0x${parsed.fileSize.toString(16)} != canonical 0x${expectedSize.toString(16)}`);

  for (const entry of parsed.entries) {
    if (entry.size !== 0 || entry.relativeOffset === 0) continue;
    const candidates = parsed.entries.filter((candidate) => (
      candidate.size > 0 && candidate.relativeOffset === entry.relativeOffset
    ));
    if (candidates.length !== 1) {
      reasons.push(`zero-size entry ${entry.index} offset 0x${entry.relativeOffset.toString(16)} has ${candidates.length} non-empty anchor targets`);
      continue;
    }
    anchors.push({ emptyEntryIndex: entry.index, targetEntryIndex: candidates[0].index });
  }
  if (!anchors.length) reasons.push('no nonzero zero-size anchor entries');

  // Repacking is safe only if every byte outside declared payloads is known
  // zero padding.  This mirrors analyzeStandardLayout's opaque-byte guard.
  if (!reasons.length) {
    let dataCursor = parsed.eoh;
    for (const entry of parsed.entries) {
      if (!entry.size) continue;
      for (let i = dataCursor; i < entry.absoluteOffset; i += 1) {
        if (buffer[i] !== 0) {
          reasons.push(`nonzero opaque byte at 0x${i.toString(16)}`);
          break;
        }
      }
      if (reasons.length) break;
      dataCursor = entry.endOffset;
    }
    if (!reasons.length) {
      for (let i = dataCursor; i < buffer.length; i += 1) {
        if (buffer[i] !== 0) {
          reasons.push(`nonzero trailing opaque byte at 0x${i.toString(16)}`);
          break;
        }
      }
    }
  }

  return {
    supported: reasons.length === 0,
    reasons,
    anchors,
    expectedEoh,
    expectedSize,
  };
}

function isGameoverTemplate(parsed) {
  if (parsed.eoh !== GAMEOVER_SIGNATURE.eoh
      || parsed.entryCount !== GAMEOVER_SIGNATURE.entryCount
      || parsed.fileSize !== GAMEOVER_SIGNATURE.fileSize
      || parsed.sizeField !== parsed.fileSize
      || parsed.headerUnknownHex !== GAMEOVER_SIGNATURE.headerUnknownHex
      || parsed.overlaps.length) return false;
  for (let i = 0; i < parsed.entryCount; i += 1) {
    const entry = parsed.entries[i];
    if (entry.name !== GAMEOVER_SIGNATURE.names[i]
        || entry.relativeOffset !== GAMEOVER_SIGNATURE.relativeOffsets[i]
        || entry.size === 0) return false;
  }
  return true;
}

function payloadChanges(originalPayloads, newPayloads) {
  assert(Array.isArray(newPayloads), 'RTDP_PAYLOADS_TYPE', 'Payloads must be an array ordered by entry index');
  assert(originalPayloads.length === newPayloads.length, 'RTDP_PAYLOAD_COUNT', `Expected ${originalPayloads.length} payloads, got ${newPayloads.length}`);
  const changes = [];
  for (let i = 0; i < originalPayloads.length; i += 1) {
    assert(Buffer.isBuffer(newPayloads[i]), 'RTDP_PAYLOAD_TYPE', `Entry ${i} replacement is not a Buffer`);
    const oldPayload = originalPayloads[i];
    const newPayload = newPayloads[i];
    if (!oldPayload.equals(newPayload)) {
      changes.push({
        index: i,
        oldSize: oldPayload.length,
        newSize: newPayload.length,
        oldSha256: sha256(oldPayload),
        newSha256: sha256(newPayload),
      });
    }
  }
  return changes;
}

function verifyRtdpResult(template, rebuilt, newPayloads, policy, sourceLabel) {
  const before = parseRtdp(template, `${sourceLabel} (template)`);
  const after = parseRtdp(rebuilt, `${sourceLabel} (rebuilt)`);
  assert(after.sizeField === rebuilt.length, 'RTDP_REBUILD_SIZE_FIELD', `${sourceLabel}: rebuilt size field mismatch`);
  assert(after.entryCount === before.entryCount, 'RTDP_REBUILD_ENTRY_COUNT', `${sourceLabel}: entry count changed`);
  assert(after.eoh === before.eoh, 'RTDP_REBUILD_EOH', `${sourceLabel}: EOH changed`);
  assert(after.headerUnknown.equals(before.headerUnknown), 'RTDP_REBUILD_UNKNOWN_HEADER', `${sourceLabel}: opaque header bytes changed`);
  assert(after.headerPadding.equals(before.headerPadding), 'RTDP_REBUILD_HEADER_PADDING', `${sourceLabel}: EOH padding changed`);
  for (let i = 0; i < before.entryCount; i += 1) {
    assert(after.entries[i].nameRaw.equals(before.entries[i].nameRaw), 'RTDP_REBUILD_NAME', `${sourceLabel}: raw name changed at entry ${i}`);
    assert(after.entries[i].size === newPayloads[i].length, 'RTDP_REBUILD_ENTRY_SIZE', `${sourceLabel}: wrong size at entry ${i}`);
    const extracted = xor55(rebuilt.subarray(after.entries[i].absoluteOffset, after.entries[i].endOffset));
    assert(extracted.equals(newPayloads[i]), 'RTDP_REBUILD_PAYLOAD', `${sourceLabel}: re-extracted payload mismatch at entry ${i}`);
  }
  if (policy === 'standard-resize') {
    const standard = analyzeStandardLayout(rebuilt, after);
    assert(standard.standard, 'RTDP_REBUILD_NOT_STANDARD', `${sourceLabel}: rebuilt standard archive is not canonical`, standard.reasons);
  }
  if (policy === 'zero-size-anchor-resize') {
    const beforeLayout = analyzeZeroSizeAnchorLayout(template, before);
    const afterLayout = analyzeZeroSizeAnchorLayout(rebuilt, after);
    assert(beforeLayout.supported, 'RTDP_REBUILD_ANCHOR_SOURCE', `${sourceLabel}: source anchor layout no longer validates`, beforeLayout.reasons);
    assert(afterLayout.supported, 'RTDP_REBUILD_ANCHOR_OUTPUT', `${sourceLabel}: rebuilt anchor layout is invalid`, afterLayout.reasons);
    assert(JSON.stringify(afterLayout.anchors) === JSON.stringify(beforeLayout.anchors), 'RTDP_REBUILD_ANCHOR_IDENTITY', `${sourceLabel}: zero-size anchor relationships changed`, {
      before: beforeLayout.anchors,
      after: afterLayout.anchors,
    });
  }
  if (policy === 'gameover-template') {
    assert(isGameoverTemplate(after), 'RTDP_REBUILD_GAMEOVER_TEMPLATE', `${sourceLabel}: special template geometry changed`);
    for (let i = 0; i < before.entryCount; i += 1) {
      assert(after.entries[i].relativeOffset === before.entries[i].relativeOffset, 'RTDP_REBUILD_GAMEOVER_OFFSET', `${sourceLabel}: gameover slot ${i} moved`);
    }
  }
  return after;
}

function rebuildFixedLayout(template, parsed, newPayloads) {
  const rebuilt = Buffer.from(template);
  for (const entry of parsed.entries) {
    const payload = newPayloads[entry.index];
    assert(payload.length === entry.size, 'RTDP_FIXED_SIZE_CHANGE', `Entry ${entry.index} changed size in fixed-layout mode`);
    xor55(payload).copy(rebuilt, entry.absoluteOffset);
  }
  return rebuilt;
}

function rebuildStandard(template, parsed, newPayloads) {
  for (const entry of parsed.entries) {
    const wasEmpty = entry.size === 0;
    const isEmpty = newPayloads[entry.index].length === 0;
    assert(wasEmpty === isEmpty, 'RTDP_EMPTY_STATE_CHANGE', `Entry ${entry.index}: changing empty/non-empty state is unsupported`, {
      oldSize: entry.size,
      newSize: newPayloads[entry.index].length,
    });
  }

  const relativeOffsets = new Array(parsed.entryCount).fill(0);
  let cursor = 0;
  let seenNonEmpty = false;
  for (const entry of parsed.entries) {
    const payload = newPayloads[entry.index];
    if (!payload.length) continue;
    const relativeOffset = seenNonEmpty ? alignUp(cursor, ALIGNMENT) : 0;
    relativeOffsets[entry.index] = relativeOffset;
    cursor = relativeOffset + payload.length;
    seenNonEmpty = true;
  }
  const newSize = parsed.eoh + alignUp(cursor, ALIGNMENT);
  assert(newSize <= 0xffffffff, 'RTDP_TOO_LARGE', `Rebuilt RTDP exceeds u32 size: ${newSize}`);

  const rebuilt = Buffer.alloc(newSize, 0);
  template.subarray(0, parsed.eoh).copy(rebuilt, 0);
  rebuilt.writeUInt32BE(newSize, 0x0c);
  for (const entry of parsed.entries) {
    const payload = newPayloads[entry.index];
    const recordOffset = entry.recordOffset;
    rebuilt.writeUInt32BE(payload.length, recordOffset + 32);
    rebuilt.writeUInt32BE(relativeOffsets[entry.index], recordOffset + 36);
    if (payload.length) xor55(payload).copy(rebuilt, parsed.eoh + relativeOffsets[entry.index]);
  }
  return rebuilt;
}

function rebuildZeroSizeAnchors(template, parsed, newPayloads, layout) {
  assert(layout.supported && layout.anchors.length > 0, 'RTDP_ANCHOR_LAYOUT', 'Unsupported zero-size anchor layout');
  // First perform the ordinary canonical repack.  It deliberately writes zero
  // offsets for empty entries; patch only the proven aliases afterward so they
  // follow their target entries to the new aligned positions.
  const rebuilt = rebuildStandard(template, parsed, newPayloads);
  const canonical = parseRtdp(rebuilt, `${parsed.sourceLabel} (canonical anchor intermediate)`);
  for (const anchor of layout.anchors) {
    const emptyEntry = canonical.entries[anchor.emptyEntryIndex];
    const targetEntry = canonical.entries[anchor.targetEntryIndex];
    assert(emptyEntry.size === 0 && targetEntry.size > 0, 'RTDP_ANCHOR_TARGET_STATE', `Anchor state changed for empty entry ${anchor.emptyEntryIndex}`);
    rebuilt.writeUInt32BE(targetEntry.relativeOffset, emptyEntry.recordOffset + 36);
  }
  return rebuilt;
}

function gameoverSlotEnd(parsed, entryIndex) {
  if (entryIndex + 1 < parsed.entries.length) return parsed.entries[entryIndex + 1].relativeOffset;
  return parsed.fileSize - parsed.eoh;
}

function rebuildGameoverTemplate(template, parsed, newPayloads) {
  const rebuilt = Buffer.from(template);
  for (const entry of parsed.entries) {
    const payload = newPayloads[entry.index];
    assert(payload.length > 0, 'GAMEOVER_EMPTY_ENTRY', `Gameover entry ${entry.index}: empty payload is unsupported`);
    const slotEnd = gameoverSlotEnd(parsed, entry.index);
    const slotCapacity = slotEnd - entry.relativeOffset;
    assert(payload.length <= slotCapacity, 'GAMEOVER_SLOT_OVERFLOW', `Gameover entry ${entry.index} exceeds its preserved slot`, {
      entryIndex: entry.index,
      name: entry.name,
      newSize: payload.length,
      slotCapacity,
      relativeOffset: entry.relativeOffset,
      slotEnd,
    });
    // Unknown slot padding is only safe to regenerate when it is zero in the
    // observed template.  This catches any future variant rather than erasing
    // opaque data under the guise of padding.
    for (let offset = entry.endOffset; offset < parsed.eoh + slotEnd; offset += 1) {
      assert(template[offset] === 0, 'GAMEOVER_NONZERO_SLOT_PADDING', `Gameover entry ${entry.index} has nonzero template padding at 0x${offset.toString(16)}`);
    }
    rebuilt.fill(0, parsed.eoh + entry.relativeOffset, parsed.eoh + slotEnd);
    xor55(payload).copy(rebuilt, parsed.eoh + entry.relativeOffset);
    rebuilt.writeUInt32BE(payload.length, entry.recordOffset + 32);
    // Relative offsets, EOH, file size, unknown header, and raw names remain
    // byte-for-byte copied from the template.
  }
  return rebuilt;
}

/**
 * Rebuild one RTDP archive from a complete decoded payload array.
 *
 * Policies:
 * - exact-noop: return the exact source bytes if no decoded payload changed.
 * - fixed-layout: any archive may receive same-size edits without relocation.
 * - standard-resize: canonical 0x20-packed archives may resize non-empty entries.
 * - zero-size-anchor-resize: canonical archives whose empty optional slot
 *   aliases a later payload offset preserve that relationship while repacking.
 * - gameover-template: the one known special archive keeps all original slots;
 *   each payload may resize only within its pre-existing slot.
 * - every other nonstandard resize is rejected explicitly.
 */
function rebuildRtdp(template, newPayloads, options = {}) {
  const sourceLabel = options.sourceLabel || '<RTDP>';
  const parsed = parseRtdp(template, sourceLabel);
  const originalPayloads = decodeRtdpEntries(template, parsed);
  const changes = payloadChanges(originalPayloads, newPayloads);
  const reportBase = {
    sourceLabel,
    inputSize: template.length,
    inputSha256: sha256(template),
    eoh: parsed.eoh,
    entryCount: parsed.entryCount,
    headerUnknownHex: parsed.headerUnknownHex,
    changes,
  };
  if (!changes.length) {
    const buffer = Buffer.from(template);
    return {
      buffer,
      report: { ...reportBase, policy: 'exact-noop', outputSize: buffer.length, outputSha256: sha256(buffer), byteExact: true },
    };
  }

  assert(parsed.sizeField === parsed.fileSize, 'RTDP_SOURCE_SIZE_FIELD', `${sourceLabel}: source size field mismatch`);
  assert(!parsed.overlaps.length, 'RTDP_SOURCE_OVERLAP', `${sourceLabel}: source entries overlap`, parsed.overlaps);
  const hasResize = changes.some((change) => change.oldSize !== change.newSize);
  let policy;
  let rebuilt;
  if (!hasResize) {
    policy = 'fixed-layout';
    rebuilt = rebuildFixedLayout(template, parsed, newPayloads);
  } else {
    const standard = analyzeStandardLayout(template, parsed);
    if (standard.standard) {
      policy = 'standard-resize';
      rebuilt = rebuildStandard(template, parsed, newPayloads);
    } else {
      const anchored = analyzeZeroSizeAnchorLayout(template, parsed);
      if (anchored.supported) {
        policy = 'zero-size-anchor-resize';
        rebuilt = rebuildZeroSizeAnchors(template, parsed, newPayloads, anchored);
      } else if (isGameoverTemplate(parsed)) {
        policy = 'gameover-template';
        rebuilt = rebuildGameoverTemplate(template, parsed, newPayloads);
      } else {
        throw new ContainerError(
          'UNSUPPORTED_NONSTANDARD_RESIZE',
          `${sourceLabel}: variable-size rebuild is allowed only for canonical RTDP, a verified zero-size-anchor layout, or the recognized btl_gameover.vol template`,
          { standardReasons: standard.reasons, zeroSizeAnchorReasons: anchored.reasons },
        );
      }
    }
  }
  verifyRtdpResult(template, rebuilt, newPayloads, policy, sourceLabel);
  return {
    buffer: rebuilt,
    report: {
      ...reportBase,
      policy,
      outputSize: rebuilt.length,
      outputSha256: sha256(rebuilt),
      byteExact: rebuilt.equals(template),
    },
  };
}

function decompressLz10Detailed(packed, sourceLabel = '<LZ10>') {
  assert(Buffer.isBuffer(packed), 'INVALID_BUFFER', `${sourceLabel}: LZ10 input must be a Buffer`);
  assert(packed.length >= 4 && packed[0] === 0x10, 'LZ10_BAD_MAGIC', `${sourceLabel}: not an LZ10 stream`);
  const expectedSize = packed[1] | (packed[2] << 8) | (packed[3] << 16);
  let source = 4;
  const output = Buffer.alloc(expectedSize);
  let target = 0;
  while (target < expectedSize) {
    assert(source < packed.length, 'LZ10_TRUNCATED_FLAGS', `${sourceLabel}: truncated flags at output ${target}/${expectedSize}`);
    const flags = packed[source++];
    for (let bit = 7; bit >= 0 && target < expectedSize; bit -= 1) {
      if (flags & (1 << bit)) {
        assert(source + 2 <= packed.length, 'LZ10_TRUNCATED_BACKREF', `${sourceLabel}: truncated back-reference`);
        const first = packed[source++];
        const second = packed[source++];
        const length = (first >>> 4) + 3;
        const distance = (((first & 0x0f) << 8) | second) + 1;
        assert(distance <= target, 'LZ10_BAD_DISTANCE', `${sourceLabel}: invalid distance ${distance} at output ${target}`);
        for (let i = 0; i < length && target < expectedSize; i += 1) {
          output[target] = output[target - distance];
          target += 1;
        }
      } else {
        assert(source < packed.length, 'LZ10_TRUNCATED_LITERAL', `${sourceLabel}: truncated literal`);
        output[target++] = packed[source++];
      }
    }
  }
  return {
    output,
    expectedSize,
    consumedBytes: source,
    trailingBytes: Buffer.from(packed.subarray(source)),
  };
}

function decompressLz10(packed, sourceLabel = '<LZ10>') {
  return decompressLz10Detailed(packed, sourceLabel).output;
}

function lzKey(data, offset) {
  return (data[offset] << 16) | (data[offset + 1] << 8) | data[offset + 2];
}

/**
 * Deterministic Nintendo LZ10 compressor.
 *
 * Greedy longest match, 0x1000-byte window, 3..18-byte matches.  Equal-length
 * matches choose the nearest source position.  Every output is padded with
 * zero bytes to `alignment` (4 by default), which matches all sampled .cxd.
 */
function compressLz10(data, options = {}) {
  assert(Buffer.isBuffer(data), 'INVALID_BUFFER', 'LZ10 input must be a Buffer');
  assert(data.length <= LZ10_MAX_UNPACKED, 'LZ10_SIZE_LIMIT', `LZ10 24-bit size limit exceeded: ${data.length}`);
  const alignment = options.alignment === undefined ? 4 : options.alignment;
  assert(Number.isInteger(alignment) && alignment >= 1, 'LZ10_BAD_ALIGNMENT', `Invalid output alignment ${alignment}`);

  const bytes = [0x10, data.length & 0xff, (data.length >>> 8) & 0xff, (data.length >>> 16) & 0xff];
  const chains = new Map();
  let position = 0;

  function addPosition(pos) {
    if (pos + 2 >= data.length) return;
    const key = lzKey(data, pos);
    let chain = chains.get(key);
    if (!chain) {
      chain = { positions: [], head: 0 };
      chains.set(key, chain);
    }
    chain.positions.push(pos);
    // Amortized bounded memory: old positions can never be referenced again.
    while (chain.head < chain.positions.length && chain.positions[chain.head] < pos - 0x1000) chain.head += 1;
    if (chain.head > 4096 && chain.head * 2 > chain.positions.length) {
      chain.positions = chain.positions.slice(chain.head);
      chain.head = 0;
    }
  }

  while (position < data.length) {
    const flagIndex = bytes.length;
    bytes.push(0);
    let flags = 0;
    for (let token = 0; token < 8 && position < data.length; token += 1) {
      let bestLength = 0;
      let bestDistance = 0;
      if (position + 2 < data.length) {
        const chain = chains.get(lzKey(data, position));
        if (chain) {
          while (chain.head < chain.positions.length && chain.positions[chain.head] < position - 0x1000) chain.head += 1;
          // Reverse order makes equal-length ties select the nearest match.
          for (let c = chain.positions.length - 1; c >= chain.head; c -= 1) {
            const candidate = chain.positions[c];
            const distance = position - candidate;
            if (distance < 1 || distance > 0x1000) continue;
            const maxLength = Math.min(18, data.length - position);
            let length = 0;
            while (length < maxLength && data[candidate + length] === data[position + length]) length += 1;
            if (length > bestLength) {
              bestLength = length;
              bestDistance = distance;
              if (bestLength === 18) break;
            }
          }
        }
      }

      if (bestLength >= 3) {
        flags |= 1 << (7 - token);
        const encodedDistance = bestDistance - 1;
        bytes.push(((bestLength - 3) << 4) | ((encodedDistance >>> 8) & 0x0f));
        bytes.push(encodedDistance & 0xff);
        for (let i = 0; i < bestLength; i += 1) addPosition(position + i);
        position += bestLength;
      } else {
        bytes.push(data[position]);
        addPosition(position);
        position += 1;
      }
    }
    bytes[flagIndex] = flags;
  }

  while (bytes.length % alignment) bytes.push(0);
  const packed = Buffer.from(bytes);
  const roundtrip = decompressLz10(packed, '<new LZ10>');
  assert(roundtrip.equals(data), 'LZ10_SELF_VERIFY', 'Freshly compressed stream failed decompression equality');
  return packed;
}

function rebuildLz10(templatePacked, newUnpacked, options = {}) {
  const sourceLabel = options.sourceLabel || '<LZ10>';
  const detail = decompressLz10Detailed(templatePacked, sourceLabel);
  assert(Buffer.isBuffer(newUnpacked), 'INVALID_BUFFER', `${sourceLabel}: replacement unpacked data must be a Buffer`);
  if (detail.output.equals(newUnpacked)) {
    const buffer = Buffer.from(templatePacked);
    return {
      buffer,
      report: {
        sourceLabel,
        policy: 'exact-noop',
        inputPackedSize: templatePacked.length,
        outputPackedSize: buffer.length,
        unpackedSize: newUnpacked.length,
        inputSha256: sha256(templatePacked),
        outputSha256: sha256(buffer),
        unpackedSha256: sha256(newUnpacked),
        byteExact: true,
      },
    };
  }
  for (let i = 0; i < detail.trailingBytes.length; i += 1) {
    assert(detail.trailingBytes[i] === 0, 'LZ10_NONZERO_TRAILER', `${sourceLabel}: refusing to discard nonzero trailing byte at +0x${i.toString(16)}`);
  }
  const alignment = options.alignment === undefined ? 4 : options.alignment;
  const buffer = compressLz10(newUnpacked, { alignment });
  const verified = decompressLz10(buffer, `${sourceLabel} (rebuilt)`);
  assert(verified.equals(newUnpacked), 'LZ10_REBUILD_VERIFY', `${sourceLabel}: rebuilt stream did not decompress to requested bytes`);
  return {
    buffer,
    report: {
      sourceLabel,
      policy: 'deterministic-greedy-lz10',
      tieBreak: 'longest-match, then nearest-distance',
      alignment,
      inputPackedSize: templatePacked.length,
      outputPackedSize: buffer.length,
      unpackedSize: newUnpacked.length,
      inputSha256: sha256(templatePacked),
      outputSha256: sha256(buffer),
      unpackedSha256: sha256(newUnpacked),
      byteExact: buffer.equals(templatePacked),
    },
  };
}

/**
 * Safe whole-payload .cxd rewrapper for non-RTDP inners such as WTMD.
 * The caller must bind the edit to the exact decompressed source hash unless
 * `requireExpectedHash:false` is explicitly selected for research code.
 */
function rebuildCxdPayload(templatePacked, newUnpacked, options = {}) {
  const sourceLabel = options.sourceLabel || '<CXD/LZ10 payload>';
  const detail = decompressLz10Detailed(templatePacked, sourceLabel);
  const requireExpectedHash = options.requireExpectedHash !== false;
  const actualHash = sha256(detail.output);
  if (requireExpectedHash) {
    assert(typeof options.expectedUnpackedSha256 === 'string' && /^[0-9a-f]{64}$/i.test(options.expectedUnpackedSha256), 'CXD_EXPECTED_HASH', `${sourceLabel}: expectedUnpackedSha256 is required`);
    assert(actualHash === options.expectedUnpackedSha256.toLowerCase(), 'CXD_HASH_MISMATCH', `${sourceLabel}: decompressed source hash mismatch`, {
      expected: options.expectedUnpackedSha256.toLowerCase(),
      actual: actualHash,
    });
  }
  const wrapped = rebuildLz10(templatePacked, newUnpacked, options);
  const verified = decompressLz10(wrapped.buffer, `${sourceLabel} (whole-payload verify)`);
  assert(verified.equals(newUnpacked), 'CXD_PAYLOAD_VERIFY', `${sourceLabel}: whole-payload rewrap failed decompression equality`);
  return {
    buffer: wrapped.buffer,
    report: {
      format: 'LZ10-whole-payload-rebuild-v1',
      sourceLabel,
      inputPackedSize: templatePacked.length,
      outputPackedSize: wrapped.buffer.length,
      inputPackedSha256: sha256(templatePacked),
      outputPackedSha256: sha256(wrapped.buffer),
      inputUnpackedSize: detail.output.length,
      outputUnpackedSize: newUnpacked.length,
      inputUnpackedSha256: actualHash,
      outputUnpackedSha256: sha256(newUnpacked),
      decompressionEqualityVerified: true,
      lz10: wrapped.report,
    },
  };
}

function normalizeEdits(edits, options = {}) {
  assert(Array.isArray(edits), 'EDIT_LIST_TYPE', 'Edits must be an array');
  const requireExpectedHash = options.requireExpectedHash !== false;
  const normalized = edits.map((edit, ordinal) => {
    assert(edit && typeof edit === 'object', 'EDIT_TYPE', `Edit ${ordinal} must be an object`);
    assert(Array.isArray(edit.entryPath) && edit.entryPath.length > 0, 'EDIT_PATH', `Edit ${ordinal} needs a non-empty entryPath`);
    const entryPath = edit.entryPath.map((value) => {
      assert(Number.isInteger(value) && value >= 0, 'EDIT_PATH_INDEX', `Edit ${ordinal} has invalid entry index ${value}`);
      return value;
    });
    assert(Buffer.isBuffer(edit.data), 'EDIT_DATA', `Edit ${ordinal} data must be a Buffer`);
    if (requireExpectedHash) {
      assert(typeof edit.expectedSha256 === 'string' && /^[0-9a-f]{64}$/i.test(edit.expectedSha256), 'EDIT_EXPECTED_HASH', `Edit ${ordinal} needs expectedSha256`);
    }
    return { entryPath, data: edit.data, expectedSha256: edit.expectedSha256 ? edit.expectedSha256.toLowerCase() : undefined };
  });
  const keys = new Set();
  for (const edit of normalized) {
    const key = edit.entryPath.join('/');
    assert(!keys.has(key), 'EDIT_DUPLICATE_PATH', `Duplicate edit path ${key}`);
    keys.add(key);
  }
  for (const left of normalized) {
    for (const right of normalized) {
      if (left === right || left.entryPath.length >= right.entryPath.length) continue;
      const prefix = left.entryPath.every((value, index) => right.entryPath[index] === value);
      assert(!prefix, 'EDIT_PATH_CONFLICT', `Leaf edit ${left.entryPath.join('/')} is a prefix of ${right.entryPath.join('/')}`);
    }
  }
  return normalized;
}

function rebuildRtdpTree(template, edits, options = {}) {
  const sourceLabel = options.sourceLabel || '<RTDP tree>';
  const normalized = options.normalized ? edits : normalizeEdits(edits, options);
  const auditTrail = [];
  const containerTrail = [];

  function visit(container, localEdits, label, prefix) {
    const parsed = parseRtdp(container, label);
    const payloads = decodeRtdpEntries(container, parsed);
    const grouped = new Map();
    for (const edit of localEdits) {
      const index = edit.entryPath[0];
      assert(index < parsed.entryCount, 'EDIT_PATH_RANGE', `${label}: entry index ${index} out of range ${parsed.entryCount}`);
      if (!grouped.has(index)) grouped.set(index, []);
      grouped.get(index).push(edit);
    }
    for (const [index, group] of grouped) {
      const leaf = group.find((edit) => edit.entryPath.length === 1);
      const descendants = group.filter((edit) => edit.entryPath.length > 1);
      assert(!(leaf && descendants.length), 'EDIT_PATH_CONFLICT', `${label}: both leaf and descendant edits target entry ${index}`);
      if (leaf) {
        const oldPayload = payloads[index];
        const oldHash = sha256(oldPayload);
        if (leaf.expectedSha256) {
          assert(oldHash === leaf.expectedSha256, 'EDIT_HASH_MISMATCH', `${label}: entry ${index} expected hash mismatch`, {
            expected: leaf.expectedSha256,
            actual: oldHash,
            entryPath: [...prefix, index],
          });
        }
        payloads[index] = leaf.data;
        auditTrail.push({
          entryPath: [...prefix, index],
          name: parsed.entries[index].name,
          oldSize: oldPayload.length,
          newSize: leaf.data.length,
          oldSha256: oldHash,
          newSha256: sha256(leaf.data),
        });
      } else {
        const child = payloads[index];
        assert(hasMagic(child, RTDP_MAGIC), 'EDIT_DESCEND_NOT_RTDP', `${label}: entry ${index} is not a nested RTDP archive`);
        const stripped = descendants.map((edit) => ({ ...edit, entryPath: edit.entryPath.slice(1) }));
        const childResult = visit(child, stripped, `${label}::${String(index).padStart(4, '0')}:${parsed.entries[index].name}`, [...prefix, index]);
        payloads[index] = childResult;
      }
    }
    const result = rebuildRtdp(container, payloads, { sourceLabel: label });
    containerTrail.push({ prefix, ...result.report });
    return result.buffer;
  }

  const buffer = visit(template, normalized, sourceLabel, []);
  return {
    buffer,
    report: {
      format: 'RTDP-tree-rebuild-v1',
      sourceLabel,
      inputSha256: sha256(template),
      outputSha256: sha256(buffer),
      inputSize: template.length,
      outputSize: buffer.length,
      byteExact: buffer.equals(template),
      editAudit: auditTrail,
      // Bottom-up order: children are pushed before parents.
      containerAuditBottomUp: containerTrail,
    },
  };
}

function rebuildCxd(templatePacked, edits, options = {}) {
  const sourceLabel = options.sourceLabel || '<CXD/LZ10>';
  const normalized = normalizeEdits(edits, options);
  const detail = decompressLz10Detailed(templatePacked, sourceLabel);
  assert(hasMagic(detail.output, RTDP_MAGIC), 'CXD_INNER_NOT_RTDP', `${sourceLabel}: decompressed content is not RTDP`);
  const tree = rebuildRtdpTree(detail.output, normalized, { ...options, sourceLabel: `${sourceLabel}#unpacked`, normalized: true });
  const packed = rebuildLz10(templatePacked, tree.buffer, { ...options, sourceLabel });
  const unpackedAgain = decompressLz10(packed.buffer, `${sourceLabel} (final verify)`);
  assert(unpackedAgain.equals(tree.buffer), 'CXD_FINAL_VERIFY', `${sourceLabel}: final decompressed bytes differ from rebuilt RTDP`);
  return {
    buffer: packed.buffer,
    report: {
      format: 'LZ10-RTDP-tree-rebuild-v1',
      sourceLabel,
      inputSha256: sha256(templatePacked),
      outputSha256: sha256(packed.buffer),
      inputSize: templatePacked.length,
      outputSize: packed.buffer.length,
      unpackedInputSha256: sha256(detail.output),
      unpackedOutputSha256: sha256(tree.buffer),
      byteExact: packed.buffer.equals(templatePacked),
      lz10: packed.report,
      rtdpTree: tree.report,
    },
  };
}

function rebuildContainer(template, edits, options = {}) {
  if (hasMagic(template, RTDP_MAGIC)) return rebuildRtdpTree(template, edits, options);
  if (template.length >= 1 && template[0] === 0x10) return rebuildCxd(template, edits, options);
  throw new ContainerError('UNSUPPORTED_CONTAINER', `${options.sourceLabel || '<container>'}: expected RTDP or LZ10`);
}

function inspectContainer(buffer, sourceLabel = '<container>') {
  if (hasMagic(buffer, RTDP_MAGIC)) {
    const parsed = parseRtdp(buffer, sourceLabel);
    const standard = analyzeStandardLayout(buffer, parsed);
    return {
      wrapper: 'RTDP',
      sourceLabel,
      size: buffer.length,
      sha256: sha256(buffer),
      eoh: parsed.eoh,
      entryCount: parsed.entryCount,
      sizeField: parsed.sizeField,
      headerUnknownHex: parsed.headerUnknownHex,
      policy: standard.standard
        ? 'standard-resize'
        : analyzeZeroSizeAnchorLayout(buffer, parsed).supported
          ? 'zero-size-anchor-resize'
          : isGameoverTemplate(parsed)
            ? 'gameover-template'
            : 'nonstandard-fixed-size-only',
      standardReasons: standard.reasons,
      entries: parsed.entries.map((entry) => ({
        index: entry.index,
        name: entry.name,
        nameRawHex: entry.nameRaw.toString('hex'),
        size: entry.size,
        relativeOffset: entry.relativeOffset,
        decodedSha256: sha256(xor55(buffer.subarray(entry.absoluteOffset, entry.endOffset))),
      })),
    };
  }
  if (buffer.length && buffer[0] === 0x10) {
    const detail = decompressLz10Detailed(buffer, sourceLabel);
    return {
      wrapper: 'LZ10',
      sourceLabel,
      packedSize: buffer.length,
      packedSha256: sha256(buffer),
      unpackedSize: detail.output.length,
      unpackedSha256: sha256(detail.output),
      consumedBytes: detail.consumedBytes,
      trailingBytesHex: detail.trailingBytes.toString('hex'),
      inner: hasMagic(detail.output, RTDP_MAGIC) ? inspectContainer(detail.output, `${sourceLabel}#unpacked`) : { wrapper: 'unknown' },
    };
  }
  throw new ContainerError('UNSUPPORTED_CONTAINER', `${sourceLabel}: expected RTDP or LZ10`);
}

function loadEditManifest(manifestPath) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  assert(manifest && manifest.format === 'arf-container-edits-v1', 'MANIFEST_FORMAT', 'Expected format arf-container-edits-v1');
  assert(Array.isArray(manifest.edits), 'MANIFEST_EDITS', 'Manifest edits must be an array');
  const base = path.dirname(path.resolve(manifestPath));
  return manifest.edits.map((edit, index) => {
    assert(typeof edit.replacementFile === 'string', 'MANIFEST_REPLACEMENT', `Edit ${index} needs replacementFile`);
    const resolved = path.resolve(base, edit.replacementFile);
    return {
      entryPath: edit.entryPath,
      expectedSha256: edit.expectedSha256,
      data: fs.readFileSync(resolved),
    };
  });
}

function usage() {
  process.stdout.write([
    'Usage:',
    '  node container_tool.js inspect <source>',
    '  node container_tool.js lz10-decompress <source> <output>',
    '  node container_tool.js lz10-compress <source> <output>',
    '  node container_tool.js rewrap-cxd <source.cxd> <replacement-unpacked> <expected-unpacked-sha256> <output.cxd> <report.json>',
    '  node container_tool.js rebuild <source> <edits.json> <output> <report.json>',
    '',
    'edits.json format: arf-container-edits-v1; every edit uses an entry-index',
    'path, expected decoded SHA-256, and replacementFile relative to the JSON.',
  ].join('\n'));
}

function main(argv = process.argv.slice(2)) {
  const [command, arg1, arg2, arg3, arg4, arg5] = argv;
  if (!command || command === '-h' || command === '--help') {
    usage();
    return;
  }
  if (command === 'inspect') {
    assert(arg1, 'CLI_ARGUMENTS', 'inspect needs <source>');
    process.stdout.write(`${JSON.stringify(inspectContainer(fs.readFileSync(arg1), path.resolve(arg1)), null, 2)}\n`);
    return;
  }
  if (command === 'lz10-decompress') {
    assert(arg1 && arg2, 'CLI_ARGUMENTS', 'lz10-decompress needs <source> <output>');
    const output = decompressLz10(fs.readFileSync(arg1), path.resolve(arg1));
    fs.mkdirSync(path.dirname(path.resolve(arg2)), { recursive: true });
    fs.writeFileSync(arg2, output);
    process.stdout.write(`${JSON.stringify({ output: path.resolve(arg2), size: output.length, sha256: sha256(output) }, null, 2)}\n`);
    return;
  }
  if (command === 'lz10-compress') {
    assert(arg1 && arg2, 'CLI_ARGUMENTS', 'lz10-compress needs <source> <output>');
    const input = fs.readFileSync(arg1);
    const output = compressLz10(input);
    fs.mkdirSync(path.dirname(path.resolve(arg2)), { recursive: true });
    fs.writeFileSync(arg2, output);
    process.stdout.write(`${JSON.stringify({ output: path.resolve(arg2), packedSize: output.length, unpackedSize: input.length, sha256: sha256(output) }, null, 2)}\n`);
    return;
  }
  if (command === 'rewrap-cxd') {
    assert(arg1 && arg2 && arg3 && arg4 && arg5, 'CLI_ARGUMENTS', 'rewrap-cxd needs <source.cxd> <replacement-unpacked> <expected-unpacked-sha256> <output.cxd> <report.json>');
    const source = fs.readFileSync(arg1);
    const replacement = fs.readFileSync(arg2);
    const result = rebuildCxdPayload(source, replacement, {
      sourceLabel: path.resolve(arg1),
      expectedUnpackedSha256: arg3,
    });
    fs.mkdirSync(path.dirname(path.resolve(arg4)), { recursive: true });
    fs.mkdirSync(path.dirname(path.resolve(arg5)), { recursive: true });
    fs.writeFileSync(arg4, result.buffer);
    fs.writeFileSync(arg5, `${JSON.stringify(result.report, null, 2)}\n`, 'utf8');
    process.stdout.write(`${JSON.stringify({ output: path.resolve(arg4), report: path.resolve(arg5), ...result.report }, null, 2)}\n`);
    return;
  }
  if (command === 'rebuild') {
    assert(arg1 && arg2 && arg3 && arg4, 'CLI_ARGUMENTS', 'rebuild needs <source> <edits.json> <output> <report.json>');
    const source = fs.readFileSync(arg1);
    const edits = loadEditManifest(arg2);
    const result = rebuildContainer(source, edits, { sourceLabel: path.resolve(arg1) });
    fs.mkdirSync(path.dirname(path.resolve(arg3)), { recursive: true });
    fs.mkdirSync(path.dirname(path.resolve(arg4)), { recursive: true });
    fs.writeFileSync(arg3, result.buffer);
    fs.writeFileSync(arg4, `${JSON.stringify(result.report, null, 2)}\n`, 'utf8');
    process.stdout.write(`${JSON.stringify({ output: path.resolve(arg3), report: path.resolve(arg4), ...result.report }, null, 2)}\n`);
    return;
  }
  throw new ContainerError('CLI_COMMAND', `Unknown command ${command}`);
}

module.exports = {
  ALIGNMENT,
  ContainerError,
  GAMEOVER_SIGNATURE,
  alignUp,
  analyzeStandardLayout,
  analyzeZeroSizeAnchorLayout,
  compressLz10,
  decodeRtdpEntries,
  decompressLz10,
  decompressLz10Detailed,
  inspectContainer,
  isGameoverTemplate,
  normalizeEdits,
  parseRtdp,
  rebuildContainer,
  rebuildCxd,
  rebuildCxdPayload,
  rebuildLz10,
  rebuildRtdp,
  rebuildRtdpTree,
  sha256,
  xor55,
};

if (require.main === module) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`${error.stack || error}\n`);
    process.exitCode = 1;
  }
}
