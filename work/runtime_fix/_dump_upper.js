const fs=require('fs'),d=require('../catalog/text_probe_10.json');
for(const r of d.records.filter(r=>r.offset>=0x3d0000&&r.offset<0x3d6000))console.log(r.offset.toString(16).padStart(8,'0')+'\t'+r.byte_length+'\t'+JSON.stringify(r.text));
