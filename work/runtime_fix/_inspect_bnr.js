const fs=require('fs'),crypto=require('crypto');
const p='work/disc_extracted/DATA/files/opening.bnr',b=fs.readFileSync(p);
for(const enc of ['utf8']){}
const magic=Buffer.from([0x55,0xaa,0x38,0x2d]); console.log('size',b.length,'sha',crypto.createHash('sha256').update(b).digest('hex').toUpperCase(),'u8magic',b.indexOf(magic),'hex','0x'+b.indexOf(magic).toString(16));
function swapToLE(buf){const o=Buffer.alloc(buf.length);for(let i=0;i+1<buf.length;i+=2){o[i]=buf[i+1];o[i+1]=buf[i];}return o;}
for(let off=0x5c;off<0x5c+10*84;off+=84){let z=off;while(z+1<off+84 && (b[z]||b[z+1])) z+=2;const s=swapToLE(b.subarray(off,z)).toString('utf16le');console.log('IMET','0x'+off.toString(16),JSON.stringify(s));}
// find runs of ASCII printable strings >=4
let arr=[];for(let i=0;i<b.length;){if(b[i]>=0x20&&b[i]<=0x7e){let j=i;while(j<b.length&&b[j]>=0x20&&b[j]<=0x7e)j++;if(j-i>=4)arr.push([i,b.subarray(i,j).toString('ascii')]);i=j}else i++;}
console.log(arr.slice(0,100).map(([o,s])=>'0x'+o.toString(16)+': '+s).join('\n'));
