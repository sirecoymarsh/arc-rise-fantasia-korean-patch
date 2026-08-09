const fs=require('fs'); const j=JSON.parse(fs.readFileSync('work/catalog/text_probe_10.json','utf8'));const td=new TextDecoder('euc-jp');
const ranges=[[3972500,3973700],[4001700,4003800]];
for(const [a,b] of ranges){console.log('RANGE',a,b);for(const r of j.records.filter(x=>x.offset>=a&&x.offset<=b)){const text=td.decode(Buffer.from(r.raw_hex,'hex'));console.log(JSON.stringify({...r,text,offset_hex:'0x'+r.offset.toString(16).toUpperCase()}));}}
