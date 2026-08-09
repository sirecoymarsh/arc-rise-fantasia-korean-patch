#!/usr/bin/env python3
from __future__ import annotations
import collections, struct
from pathlib import Path

P=Path('work/pristine/Sys/system.vol/quest.bin')
d=P.read_bytes(); tables,relocs=struct.unpack_from('>HH',d,8); desc_words=2*tables-1; r0=0x10+4*desc_words
pairs=[struct.unpack_from('>II',d,r0+i*8) for i in range(relocs)]
vals=[v for _,v in pairs]; targets=[t for t,_ in pairs]; pool=min(vals)
print('size',len(d),'tables',tables,'relocs',relocs,'reloc0',hex(r0),'pool',hex(pool),'unique_values',len(set(vals)))
print('values monotonic',vals==sorted(vals),'targets monotonic',targets==sorted(targets))
print('target deltas',collections.Counter(b-a for a,b in zip(targets,targets[1:])).most_common(20))
print('value duplicates',[(hex(k),v) for k,v in collections.Counter(vals).items() if v>1][:20])
print('all_pointer_targets_zero', all(d[t:t+4] == b'\0\0\0\0' for t in targets))
for i in range(80):
    row=[]
    for j in range(6):
        t,v=pairs[i*6+j]; end=d.find(b'\0',v); raw=d[v:end];
        try:s=raw.decode('euc_jp')
        except:s='<'+raw.hex()+'>'
        row.append((hex(t-(0xF20+i*0x60)),hex(v),s))
    if i<5 or i>=75 or any(x[2] for x in row[4:]): print(i,row)

# Test that unique pointed strings plus their NULs tile the pool to EOF exactly.
uv=sorted(set(vals)); gaps=[]
for i,v in enumerate(uv):
    e=d.find(b'\0',v)+1; n=uv[i+1] if i+1<len(uv) else len(d)
    if e!=n:gaps.append((v,e,n,d[e:n].hex()))
print('pool_tiling_gaps',len(gaps),gaps[:20])
