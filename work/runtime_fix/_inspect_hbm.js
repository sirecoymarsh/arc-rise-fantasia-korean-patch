const fs=require('fs'), crypto=require('crypto');
for(const name of ['home.csv','home_nosave.csv']){
 const p='work/disc_extracted/DATA/files/Hbm/'+name; const b=fs.readFileSync(p);
 const swap=Buffer.alloc(b.length); for(let i=0;i+1<b.length;i+=2){swap[i]=b[i+1];swap[i+1]=b[i];}
 const s=swap.toString('utf16le');
 console.log(name,b.length,crypto.createHash('sha256').update(b).digest('hex').toUpperCase(),b.subarray(0,16).toString('hex'));
 console.log(s.slice(0,1500).replace(/\r/g,'\\r').replace(/\n/g,'\\n\n'));
 console.log('---');
}
