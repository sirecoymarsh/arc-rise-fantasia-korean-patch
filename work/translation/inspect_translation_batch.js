const fs = require("fs");

const [batch, startArg, endArg] = process.argv.slice(2);
const start = Number(startArg);
const end = Number(endArg);
const file = `work/translation/tm_v2/batches/source/${batch}.jsonl`;
const rows = fs
  .readFileSync(file, "utf8")
  .split(/\r?\n/)
  .filter(Boolean)
  .map(JSON.parse);

for (let index = start; index <= Math.min(end, rows.length); index += 1) {
  const row = rows[index - 1];
  const context = row.sample_contexts?.[0] ?? {};
  process.stdout.write(
    `${index}\tSRC=${JSON.stringify(row.source_text)}` +
      `\tTOK=${JSON.stringify(row.control_tokens)}` +
      `\tPREV=${JSON.stringify(context.previous_source ?? "")}` +
      `\tNEXT=${JSON.stringify(context.next_source ?? "")}\n`,
  );
}
