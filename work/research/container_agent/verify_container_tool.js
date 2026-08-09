#!/usr/bin/env node
'use strict';

/* Reproducible verification suite for container_tool.js. */

const fs = require('fs');
const path = require('path');
const tool = require('./container_tool.js');

const HERE = __dirname;
const WORKSPACE = path.resolve(HERE, '..', '..', '..');
const DATA_ROOT = path.join(WORKSPACE, 'work', 'disc_extracted', 'DATA', 'files');
const OUTPUT_JSON = path.join(HERE, 'verification.json');
const REPRO_JSON = path.join(HERE, 'reproduction.json');

function check(condition, message) {
  if (!condition) throw new Error(`VERIFY: ${message}`);
}

function relativeData(filePath) {
  return path.relative(DATA_ROOT, filePath).replace(/\\/g, '/');
}

function walkFiles(root, predicate) {
  const result = [];
  const stack = [root];
  while (stack.length) {
    const current = stack.pop();
    for (const dirent of fs.readdirSync(current, { withFileTypes: true })) {
      const full = path.join(current, dirent.name);
      if (dirent.isDirectory()) stack.push(full);
      else if (dirent.isFile() && predicate(full)) result.push(full);
    }
  }
  return result.sort((a, b) => a.localeCompare(b, 'en'));
}

function decodedAt(container, index) {
  const parsed = tool.parseRtdp(container);
  return tool.xor55(container.subarray(parsed.entries[index].absoluteOffset, parsed.entries[index].endOffset));
}

function semanticRtdpSummary(beforeBuffer, afterBuffer) {
  const before = tool.parseRtdp(beforeBuffer, 'before');
  const after = tool.parseRtdp(afterBuffer, 'after');
  return {
    entryCountPreserved: before.entryCount === after.entryCount,
    eohPreserved: before.eoh === after.eoh,
    headerUnknownPreserved: before.headerUnknown.equals(after.headerUnknown),
    headerPaddingPreserved: before.headerPadding.equals(after.headerPadding),
    rawNamesPreserved: before.entries.every((entry, index) => entry.nameRaw.equals(after.entries[index].nameRaw)),
    beforeOffsets: before.entries.map((entry) => entry.relativeOffset),
    afterOffsets: after.entries.map((entry) => entry.relativeOffset),
    beforeSizes: before.entries.map((entry) => entry.size),
    afterSizes: after.entries.map((entry) => entry.size),
    beforeDecodedSha256: before.entries.map((entry) => tool.sha256(decodedAt(beforeBuffer, entry.index))),
    afterDecodedSha256: after.entries.map((entry) => tool.sha256(decodedAt(afterBuffer, entry.index))),
  };
}

function verifyCorpusNoop() {
  const files = walkFiles(DATA_ROOT, (file) => file.toLowerCase().endsWith('.vol'));
  let archiveCount = 0;
  let physicalCount = 0;
  let nestedCount = 0;
  let entryCount = 0;
  let totalArchiveBytes = 0;
  let standardCount = 0;
  let gameoverCount = 0;
  let otherNonstandardCount = 0;
  const failures = [];

  function verifyArchive(buffer, label, depth) {
    archiveCount += 1;
    if (depth === 0) physicalCount += 1;
    else nestedCount += 1;
    totalArchiveBytes += buffer.length;
    const parsed = tool.parseRtdp(buffer, label);
    entryCount += parsed.entryCount;
    const standard = tool.analyzeStandardLayout(buffer, parsed);
    if (standard.standard) standardCount += 1;
    else if (tool.isGameoverTemplate(parsed)) gameoverCount += 1;
    else otherNonstandardCount += 1;
    const payloads = tool.decodeRtdpEntries(buffer, parsed);
    const rebuilt = tool.rebuildRtdp(buffer, payloads, { sourceLabel: label });
    if (!rebuilt.buffer.equals(buffer) || rebuilt.report.policy !== 'exact-noop') {
      failures.push({ label, depth, inputSha256: tool.sha256(buffer), outputSha256: tool.sha256(rebuilt.buffer), policy: rebuilt.report.policy });
    }
    payloads.forEach((payload, index) => {
      if (payload.length >= 4 && payload.subarray(0, 4).toString('ascii') === 'RTDP') {
        verifyArchive(payload, `${label}::${String(index).padStart(4, '0')}:${parsed.entries[index].name}`, depth + 1);
      }
    });
  }

  for (const file of files) verifyArchive(fs.readFileSync(file), relativeData(file), 0);
  check(failures.length === 0, `${failures.length} corpus no-op failures`);
  return {
    physicalVolFiles: files.length,
    physicalArchiveCount: physicalCount,
    nestedArchiveCount: nestedCount,
    totalArchiveCount: archiveCount,
    totalEntryCount: entryCount,
    totalArchiveBytes,
    standardLayoutCount: standardCount,
    recognizedGameoverTemplateCount: gameoverCount,
    otherNonstandardCount,
    byteExactNoopCount: archiveCount,
    failureCount: failures.length,
    failures,
  };
}

function verifyStandardResize() {
  const sourcePath = path.join(DATA_ROOT, 'Event', 'fc', 'fc_00_001.vol');
  const source = fs.readFileSync(sourcePath);
  const parsed = tool.parseRtdp(source, relativeData(sourcePath));
  const payloads = tool.decodeRtdpEntries(source, parsed);
  const replacement = Buffer.concat([payloads[0], Buffer.alloc(37, 0)]);
  payloads[0] = replacement;
  const rebuilt = tool.rebuildRtdp(source, payloads, { sourceLabel: relativeData(sourcePath) });
  check(rebuilt.report.policy === 'standard-resize', 'standard resize did not select standard-resize policy');
  const after = tool.parseRtdp(rebuilt.buffer, 'standard controlled resize');
  check(tool.analyzeStandardLayout(rebuilt.buffer, after).standard, 'standard resize output not canonical');
  check(decodedAt(rebuilt.buffer, 0).equals(replacement), 'standard resize payload mismatch');
  const semantic = semanticRtdpSummary(source, rebuilt.buffer);
  check(semantic.entryCountPreserved && semantic.eohPreserved && semantic.headerUnknownPreserved && semantic.headerPaddingPreserved && semantic.rawNamesPreserved, 'standard metadata preservation failed');
  return {
    source: relativeData(sourcePath),
    sourceSize: source.length,
    sourceSha256: tool.sha256(source),
    outputSize: rebuilt.buffer.length,
    outputSha256: tool.sha256(rebuilt.buffer),
    policy: rebuilt.report.policy,
    targetEntryIndex: 0,
    appendedFixtureBytes: 37,
    reparsed: true,
    canonicalAlignmentVerified: true,
    reextractedPayloadEqualsReplacement: true,
    semantic,
  };
}

function verifyFixedSizeEdit() {
  const sourcePath = path.join(DATA_ROOT, 'Event', 'fc', 'fc_00_001.vol');
  const source = fs.readFileSync(sourcePath);
  const parsed = tool.parseRtdp(source);
  const payloads = tool.decodeRtdpEntries(source, parsed);
  const replacement = Buffer.from(payloads[0]);
  replacement[31] ^= 0x01;
  payloads[0] = replacement;
  const result = tool.rebuildRtdp(source, payloads, { sourceLabel: relativeData(sourcePath) });
  check(result.report.policy === 'fixed-layout', 'same-size edit did not use fixed-layout');
  const diffs = [];
  for (let i = 0; i < source.length; i += 1) if (source[i] !== result.buffer[i]) diffs.push(i);
  check(diffs.length === 1, `expected exactly one stored-byte difference, got ${diffs.length}`);
  check(decodedAt(result.buffer, 0).equals(replacement), 'same-size payload re-extraction mismatch');
  return {
    source: relativeData(sourcePath),
    policy: result.report.policy,
    changedDecodedOffset: 31,
    changedArchiveOffsets: diffs,
    xor55Verified: source[diffs[0]] === (payloads[0][31] ^ 0x01 ^ 0x55) && result.buffer[diffs[0]] === (payloads[0][31] ^ 0x55),
    reextractedPayloadEqualsReplacement: true,
  };
}

function verifyGameoverPolicy() {
  const sourcePath = path.join(DATA_ROOT, 'Btl', 'btl_gameover.vol');
  const source = fs.readFileSync(sourcePath);
  const parsed = tool.parseRtdp(source, relativeData(sourcePath));
  check(tool.isGameoverTemplate(parsed), 'gameover signature not recognized');
  const payloads = tool.decodeRtdpEntries(source, parsed);
  const replacement = Buffer.concat([payloads[0], Buffer.alloc(32, 0)]);
  payloads[0] = replacement;
  const rebuilt = tool.rebuildRtdp(source, payloads, { sourceLabel: relativeData(sourcePath) });
  check(rebuilt.report.policy === 'gameover-template', 'gameover resize did not use template policy');
  check(rebuilt.buffer.length === source.length, 'gameover template file size changed');
  const semantic = semanticRtdpSummary(source, rebuilt.buffer);
  check(semantic.beforeOffsets.every((value, index) => semantic.afterOffsets[index] === value), 'gameover slot offsets moved');
  check(decodedAt(rebuilt.buffer, 0).equals(replacement), 'gameover replacement mismatch');
  for (let i = 1; i < parsed.entryCount; i += 1) {
    check(semantic.beforeDecodedSha256[i] === semantic.afterDecodedSha256[i], `gameover unaffected entry ${i} changed`);
  }

  const overflowPayloads = tool.decodeRtdpEntries(source, parsed);
  const slotCapacity = parsed.entries[1].relativeOffset - parsed.entries[0].relativeOffset;
  overflowPayloads[0] = Buffer.concat([overflowPayloads[0], Buffer.alloc(slotCapacity - overflowPayloads[0].length + 1, 0)]);
  let overflowRejection;
  try {
    tool.rebuildRtdp(source, overflowPayloads, { sourceLabel: relativeData(sourcePath) });
  } catch (error) {
    overflowRejection = { code: error.code, message: error.message };
  }
  check(overflowRejection && overflowRejection.code === 'GAMEOVER_SLOT_OVERFLOW', 'gameover slot overflow was not explicitly rejected');

  return {
    source: relativeData(sourcePath),
    sourceSize: source.length,
    sourceSha256: tool.sha256(source),
    recognizedTemplate: true,
    policy: rebuilt.report.policy,
    outputSize: rebuilt.buffer.length,
    outputSha256: tool.sha256(rebuilt.buffer),
    targetEntryIndex: 0,
    targetSlotCapacity: slotCapacity,
    targetOldSize: parsed.entries[0].size,
    targetNewSize: replacement.length,
    offsetsPreserved: true,
    otherEntryHashesPreserved: true,
    reextractedPayloadEqualsReplacement: true,
    overflowRejection,
    semantic,
  };
}

function verifyUnknownNonstandardRejection() {
  const sourcePath = path.join(DATA_ROOT, 'Event', 'fc', 'fc_00_001.vol');
  const canonical = fs.readFileSync(sourcePath);
  const parsed = tool.parseRtdp(canonical);
  const inserted = Buffer.concat([
    canonical.subarray(0, parsed.eoh),
    Buffer.alloc(0x20, 0),
    canonical.subarray(parsed.eoh),
  ]);
  inserted.writeUInt32BE(parsed.eoh + 0x20, 0x04);
  inserted.writeUInt32BE(inserted.length, 0x0c);
  const customParsed = tool.parseRtdp(inserted, 'synthetic-nonstandard-template');
  check(!tool.analyzeStandardLayout(inserted, customParsed).standard, 'synthetic archive unexpectedly standard');
  const exact = tool.rebuildRtdp(inserted, tool.decodeRtdpEntries(inserted, customParsed), { sourceLabel: 'synthetic-nonstandard-template' });
  check(exact.buffer.equals(inserted), 'unknown nonstandard no-op was not exact');
  const payloads = tool.decodeRtdpEntries(inserted, customParsed);
  payloads[0] = Buffer.concat([payloads[0], Buffer.from([0])]);
  let rejection;
  try {
    tool.rebuildRtdp(inserted, payloads, { sourceLabel: 'synthetic-nonstandard-template' });
  } catch (error) {
    rejection = { code: error.code, message: error.message, details: error.details };
  }
  check(rejection && rejection.code === 'UNSUPPORTED_NONSTANDARD_RESIZE', 'unknown nonstandard resize was not explicitly rejected');
  return {
    syntheticFrom: relativeData(sourcePath),
    eohDelta: 0x20,
    validRtdp: true,
    unchangedNoopByteExact: true,
    resizeRejection: rejection,
  };
}

function verifyLz10() {
  const samples = [
    path.join(DATA_ROOT, 'interface', 'tex_loc_title_jad_wtm.cxd'),
    path.join(DATA_ROOT, 'interface', 'data_map_aka_vol.cxd'),
    path.join(DATA_ROOT, 'Map', 'map_t_jad_00.cxd'),
  ];
  return samples.map((sourcePath) => {
    const packed = fs.readFileSync(sourcePath);
    const detail = tool.decompressLz10Detailed(packed, relativeData(sourcePath));
    const first = tool.compressLz10(detail.output);
    const second = tool.compressLz10(detail.output);
    const decoded = tool.decompressLz10(first, 'deterministic compressed sample');
    const noop = tool.rebuildLz10(packed, detail.output, { sourceLabel: relativeData(sourcePath) });
    check(first.equals(second), `${relativeData(sourcePath)} compressor output not deterministic`);
    check(decoded.equals(detail.output), `${relativeData(sourcePath)} decompression equality failed`);
    check(noop.buffer.equals(packed), `${relativeData(sourcePath)} LZ10 no-op not exact`);
    check([...detail.trailingBytes].every((byte) => byte === 0), `${relativeData(sourcePath)} has nonzero trailing bytes`);
    return {
      source: relativeData(sourcePath),
      originalPackedSize: packed.length,
      originalPackedSha256: tool.sha256(packed),
      unpackedSize: detail.output.length,
      unpackedSha256: tool.sha256(detail.output),
      originalConsumedBytes: detail.consumedBytes,
      originalTrailingPaddingHex: detail.trailingBytes.toString('hex'),
      deterministicPackedSize: first.length,
      deterministicPackedSha256: tool.sha256(first),
      repeatedCompressionByteEqual: true,
      decompressionEqualsInput: true,
      unchangedWrapperByteExact: true,
      outputAlignment: first.length % 4,
    };
  });
}

function verifyWholePayloadCxd() {
  const sourcePath = path.join(DATA_ROOT, 'interface', 'tex_loc_title_jad_wtm.cxd');
  const source = fs.readFileSync(sourcePath);
  const original = tool.decompressLz10(source, relativeData(sourcePath));
  check(original.subarray(0, 4).toString('ascii') === 'WTMD', 'whole-payload CXD sample is not WTMD');
  const replacement = Buffer.concat([original, Buffer.alloc(7, 0)]);
  const result = tool.rebuildCxdPayload(source, replacement, {
    sourceLabel: relativeData(sourcePath),
    expectedUnpackedSha256: tool.sha256(original),
  });
  const reextracted = tool.decompressLz10(result.buffer, 'whole-payload CXD output');
  check(reextracted.equals(replacement), 'whole-payload CXD decompression equality failed');
  let staleHashRejection;
  try {
    tool.rebuildCxdPayload(source, replacement, {
      sourceLabel: relativeData(sourcePath),
      expectedUnpackedSha256: '0'.repeat(64),
    });
  } catch (error) {
    staleHashRejection = { code: error.code, message: error.message, details: error.details };
  }
  check(staleHashRejection && staleHashRejection.code === 'CXD_HASH_MISMATCH', 'whole-payload CXD stale hash not rejected');
  return {
    source: relativeData(sourcePath),
    innerMagic: 'WTMD',
    inputPackedSize: source.length,
    inputPackedSha256: tool.sha256(source),
    outputPackedSize: result.buffer.length,
    outputPackedSha256: tool.sha256(result.buffer),
    inputUnpackedSize: original.length,
    inputUnpackedSha256: tool.sha256(original),
    outputUnpackedSize: replacement.length,
    outputUnpackedSha256: tool.sha256(replacement),
    reextractedSha256: tool.sha256(reextracted),
    decompressionEqualityVerified: true,
    staleHashRejection,
  };
}

function verifyCxdBottomUp() {
  const sourcePath = path.join(DATA_ROOT, 'interface', 'data_map_aka_vol.cxd');
  const source = fs.readFileSync(sourcePath);
  const unpackedBefore = tool.decompressLz10(source, relativeData(sourcePath));
  const parsed = tool.parseRtdp(unpackedBefore, `${relativeData(sourcePath)}#unpacked`);
  const targetIndex = parsed.entries.find((entry) => entry.size > 0).index;
  const oldPayload = decodedAt(unpackedBefore, targetIndex);
  const replacement = Buffer.concat([oldPayload, Buffer.alloc(11, 0)]);
  const result = tool.rebuildCxd(source, [{
    entryPath: [targetIndex],
    expectedSha256: tool.sha256(oldPayload),
    data: replacement,
  }], { sourceLabel: relativeData(sourcePath) });
  const unpackedAfter = tool.decompressLz10(result.buffer, 'controlled CXD output');
  const afterParsed = tool.parseRtdp(unpackedAfter, 'controlled CXD inner RTDP');
  const extracted = decodedAt(unpackedAfter, targetIndex);
  check(extracted.equals(replacement), 'CXD bottom-up target mismatch');
  check(tool.analyzeStandardLayout(unpackedAfter, afterParsed).standard, 'CXD inner rebuilt RTDP not standard');
  check(tool.sha256(unpackedAfter) === result.report.unpackedOutputSha256, 'CXD decompressed output hash mismatch');
  const semantic = semanticRtdpSummary(unpackedBefore, unpackedAfter);
  return {
    source: relativeData(sourcePath),
    sourcePackedSize: source.length,
    sourcePackedSha256: tool.sha256(source),
    outputPackedSize: result.buffer.length,
    outputPackedSha256: tool.sha256(result.buffer),
    unpackedInputSize: unpackedBefore.length,
    unpackedInputSha256: tool.sha256(unpackedBefore),
    unpackedOutputSize: unpackedAfter.length,
    unpackedOutputSha256: tool.sha256(unpackedAfter),
    reportUnpackedOutputSha256: result.report.unpackedOutputSha256,
    decompressedOutputHashVerified: true,
    targetEntryIndex: targetIndex,
    targetOldSize: oldPayload.length,
    targetNewSize: replacement.length,
    targetOldSha256: tool.sha256(oldPayload),
    targetNewSha256: tool.sha256(replacement),
    targetReextractedSha256: tool.sha256(extracted),
    innerPolicy: result.report.rtdpTree.containerAuditBottomUp.at(-1).policy,
    lz10Policy: result.report.lz10.policy,
    semantic,
  };
}

function verifyNestedRtdpBottomUp() {
  const sourcePath = path.join(DATA_ROOT, 'Sys', 'system.vol');
  const source = fs.readFileSync(sourcePath);
  const outerParsed = tool.parseRtdp(source, relativeData(sourcePath));
  const outerPayloads = tool.decodeRtdpEntries(source, outerParsed);
  const nestedIndex = outerPayloads.findIndex((payload) => payload.length >= 4 && payload.subarray(0, 4).toString('ascii') === 'RTDP');
  check(nestedIndex >= 0, 'system.vol has no nested RTDP');
  const child = outerPayloads[nestedIndex];
  const childParsed = tool.parseRtdp(child, 'nested child');
  const leafIndex = childParsed.entries.find((entry) => entry.size > 0).index;
  const leaf = decodedAt(child, leafIndex);
  const replacement = Buffer.concat([leaf, Buffer.alloc(13, 0)]);
  const result = tool.rebuildRtdpTree(source, [{
    entryPath: [nestedIndex, leafIndex],
    expectedSha256: tool.sha256(leaf),
    data: replacement,
  }], { sourceLabel: relativeData(sourcePath) });
  const rebuiltChild = decodedAt(result.buffer, nestedIndex);
  const rebuiltLeaf = decodedAt(rebuiltChild, leafIndex);
  check(rebuiltLeaf.equals(replacement), 'nested bottom-up leaf mismatch');
  check(result.report.containerAuditBottomUp.length === 2, 'nested bottom-up expected two RTDP rebuild layers');
  check(result.report.containerAuditBottomUp[0].prefix.length === 1 && result.report.containerAuditBottomUp[1].prefix.length === 0, 'container audit is not bottom-up');
  const outerSemantic = semanticRtdpSummary(source, result.buffer);
  const innerSemantic = semanticRtdpSummary(child, rebuiltChild);
  return {
    source: relativeData(sourcePath),
    sourceSize: source.length,
    sourceSha256: tool.sha256(source),
    outputSize: result.buffer.length,
    outputSha256: tool.sha256(result.buffer),
    nestedEntryIndex: nestedIndex,
    nestedEntryName: outerParsed.entries[nestedIndex].name,
    leafEntryIndex: leafIndex,
    leafEntryName: childParsed.entries[leafIndex].name,
    leafOldSize: leaf.length,
    leafNewSize: replacement.length,
    leafOldSha256: tool.sha256(leaf),
    leafNewSha256: tool.sha256(replacement),
    leafReextractedSha256: tool.sha256(rebuiltLeaf),
    rebuildPoliciesBottomUp: result.report.containerAuditBottomUp.map((entry) => ({ prefix: entry.prefix, policy: entry.policy, inputSize: entry.inputSize, outputSize: entry.outputSize })),
    bottomUpOrderVerified: true,
    outerSemantic,
    innerSemantic,
  };
}

function verifyHashGuard() {
  const sourcePath = path.join(DATA_ROOT, 'Event', 'fc', 'fc_00_001.vol');
  const source = fs.readFileSync(sourcePath);
  const payload = decodedAt(source, 0);
  let rejection;
  try {
    tool.rebuildRtdpTree(source, [{
      entryPath: [0],
      expectedSha256: '0'.repeat(64),
      data: Buffer.from(payload),
    }], { sourceLabel: relativeData(sourcePath) });
  } catch (error) {
    rejection = { code: error.code, message: error.message, details: error.details };
  }
  check(rejection && rejection.code === 'EDIT_HASH_MISMATCH', 'expected-hash guard did not reject stale edit');
  return rejection;
}

function main() {
  const started = new Date().toISOString();
  const verification = {
    format: 'arf-container-verification-v1',
    scope: 'Outer containers only; no translation and no payload-format semantics.',
    started,
    nodeVersion: process.version,
    dataRoot: path.relative(WORKSPACE, DATA_ROOT).replace(/\\/g, '/'),
    tests: {},
  };
  const run = (name, fn) => {
    const begin = Date.now();
    process.stderr.write(`VERIFY ${name}...\n`);
    verification.tests[name] = fn();
    verification.tests[name].elapsedMs = Date.now() - begin;
    process.stderr.write(`PASS   ${name} (${verification.tests[name].elapsedMs} ms)\n`);
  };

  run('corpusUnchangedNoop', verifyCorpusNoop);
  run('fixedSizeXor55Edit', verifyFixedSizeEdit);
  run('standardControlledResize', verifyStandardResize);
  run('gameoverTemplatePolicy', verifyGameoverPolicy);
  run('unknownNonstandardRefusalBoundary', verifyUnknownNonstandardRejection);
  run('lz10DeterminismAndEquality', () => ({ samples: verifyLz10() }));
  run('wholePayloadCxdResize', verifyWholePayloadCxd);
  run('cxdBottomUpResize', verifyCxdBottomUp);
  run('nestedRtdpBottomUpResize', verifyNestedRtdpBottomUp);
  run('expectedHashGuard', () => ({ rejection: verifyHashGuard() }));

  verification.finished = new Date().toISOString();
  verification.result = 'PASS';
  fs.writeFileSync(OUTPUT_JSON, `${JSON.stringify(verification, null, 2)}\n`, 'utf8');

  const reproduction = {
    format: 'arf-container-reproduction-v1',
    generatedBy: path.relative(WORKSPACE, __filename).replace(/\\/g, '/'),
    tool: path.relative(WORKSPACE, path.join(HERE, 'container_tool.js')).replace(/\\/g, '/'),
    nodeVersion: process.version,
    commandFromWorkspaceRoot: 'node work/research/container_agent/verify_container_tool.js',
    immutableInputs: [
      'work/disc_extracted/DATA/files/**/*.vol',
      'work/disc_extracted/DATA/files/interface/tex_loc_title_jad_wtm.cxd',
      'work/disc_extracted/DATA/files/interface/data_map_aka_vol.cxd',
      'work/disc_extracted/DATA/files/Map/map_t_jad_00.cxd',
    ],
    writesOnly: [
      'work/research/container_agent/verification.json',
      'work/research/container_agent/reproduction.json',
    ],
    toolSha256: tool.sha256(fs.readFileSync(path.join(HERE, 'container_tool.js'))),
    verifierSha256: tool.sha256(fs.readFileSync(__filename)),
    verificationSha256: tool.sha256(fs.readFileSync(OUTPUT_JSON)),
    note: 'Controlled resizes are in-memory synthetic outer-container proofs; no source or extracted game file is modified.',
  };
  fs.writeFileSync(REPRO_JSON, `${JSON.stringify(reproduction, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({ result: verification.result, verification: OUTPUT_JSON, reproduction: REPRO_JSON }, null, 2)}\n`);
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
}
