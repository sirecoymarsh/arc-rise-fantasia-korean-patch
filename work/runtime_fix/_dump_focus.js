const fs=require('fs'); const d=JSON.parse(fs.readFileSync('work/catalog/text_probe_10.json','utf8'));
const ranges=[[0x3c6400,0x3c6600],[0x3c8a00,0x3ca260],[0x3ca500,0x3ca700],[0x3cb700,0x3d1d80]];
let out=[]; for(const r of d.records) if(ranges.some(([a,b])=>r.offset>=a&&r.offset<b)) out.push(`${r.offset.toString(16).padStart(8,'0')}\t${r.byte_length}\t${r.capacity_to_nul}\t${JSON.stringify(r.text)}\t${r.raw_hex}`);
fs.writeFileSync('work/runtime_fix/candidates_focus.tsv',out.join('\n'),'utf8'); console.log(out.length)
