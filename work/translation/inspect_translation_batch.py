import json
import pathlib
import sys


batch = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
end = int(sys.argv[3]) if len(sys.argv) > 3 else 200
path = pathlib.Path(f"work/translation/tm_v2/batches/source/{batch}.jsonl")
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

for index, row in enumerate(rows[start - 1 : end], start):
    print(f"## {index} {row['tm_id']}")
    print(f"JA: {row['source_text']}")
    for context in row.get("sample_contexts", [])[:2]:
        print(
            "CTX: "
            f"{context.get('logical_locator', '')} | "
            f"PREV={context.get('previous_source', '')} | "
            f"NEXT={context.get('next_source', '')}"
        )
    print()
