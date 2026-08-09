const fs=require('fs'); const d=JSON.parse(fs.readFileSync('work/catalog/text_probe_10.json','utf8'));
console.log(d.candidate_count,d.records.length);
for(const r of d.records) if(r.byte_length>=12) console.log(r.offset.toString(16).padStart(8,'0'),`len=${r.byte_length}`,`cap=${r.capacity_to_nul}`,JSON.stringify(r.text));
