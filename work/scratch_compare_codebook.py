import json
from pathlib import Path

old = json.loads(Path("work/font/canonical_v1/codebook.json").read_text(encoding="utf-8"))
new = json.loads(Path("work/font/canonical_v1/codebook_next.json").read_text(encoding="utf-8"))
changed = [
    char
    for char, value in old["characters"].items()
    if new["characters"].get(char) != value
]
missing = [char for char in old["characters"] if char not in new["characters"]]
added = [char for char in new["characters"] if char not in old["characters"]]
print(
    json.dumps(
        {
            "old_assigned": old["assigned"],
            "new_assigned": new["assigned"],
            "changed": changed,
            "missing": missing,
            "added_count": len(added),
            "added": added,
            "reserved": new["reserved_source_pairs"],
            "available": new["available_after_reservations"],
        },
        ensure_ascii=False,
    )
)
if changed or missing:
    raise SystemExit(1)
