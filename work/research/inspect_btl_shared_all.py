from __future__ import annotations
import importlib.util
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[2]
source=root/'work/battle_ui_raster_application/inspect_0007__btl_tex_shared/payloads'
out=root/'work/battle_ui_raster_application/all_shared_png';out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('wtmd',root/'work/image_ui_final/tools/wtmd_pipeline.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=[]
for p in sorted(source.iterdir()):
 if not p.is_file() or p.stat().st_size==0: continue
 try: im,h=m.decode_wtmd(p.read_bytes())
 except Exception: continue
 q=out/(p.name+'.png');im.save(q);rows.append((p.name,q))
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',12)
for n,start in enumerate(range(0,len(rows),20),1):
 page=rows[start:start+20]; cells=[];height=10
 for name,q in page:
  im=Image.open(q).convert('RGBA');scale=min(1,620/max(1,im.width),90/max(1,im.height))
  if scale<1:im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.Resampling.LANCZOS)
  cells.append((name,im));height+=20+max(22,im.height)+8
 sh=Image.new('RGB',(700,height),(27,29,31));d=ImageDraw.Draw(sh);y=6
 for name,im in cells:
  d.text((8,y),name,font=font,fill='white');y+=18;bg=Image.new('RGBA',im.size,(0,0,0,255));bg.alpha_composite(im);sh.paste(bg.convert('RGB'),((700-im.width)//2,y));y+=max(22,im.height)+8
 sh.save(out/f'contact_{n:02d}.png')
print({'decoded':len(rows),'sheets':(len(rows)+19)//20})
