import json
from pathlib import Path


root = Path(__file__).resolve().parent.parent
source_path = root / "work/translation/tm_v2/batches/source/batch_0005.jsonl"
draft_path = root / "work/translation/drafts/batch_0005.jsonl"
out_path = root / "work/translation/review_batch5_dump.txt"

source = [json.loads(line) for line in source_path.read_text(encoding="utf-8").splitlines()]
draft = [json.loads(line) for line in draft_path.read_text(encoding="utf-8").splitlines()]

blocks = []
for index, (src, drf) in enumerate(zip(source, draft), 1):
    contexts = []
    for ctx in src.get("sample_contexts", []):
        contexts.append(
            f"{ctx.get('logical_locator', '')}@{ctx.get('offset_hex', '')} | "
            f"PRE={ctx.get('previous_source', '')!r} | NEXT={ctx.get('next_source', '')!r}"
        )
    blocks.append(
        "\n".join(
            [
                f"[{index:03d}] {src['tm_id']}",
                f"JP: {src['source_text']!r}",
                f"KO: {drf['translation_ko']!r}",
                f"TOKENS: {src.get('control_tokens', [])!r}",
                "CTX: " + " || ".join(contexts),
            ]
        )
    )

out_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
print(out_path)
