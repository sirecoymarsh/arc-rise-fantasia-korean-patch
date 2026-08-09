#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const childProcess = require('child_process');

const HERE = __dirname;
const TOOL = path.join(HERE, 'rtdp_tool.js');

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function copyTree(source, destination) {
  fs.mkdirSync(destination, { recursive: true });
  for (const child of fs.readdirSync(source, { withFileTypes: true })) {
    const from = path.join(source, child.name);
    const to = path.join(destination, child.name);
    if (child.isDirectory()) copyTree(from, to);
    else if (child.isFile()) fs.copyFileSync(from, to);
  }
}

function runTool(args, expectSuccess = true) {
  const result = childProcess.spawnSync(process.execPath, [TOOL, ...args], {
    encoding: 'utf8',
    windowsHide: true,
  });
  if (expectSuccess && result.status !== 0) {
    throw new Error(`rtdp_tool failed (${result.status}): ${result.stderr || result.stdout}`);
  }
  return result;
}

function compareBuffers(left, right, sampleLimit = 16) {
  let differentByteCount = Math.abs(left.length - right.length);
  const differentOffsets = [];
  const common = Math.min(left.length, right.length);
  for (let offset = 0; offset < common; offset += 1) {
    if (left[offset] !== right[offset]) {
      differentByteCount += 1;
      if (differentOffsets.length < sampleLimit) {
        differentOffsets.push({ offset, left: left[offset], right: right[offset] });
      }
    }
  }
  return { differentByteCount, differentOffsets };
}

function fixedCase(extractionRelative, repackedRelative) {
  const extraction = path.join(HERE, extractionRelative);
  const manifest = JSON.parse(fs.readFileSync(path.join(extraction, 'manifest.json'), 'utf8'));
  const source = fs.readFileSync(manifest.sourceArchive);
  const repackedPath = path.join(HERE, repackedRelative);
  const repacked = fs.readFileSync(repackedPath);
  const comparison = compareBuffers(source, repacked);
  return {
    extractionDirectory: extraction,
    sourceArchive: manifest.sourceArchive,
    repackedArchive: repackedPath,
    sourceSize: source.length,
    repackedSize: repacked.length,
    sourceSha256: sha256(source),
    repackedSha256: sha256(repacked),
    byteExact: comparison.differentByteCount === 0,
    ...comparison,
  };
}

function main() {
  const fixedLayoutCases = [
    fixedCase('fixtures/fc_00_001', 'fixtures/fc_00_001.repacked.vol'),
    fixedCase('fixtures/btl_gameover', 'fixtures/btl_gameover.repacked.vol'),
    fixedCase('fixtures/system', 'fixtures/system.repacked.vol'),
    fixedCase('fixtures/system_nested_enm_symbole', 'fixtures/system_nested_enm_symbole.repacked.vol'),
  ];

  // Prove that decoded -> XOR 0x55 -> archive -> decoded is reversible for a
  // same-size edit.  The edit is to an unused zero byte in the extracted BSCR
  // header padding; no game or original file is touched.
  const sourceExtraction = path.join(HERE, 'fixtures', 'fc_00_001');
  const mutationExtraction = path.join(HERE, 'fixtures', 'fc_00_001_same_size_mutation');
  copyTree(sourceExtraction, mutationExtraction);
  const mutationManifest = JSON.parse(fs.readFileSync(path.join(mutationExtraction, 'manifest.json'), 'utf8'));
  const mutationPayloadPath = path.join(mutationExtraction, ...mutationManifest.entries[0].payloadFile.split('/'));
  const mutationPayload = fs.readFileSync(mutationPayloadPath);
  const payloadEditOffset = 31;
  const payloadBefore = mutationPayload[payloadEditOffset];
  const payloadAfter = payloadBefore ^ 0x01;
  mutationPayload[payloadEditOffset] = payloadAfter;
  fs.writeFileSync(mutationPayloadPath, mutationPayload);

  const mutationArchivePath = path.join(HERE, 'fixtures', 'fc_00_001_same_size_mutation.repacked.vol');
  runTool(['repack', mutationExtraction, mutationArchivePath]);
  const reextractedDirectory = path.join(HERE, 'fixtures', 'fc_00_001_same_size_mutation.reextracted');
  runTool(['extract', mutationArchivePath, reextractedDirectory]);
  const reextractedManifest = JSON.parse(fs.readFileSync(path.join(reextractedDirectory, 'manifest.json'), 'utf8'));
  const reextractedPayload = fs.readFileSync(path.join(reextractedDirectory, ...reextractedManifest.entries[0].payloadFile.split('/')));
  const originalArchive = fs.readFileSync(mutationManifest.sourceArchive);
  const mutationArchive = fs.readFileSync(mutationArchivePath);
  const archiveComparison = compareBuffers(originalArchive, mutationArchive);
  const expectedStoredOffset = mutationManifest.entries[0].absoluteOffset + payloadEditOffset;
  const sameSizeMutation = {
    sourceArchive: mutationManifest.sourceArchive,
    extractionDirectory: mutationExtraction,
    repackedArchive: mutationArchivePath,
    reextractedDirectory,
    payloadEditOffset,
    expectedStoredArchiveOffset: expectedStoredOffset,
    decodedByteBefore: payloadBefore,
    decodedByteAfter: payloadAfter,
    storedByteBefore: originalArchive[expectedStoredOffset],
    storedByteAfter: mutationArchive[expectedStoredOffset],
    xorKey: '0x55',
    xorRelationBefore: (payloadBefore ^ 0x55) === originalArchive[expectedStoredOffset],
    xorRelationAfter: (payloadAfter ^ 0x55) === mutationArchive[expectedStoredOffset],
    archiveSizePreserved: originalArchive.length === mutationArchive.length,
    archiveDifference: archiveComparison,
    reextractedPayloadSha256: sha256(reextractedPayload),
    editedPayloadSha256: sha256(mutationPayload),
    editedPayloadRecoveredExactly: reextractedPayload.equals(mutationPayload),
  };

  // Prove the safety guard: a length change is rejected rather than silently
  // invalidating offsets or the archive size field.
  const resizeExtraction = path.join(HERE, 'fixtures', 'fc_00_001_resize_rejection');
  copyTree(sourceExtraction, resizeExtraction);
  const resizeManifest = JSON.parse(fs.readFileSync(path.join(resizeExtraction, 'manifest.json'), 'utf8'));
  const resizePayloadPath = path.join(resizeExtraction, ...resizeManifest.entries[0].payloadFile.split('/'));
  fs.appendFileSync(resizePayloadPath, Buffer.from([0]));
  const resizeAttempt = runTool([
    'repack',
    resizeExtraction,
    path.join(HERE, 'fixtures', 'fc_00_001_resize_should_not_exist.vol'),
  ], false);
  const resizeGuard = {
    extractionDirectory: resizeExtraction,
    originalPayloadSize: resizeManifest.entries[0].size,
    editedPayloadSize: fs.statSync(resizePayloadPath).size,
    processExitCode: resizeAttempt.status,
    rejected: resizeAttempt.status !== 0,
    stderr: (resizeAttempt.stderr || '').trim(),
    outputArchiveExists: fs.existsSync(path.join(HERE, 'fixtures', 'fc_00_001_resize_should_not_exist.vol')),
  };

  const proof = {
    generatedAt: new Date().toISOString(),
    tool: TOOL,
    fixedLayoutCases,
    allFixedLayoutCasesByteExact: fixedLayoutCases.every((item) => item.byteExact),
    sameSizeMutation,
    resizeGuard,
  };
  const output = path.join(HERE, 'roundtrip_proof.json');
  fs.writeFileSync(output, `${JSON.stringify(proof, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify(proof, null, 2)}\n`);
}

main();

