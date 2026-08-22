from __future__ import annotations
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
root=Path(__file__).resolve().parents[2]
out=root/'work/battle_ui_raster_application/preview_png';out.mkdir(parents=True,exist_ok=True)
bold=r'C:\Windows\Fonts\malgunbd.ttf'

def center(img,text,box,size,fill,stroke,sw=1):
 d=ImageDraw.Draw(img);f=ImageFont.truetype(bold,size);bb=d.textbbox((0,0),text,font=f,stroke_width=sw);x=box[0]+(box[2]-box[0]-(bb[2]-bb[0]))//2-bb[0];y=box[1]+(box[3]-box[1]-(bb[3]-bb[1]))//2-bb[1];d.text((x,y),text,font=f,fill=fill,stroke_width=sw,stroke_fill=stroke)

# Both Excel Act banners: preserve the side rays and replace the full center plate.
for name,srcname,color in [
 ('btl_renkei_moji_excelact_pc.wtm','0034__btl_renkei_moji_excelact_pc.wtm.png','blue'),
 ('btl_renkei_moji_excelact_enemy.w','0035_enemy.png','red')]:
 src=root/'work/battle_ui_raster_application/all_wtm_png'/srcname
 img=Image.open(src).convert('RGBA');w,h=img.size;ImageDraw.Draw(img).rectangle((96,0,w-97,h-1),fill=(0,0,0,0))
 fill=(245,255,255,255) if color=='blue' else (255,120,50,255);stroke=(55,65,80,255) if color=='blue' else (120,10,0,255)
 center(img,'오의',(88,2,w-88,h-2),30,fill,stroke,2);img.save(out/(name+'.png'))

# Battle-incapacitated stamp.
base=Image.new('RGBA',(136,64),(0,0,0,0));layer=Image.new('RGBA',(136,64),(0,0,0,0));center(layer,'전투불능',(4,10,132,54),25,(255,42,28,255),(70,0,0,255),2);layer=layer.rotate(12,resample=Image.Resampling.BICUBIC,center=(68,32));base.alpha_composite(layer);base.save(out/'btl_status_dead.wtm.png')

# Link-rate result legend.
img=Image.new('RGBA',(232,32),(0,0,0,0));center(img,'연계율 %  총 피해량  HIT',(2,2,230,30),17,(255,190,45,255),(92,32,0,255),1);img.save(out/'btl_hit_moji.wtm.png')

# Weakness/resistance legend.
img=Image.new('RGBA',(64,16),(0,0,0,0));center(img,'약점 내성',(0,0,64,16),10,(255,255,255,255),(20,20,20,255),1);img.save(out/'btl_weak_resist_moji.wtm.png')
print('rendered',6)
