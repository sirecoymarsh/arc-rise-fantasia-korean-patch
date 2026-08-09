const fs = require('fs');

const [batchId, startArg, endArg] = process.argv.slice(2);
const start = Number(startArg);
const end = Number(endArg);
const readJsonl = (file) => fs.readFileSync(file, 'utf8')
  .split(/\r?\n/).filter(Boolean).map(JSON.parse);

const source = readJsonl(`work/translation/tm_v2/batches/source/${batchId}.jsonl`);
const draft = readJsonl(`work/translation/drafts/${batchId}.jsonl`);

for (let index = start; index <= Math.min(end, source.length); index += 1) {
  const sourceRow = source[index - 1];
  const draftRow = draft[index - 1];
  const context = sourceRow.sample_contexts?.[0] ?? {};
  process.stdout.write([
    `### ${index} ${sourceRow.tm_id}`,
    `SRC ${JSON.stringify(sourceRow.source_text)}`,
    `KO  ${JSON.stringify(draftRow.translation_ko)}`,
    `PRE ${JSON.stringify(context.previous_source ?? '')}`,
    `NXT ${JSON.stringify(context.next_source ?? '')}`,
    '',
  ].join('\n'));
}
