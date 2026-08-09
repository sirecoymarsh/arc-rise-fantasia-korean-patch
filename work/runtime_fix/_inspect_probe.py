import json, pathlib, collections
p=pathlib.Path(r'work/catalog/text_probe_10.json')
d=json.loads(p.read_text(encoding='utf-8'))
print(d['candidate_count'], len(d['records']))
print(collections.Counter((r['byte_length']//16)*16 for r in d['records']).most_common())
for r in d['records']:
    if r['byte_length']>=12:
        print(f"{r['offset']:08X} len={r['byte_length']:3} cap={r['capacity_to_nul']:3} {ascii(r['text'])}")
