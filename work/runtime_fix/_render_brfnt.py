from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import struct
p=Path('work/runtime_fix/audit_renders/hbm/RevoIpl_UtrilloProGrecoStd_M_32_I4.brfnt')
b=p.read_bytes(); off=0x60; sw,sh=32,256; ss=0x1000; n=14
ims=[]
for si in range(n):
 raw=b[off+si*ss:off+(si+1)*ss]; pix=[0]*(sw*sh); q=0
 for by in range(0,sh,8):
  for bx in range(0,sw,8):
   for y in range(8):
    for x in range(0,8,2):
     v=raw[q];q+=1
     pix[(by+y)*sw+bx+x]=(v>>4)*17;pix[(by+y)*sw+bx+x+1]=(v&15)*17
 im=Image.new('L',(sw,sh));im.putdata(pix);ims.append(im)
# cmap labels
maps={}
o=0xe1b4
start,end,method=struct.unpack_from('>HHH',b,o+8)
for cp in range(start,end+1):
 g=struct.unpack_from('>H',b,o+20+(cp-start)*2)[0]
 if g!=0xffff:maps[g]=chr(cp)
o=0xe270;cnt=struct.unpack_from('>H',b,o+20)[0]
for i in range(cnt):
 cp,g=struct.unpack_from('>HH',b,o+22+i*4);maps[g]=chr(cp)
# contact
scale=4;cw=150;ch=160;cols=8;rows=(108+cols-1)//cols
out=Image.new('RGB',(cw*cols,ch*rows),(30,30,30));d=ImageDraw.Draw(out);font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',18)
info=[]
for g in range(108):
 sheet=g//8;within=g%8;crop=ims[sheet].crop((0,within*32,29,within*32+31));bbox=crop.getbbox();left,width,char=struct.unpack_from('>bBB',b,0xe070+g*3);info.append((g,maps.get(g,''),bbox,left,width,char))
 x=(g%cols)*cw;y=(g//cols)*ch;show=crop.resize((116,124),Image.Resampling.NEAREST);out.paste(Image.merge('RGB',(show,show,show)),(x+17,y+25));d.text((x+2,y+2),f'{g} {maps.get(g,"")} m={left},{width},{char}',font=font,fill='yellow')
out.save('work/runtime_fix/audit_renders/hbm/brfnt_glyph_contact.png')
Path('work/runtime_fix/audit_renders/hbm/brfnt_glyph_metrics.txt').write_text('\n'.join(map(str,info)),encoding='utf-8')
print('saved',out.size)
