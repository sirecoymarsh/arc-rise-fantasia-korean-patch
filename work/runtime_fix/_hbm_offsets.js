const fs=require('fs'),crypto=require('crypto');
function be(s){const le=Buffer.from(s,'utf16le');const o=Buffer.alloc(le.length);for(let i=0;i<le.length;i+=2){o[i]=le[i+1];o[i+1]=le[i];}return o;}
const terms={
 home_csv:[
 '接続する順番に\r\n①ボタンと②ボタンを\r\n同時に押してください。',
 '切断中・・・',
 'Wiiメニューにもどりますか？\r\n（保存していない内容は失われます）',
 'リセットしますか？\r\n（保存していない内容は失われます）'
 ],
 home_nosave_csv:[
 '接続する順番に\r\n①ボタンと②ボタンを\r\n同時に押してください。',
 '切断中・・・',
 'Wiiメニューにもどりますか？',
 'リセットしますか？'
 ]
};
for(const [key,ss] of Object.entries(terms)){
 const name=key==='home_csv'?'home.csv':'home_nosave.csv';const p='work/disc_extracted/DATA/files/Hbm/'+name; const b=fs.readFileSync(p);
 console.log(name);
 for(const text of ss){const x=be(text);let pos=-1,starts=[];while((pos=b.indexOf(x,pos+1))>=0)starts.push(pos);console.log(JSON.stringify({text,offsets:starts,offset_hex:starts.map(n=>'0x'+n.toString(16).toUpperCase()),byte_length:x.length,raw_sha256:crypto.createHash('sha256').update(x).digest('hex').toUpperCase(),raw_hex:x.toString('hex').toUpperCase()}));}
}

