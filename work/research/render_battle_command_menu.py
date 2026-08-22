from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[2]
src=root/'work/battle_ui_raster_application/shared_candidates_png/0050__btl_comandselect_moji.wtm.png'
out=root/'work/battle_ui_raster_application/preview_png/btl_comandselect_moji.wtm.png'
orig=Image.open(src).convert('RGBA')
img=Image.new('RGBA',orig.size,(0,0,0,0))
draw=ImageDraw.Draw(img)
font_path=r'C:\Windows\Fonts\malgunbd.ttf'
rows=['행동 선택','작전 설정','상태','도주']
for i,text in enumerate(rows):
    box=(0,i*24,80,(i+1)*24)
    for size in range(17,8,-1):
        font=ImageFont.truetype(font_path,size)
        bb=draw.textbbox((0,0),text,font=font,stroke_width=1)
        if bb[2]-bb[0]<=76 and bb[3]-bb[1]<=21: break
    x=(80-(bb[2]-bb[0]))//2-bb[0]
    y=i*24+(24-(bb[3]-bb[1]))//2-bb[1]
    draw.text((x,y),text,font=font,fill=(255,255,255,255),stroke_width=1,stroke_fill=(25,25,25,255))
out.parent.mkdir(parents=True,exist_ok=True); img.save(out)
print(out)
