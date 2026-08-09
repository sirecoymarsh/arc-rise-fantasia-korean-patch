from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from arf_table_tool import tutorial_record_starts, field_raw, render_mixed, contains_japanese
from analyze_tutorial import decode_field
d=Path('work/disc_extracted/DATA/files/Btl/btl_tutorial.vld').read_bytes()
old=[]
for p in range(0,len(d)-0x170+1,0x10):
    if d[p+0xc:p+0x10]!=b'\xff'*4:continue
    m=decode_field(d[p+0x14:p+0x114]); s=decode_field(d[p+0x114:p+0x154])
    if m!='<binary>' and (m or s):old.append(p)
new=tutorial_record_starts(d)
print('old',len(old),'new',len(new),'missing',[hex(x) for x in old if x not in new],'extra',[hex(x) for x in new if x not in old])
for p in old:
    if p not in new:
        m,_=field_raw(d,p+0x14,0x100);s,_=field_raw(d,p+0x114,0x40)
        print(hex(p),repr(render_mixed(m)),repr(render_mixed(s)),contains_japanese(render_mixed(s)),m.hex(),s.hex())
