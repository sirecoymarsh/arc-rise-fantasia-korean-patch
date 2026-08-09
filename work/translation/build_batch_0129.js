const fs = require('fs');

const py = fs.readFileSync('work/translation/build_batch_0129.py', 'utf8');
const marker = 'translations = ';
const start = py.indexOf(marker) + marker.length;
const endMarker = '\n\n\nsource_path = ';
const end = py.indexOf(endMarker, start);
const translations = eval(py.slice(start, end));

const sourcePath = 'work/translation/tm_v2/batches/source/batch_0129.jsonl';
const outputPath = 'work/translation/drafts/batch_0129.jsonl';
const rows = fs.readFileSync(sourcePath, 'utf8').trimEnd().split(/\r?\n/).map(JSON.parse);
if (rows.length !== translations.length) {
  throw new Error(`row/translation count mismatch: ${rows.length} != ${translations.length}`);
}
for (let i = 0; i < rows.length; i++) rows[i].translation_ko = translations[i];
fs.mkdirSync('work/translation/drafts', { recursive: true });
fs.writeFileSync(outputPath, rows.map(JSON.stringify).join('\n') + '\n', 'utf8');
