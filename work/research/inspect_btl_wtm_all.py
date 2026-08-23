#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'work/battle_ui_raster_application/btl_tex_wtm_extract/payloads'
out=ROOT/'work/battle_ui_raster_application/all_wtm_png'
out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('wtmd',ROOT/'work/image_ui_final/tools/wtmd_pipeline.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
rows=[]
for p in sorted(source.iterdir()):
    if not p.is_file() or p.stat().st_size==0 or '.wtm' not in p.name: continue
    try:
        im,h=mod.decode_wtmd(p.read_bytes())
    except Exception:
        continue
    q=out/(p.name+'.png'); im.save(q); rows.append((p.name,q,im.size))
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',13)
for page_start in range(0,len(rows),18):
    page=rows[page_start:page_start+18]
    width=720; y=10
    cells=[]
    for name,q,size in page:
        im=Image.open(q).convert('RGBA')
        scale=min(1.0,640/max(1,im.width),120/max(1,im.height))
        if scale<1: im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.Resampling.LANCZOS)
        cells.append((name,im)); y+=24+max(28,im.height)+12
    sheet=Image.new('RGB',(width,y),(28,30,32)); d=ImageDraw.Draw(sheet); y=8
    for name,im in cells:
        d.text((10,y),name,font=font,fill='white'); y+=22
        bg=Image.new('RGBA',im.size,(0,0,0,255)); bg.alpha_composite(im)
        sheet.paste(bg.convert('RGB'),((width-im.width)//2,y)); y+=max(28,im.height)+12
    sheet.save(out/f'contact_{page_start//18+1:02d}.png')
print({'decoded':len(rows),'sheets':(len(rows)+17)//18,'output':str(out)})
