import json
from pathlib import Path


root = Path(__file__).resolve().parent.parent
tm_path = root / "work/translation/current/translation_memory_draft.json"
review_path = root / "work/translation/reviewed/batch_0005.jsonl"
output_path = root / "work/translation/current/translation_memory_with_batch5_review_temp.json"

tm = json.loads(tm_path.read_text(encoding="utf-8"))
reviews = {
    row["tm_id"]: row
    for row in (
        json.loads(line) for line in review_path.read_text(encoding="utf-8").splitlines()
    )
}
matched = 0
for unit in tm["units"]:
    review = reviews.get(unit["tm_id"])
    if review is None:
        continue
    assert unit["source_text"] == review["source_text"]
    unit["translation_ko"] = review["translation_ko"]
    unit["status"] = "translated"
    unit["review_status"] = "approved"
    unit["translator"] = "Codex internal model"
    unit["reviewer"] = "/root/review_batch_0005"
    matched += 1

assert matched == len(reviews) == 200
output_path.write_text(json.dumps(tm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(output_path)
