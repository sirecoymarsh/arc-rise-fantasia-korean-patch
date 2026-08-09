import json
from pathlib import Path

src_path = Path("work/translation/tm_v2/batches/source/batch_0007.jsonl")
draft_path = Path("work/translation/drafts/batch_0007.jsonl")
src = [json.loads(line) for line in src_path.read_text(encoding="utf-8").splitlines() if line.strip()]
draft = {o["tm_id"]: o for o in (json.loads(line) for line in draft_path.read_text(encoding="utf-8").splitlines() if line.strip())}

out = []
for i, item in enumerate(src, 1):
    d = draft[item["tm_id"]]
    ctx = item.get("sample_contexts") or []
    first = ctx[0] if ctx else {}
    out.extend([
        f"## {i:03d} {item['tm_id']}",
        f"SRC: {item['source_text']}",
        f"DRA: {d.get('translation_ko', '')}",
        f"LOC: {first.get('logical_locator', '')} @{first.get('offset_hex', '')}",
        f"PREV: {first.get('previous_source', '')}",
        f"NEXT: {first.get('next_source', '')}",
        f"TOK: {item.get('control_tokens', [])}",
        "",
    ])

Path("work/translation/reviews/batch_0007_inspect.txt").write_text("\n".join(out), encoding="utf-8")

compact = []
for i, item in enumerate(src, 1):
    d = draft[item["tm_id"]]
    first = (item.get("sample_contexts") or [{}])[0]
    esc = lambda s: str(s).replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    compact.append(
        "\t".join(
            [
                f"{i:03d}",
                item["tm_id"],
                esc(item["source_text"]),
                esc(d.get("translation_ko", "")),
                esc(first.get("logical_locator", "")),
                esc(first.get("previous_source", "")),
                esc(first.get("next_source", "")),
            ]
        )
    )
Path("work/translation/reviews/batch_0007_inspect.tsv").write_text("\n".join(compact) + "\n", encoding="utf-8")
