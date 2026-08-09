import fs from "node:fs";

const py = fs.readFileSync("work/write_batch0013.py", "utf8");
const start = py.indexOf("translations = [") + "translations = ".length;
const end = py.indexOf("\n\nrows =", start);
const translations = Function(`return ${py.slice(start, end)}`)();

const sourcePath = "work/translation/tm_v2/batches/source/batch_0013.jsonl";
const outputPath = "work/translation/drafts/batch_0013.jsonl";
const rows = fs.readFileSync(sourcePath, "utf8").trimEnd().split(/\r?\n/).map(JSON.parse);

if (rows.length !== translations.length) {
  throw new Error(`row/translation count mismatch: ${rows.length} != ${translations.length}`);
}

for (let i = 0; i < rows.length; i += 1) {
  rows[i].translation_ko = translations[i];
}

fs.writeFileSync(outputPath, rows.map((row) => JSON.stringify(row)).join("\n") + "\n", "utf8");
process.stdout.write(String(rows.length));
