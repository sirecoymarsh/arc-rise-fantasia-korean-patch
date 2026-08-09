import json
from pathlib import Path

IDS = {
    "ARF-TM-019ABE60D53A27F0D5E8",
    "ARF-TM-0017BC25A464A91C416E",
    "ARF-TM-01D1DE213E0797C72331",
}

for path in sorted(Path("work/translation/reviewed").glob("batch_*.jsonl")):
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        unit = json.loads(line)
        if unit.get("tm_id") in IDS:
            print(path, line_no, json.dumps(unit, ensure_ascii=False, indent=2))

audit = json.loads(
    Path("work/translation/boundary_audit/batches_0001_0002.json").read_text(
        encoding="utf-8"
    )
)
for unit in audit["units"]:
    if unit.get("tm_id") in IDS:
        print("AUDIT", json.dumps(unit, ensure_ascii=False, indent=2))
