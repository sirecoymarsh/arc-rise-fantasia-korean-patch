const fs = require("fs");
const path = require("path");

const pythonWriter = fs.readFileSync(
  path.join("work", "translation", "write_draft_batch0024.py"),
  "utf8",
);
const match = pythonWriter.match(
  /TRANSLATIONS = \{([\s\S]*?)\n\}\n\n\nsource_path/,
);
if (!match) {
  throw new Error("Could not read batch_0024 translation table");
}

const translations = Function(`"use strict"; return ({${match[1]}});`)();
const sourcePath = path.join(
  "work",
  "translation",
  "tm_v2",
  "batches",
  "source",
  "batch_0024.jsonl",
);
const outputPath = path.join(
  "work",
  "translation",
  "drafts",
  "batch_0024.jsonl",
);
const rows = fs
  .readFileSync(sourcePath, "utf8")
  .split(/\r?\n/)
  .filter((line) => line.length > 0)
  .map((line) => JSON.parse(line));

if (rows.length !== 200 || Object.keys(translations).length !== 200) {
  throw new Error("batch_0024 translation table is incomplete");
}

for (let index = 1; index <= rows.length; index += 1) {
  rows[index - 1].translation_ko = translations[index];
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(
  outputPath,
  `${rows.map((row) => JSON.stringify(row)).join("\n")}\n`,
  "utf8",
);
process.stdout.write(
  `${JSON.stringify({ batch: "batch_0024", completed: rows.length })}\n`,
);
