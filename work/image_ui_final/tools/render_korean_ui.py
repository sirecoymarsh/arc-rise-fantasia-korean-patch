#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "work" / "image_ui_final"
ORIG = BASE / "original"
EDIT = BASE / "edited"

FONT_SANS = Path(r"C:\Windows\Fonts\malgun.ttf")
FONT_SANS_BOLD = Path(r"C:\Windows\Fonts\malgunbd.ttf")
FONT_SERIF = Path(r"C:\Windows\Fonts\NotoSerifKR-VF.ttf")

LOCATIONS = {
    "adk": ("オルキナ教大神殿地下", "오르키나교 대신전 지하"),
    "adz": ("オルキナ教大神殿", "오르키나교 대신전"),
    "aka": ("空中回廊ベルクト", "공중 회랑 베르쿠트"),
    "aot": ("聖地ノワーレ", "성지 노와레"),
    "bat": ("バトラキテス", "바트라키테스"),
    "bne": ("聖都ベネトナーシュ", "성도 베네트나슈"),
    "can": ("ガロア大裂溝", "갈루아 대열곡"),
    "cob": ("コピンの里", "코핀 마을"),
    "cop": ("コピンの隠れ里", "코핀의 숨겨진 마을"),
    "des": ("ディアマント城", "디아만트성"),
    "dia": ("帝都ディアマント", "제도 디아만트"),
    "ebu": ("エブル", "에블"),
    "evt": ("ハーモニーホール", "하모니 홀"),
    "ext": ("幾何回廊アルヴィス", "기하 회랑 알비스"),
    "hai": ("グラ慈恵教会跡地", "그라 자혜교회 터"),
    "hgu": ("天衝塔ザイフェルト", "천충탑 자이페르트"),
    "hki": ("クレイデル", "크레이델"),
    "hnk": ("レテアの森", "레테아 숲"),
    "ise": ("エブル遺跡", "에블 유적"),
    "jad": ("ジャダ", "자다"),
    "kai": ("海鳴りの道", "해명의 길"),
    "kal": ("元老院", "원로원"),
    "kan": ("首都カルブンクルス", "수도 카르분쿨루스"),
    "koo": ("レゾルベント大氷壁", "레졸벤트 대빙벽"),
    "kza": ("エルゴード火山", "엘고드 화산"),
    "mit": ("ナブラ密林", "나브라 밀림"),
    "mse": ("旗艦パーセヴァル", "기함 파르세발"),
    "ori": ("教都アントラクス", "교도 안트락스"),
    "ryu": ("竜縛塔", "용박탑"),
    "sba": ("フェリス", "펠리스"),
    "sir": ("空中回廊ラスカーダ", "공중 회랑 라스카다"),
    "syo": ("ソリトン鍾乳洞", "솔리톤 종유동"),
    "tig": ("ガウス地下道", "가우스 지하도"),
    "tka": ("廃都ヒルベルト", "폐도 힐베르트"),
    "tou": ("マンデルロー海岸", "만델로 해안"),
    "tpa": ("トパジオン", "토파지온"),
    "yuk": ("オパルス", "오팔루스"),
}

STRINGS = {
    "strap_common_upper_a": ("まわりに人がいないか、物がないか\nよく確かめましょう", "주변에 사람이나 물건이 없는지\n잘 확인해 주세요."),
    "strap_common_upper_b": ("拡張コントローラを使うときは\nストラップのひもを\nプラグのフックにかけましょう", "확장 컨트롤러를 사용할 때는\n스트랩 끈을 플러그 고리에\n걸어 주세요."),
    "strap_common_bottom": ("ストラップを着け、ストッパーを締めて固定してください\nしっかり握り、手から離したり、投げたりしないでください\nWiiリモコンジャケットの装着をおすすめします", "스트랩을 착용하고 스토퍼를 조여 고정해 주세요.\n단단히 쥐고 손에서 놓거나 던지지 마세요.\nWii 리모컨 재킷 착용을 권장합니다."),
    "title_press": ("PRESS ANY BUTTON", "아무 버튼이나 누르세요"),
    "title_new_game": ("New Game", "새 게임"),
    "title_continue": ("Continue", "이어하기"),
    "title_logo_sub": ("アークライズファンタジア", "아크 라이즈 판타지아"),
    "now_loading": ("Now Loading ...", "불러오는 중…"),
    "casino_bj_bottom": ("この手札で勝負します。", "이 패로 승부합니다."),
    "casino_poker_bottom": ("交換したいカードを上下キーで選んでください", "바꿀 카드를 위아래 키로 선택해 주세요."),
    "casino_bj_controls": ("A決定 B終わる", "A 결정  B 종료"),
    "casino_bj_status": ("プレイヤー／残りカード", "플레이어 15   남은 카드 20장"),
    "casino_poker_controls": ("カード選択 Aカード交換", "↔ 카드 선택  A 교환"),
    "casino_poker_status": ("選択／交換／残りカード", "선택 0장   교환 20장   남은 카드 22장"),
}


def font(path: Path, size: int):
    return ImageFont.truetype(str(path), size)


def fit_font(text: str, path: Path, max_size: int, min_size: int, max_width: int, stroke=0):
    probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    for size in range(max_size, min_size - 1, -1):
        f = font(path, size)
        b = probe.textbbox((0, 0), text, font=f, stroke_width=stroke)
        if b[2] - b[0] <= max_width:
            return f
    return font(path, min_size)


def centered(draw, box, text, f, fill, stroke_width=0, stroke_fill=None, shadow=None):
    x0, y0, x1, y1 = box
    b = draw.textbbox((0, 0), text, font=f, stroke_width=stroke_width)
    x = x0 + ((x1 - x0) - (b[2] - b[0])) // 2 - b[0]
    y = y0 + ((y1 - y0) - (b[3] - b[1])) // 2 - b[1]
    if shadow:
        dx, dy, color, sw = shadow
        draw.text((x + dx, y + dy), text, font=f, fill=color, stroke_width=sw, stroke_fill=color)
    draw.text((x, y), text, font=f, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def save(im, name):
    EDIT.mkdir(parents=True, exist_ok=True)
    im.save(EDIT / name)


def edit_strap(name: str, upper: str):
    im = Image.open(ORIG / name).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle((260, 205, 565, 294), fill=(255, 255, 255, 255))
    d.rectangle((95, 328, 600, 426), fill=(255, 255, 255, 255))
    fu = fit_font(upper.splitlines()[0], FONT_SANS, 20, 16, 285)
    d.multiline_text((273, 213), upper, font=fu, fill=(105, 105, 105, 255), spacing=4)
    fb = font(FONT_SANS_BOLD, 20)
    d.multiline_text((106, 339), STRINGS["strap_common_bottom"][1], font=fb, fill=(0, 0, 0, 255), spacing=4)
    save(im, name)


def edit_title_label(name, text, state):
    im = Image.open(ORIG / name).convert("RGBA")
    im.paste((0, 0, 0, 0), (0, 0, im.width, im.height))
    d = ImageDraw.Draw(im)
    f = fit_font(text, FONT_SERIF, 22, 16, im.width - 8, stroke=2)
    if state == "light":
        centered(d, (0, 0, im.width, im.height), text, f, (215, 255, 248, 255), 2, (0, 53, 87, 255), shadow=(1, 2, (0, 20, 55, 180), 2))
    else:
        centered(d, (0, 0, im.width, im.height), text, f, (12, 45, 104, 255), 2, (145, 224, 236, 255), shadow=(1, 2, (0, 18, 55, 180), 2))
    save(im, name)


def edit_press():
    name = "0000__title_pressanybutton.png"
    im = Image.open(ORIG / name).convert("RGBA"); im.paste((0,0,0,0),(0,0,im.width,im.height)); d=ImageDraw.Draw(im)
    text=STRINGS["title_press"][1]; f=fit_font(text,FONT_SERIF,22,16,230,stroke=1)
    centered(d,(0,0,240,32),text,f,(245,245,245,255),1,(70,70,70,255),shadow=(2,2,(20,20,20,145),1));save(im,name)


def edit_logo():
    name="0001__title_logo.png";im=Image.open(ORIG/name).convert("RGBA")
    im.paste((0,0,0,0),(55,216,585,244));d=ImageDraw.Draw(im);text=STRINGS["title_logo_sub"][1]
    f=fit_font(text,FONT_SANS_BOLD,17,13,330,stroke=2)
    centered(d,(130,216,510,242),text,f,(245,245,245,255),2,(12,12,12,255));save(im,name)


def edit_loading():
    name="nowloading.png";im=Image.open(ORIG/name).convert("RGBA");im.paste((0,0,0,0),(0,0,128,64));d=ImageDraw.Draw(im);text=STRINGS["now_loading"][1]
    f=fit_font(text,FONT_SERIF,19,14,122,stroke=1)
    centered(d,(0,0,128,32),text,f,(40,40,40,255),1,(235,235,235,255),shadow=(1,1,(0,0,0,100),1))
    centered(d,(0,32,128,64),text,f,(245,245,245,255),1,(95,95,95,255),shadow=(1,1,(0,0,0,130),1));save(im,name)


def edit_location(code, ko):
    name=f"tex_loc_title_{code}_wtm.png";im=Image.open(ORIG/name).convert("RGBA")
    im.paste((0,0,0,0),(0,8,408,83));d=ImageDraw.Draw(im)
    f=fit_font(ko,FONT_SERIF,36,23,374,stroke=3)
    centered(d,(14,12,394,80),ko,f,(255,207,87,255),3,(112,42,0,255),shadow=(2,5,(52,18,0,130),5));save(im,name)


def edit_casino():
    name="tex_casino_intro_bj_wtm.png";im=Image.open(ORIG/name).convert("RGBA");d=ImageDraw.Draw(im)
    d.rectangle((188,0,255,15),fill=(201,151,23,245));d.text((191,4),STRINGS["casino_bj_controls"][1],font=font(FONT_SANS_BOLD,7),fill=(45,35,20,255))
    d.rectangle((0,49,42,61),fill=(17,84,67,235));d.text((4,51),"딜러",font=font(FONT_SANS_BOLD,7),fill=(245,194,25,255))
    d.rectangle((0,121,48,134),fill=(17,84,67,235));d.text((4,123),"플레이어",font=font(FONT_SANS_BOLD,6),fill=(245,194,25,255))
    d.rectangle((0,145,255,163),fill=(7,45,109,245));d.text((6,150),STRINGS["casino_bj_status"][1],font=font(FONT_SANS_BOLD,7),fill=(245,194,25,255))
    d.rectangle((0,162,255,190),fill=(11,43,105,250));d.text((8,171),STRINGS["casino_bj_bottom"][1],font=font(FONT_SANS_BOLD,9),fill=(245,245,245,255));save(im,name)
    name="tex_casino_intro_poker_wtm.png";im=Image.open(ORIG/name).convert("RGBA");d=ImageDraw.Draw(im)
    d.rectangle((162,0,255,15),fill=(201,151,23,245));d.text((165,4),STRINGS["casino_poker_controls"][1],font=font(FONT_SANS_BOLD,6),fill=(45,35,20,255))
    d.rectangle((8,21,246,72),fill=(100,52,30,245))
    left=["로열 스트레이트 플러시 ×250","파이브 카드 ×18","스트레이트 플러시 ×100","포 카드 ×50","풀 하우스 ×20"]
    right=["스트레이트 ×10","플러시 ×8","스리 카드 ×4","투 페어 ×2","원 페어 ×1","조커 ×1"]
    ff=font(FONT_SANS_BOLD,6)
    for i,t in enumerate(left):d.text((10,23+i*9),t,font=ff,fill=(235,215,185,255))
    for i,t in enumerate(right):d.text((137,23+i*8),t,font=ff,fill=(235,215,185,255))
    d.rectangle((0,145,255,163),fill=(7,45,109,245));d.text((6,150),STRINGS["casino_poker_status"][1],font=font(FONT_SANS_BOLD,6),fill=(245,194,25,255))
    d.rectangle((0,162,255,190),fill=(11,43,105,250));d.text((5,171),STRINGS["casino_poker_bottom"][1],font=font(FONT_SANS_BOLD,8),fill=(245,245,245,255));save(im,name)


def main():
    edit_strap("strapA_jp.png", STRINGS["strap_common_upper_a"][1])
    edit_strap("strapB_jp.png", STRINGS["strap_common_upper_b"][1])
    edit_press(); edit_logo()
    edit_title_label("0002__title_newgame01.png", STRINGS["title_new_game"][1], "light")
    edit_title_label("0003__title_newgame02.png", STRINGS["title_new_game"][1], "dark")
    edit_title_label("0004__title_continue01.png", STRINGS["title_continue"][1], "light")
    edit_title_label("0005__title_continue02.png", STRINGS["title_continue"][1], "dark")
    edit_loading()
    for code, (_, ko) in LOCATIONS.items(): edit_location(code, ko)
    edit_casino()
    mapping={"schema":"arf-image-ui-korean-strings-v1","provenance":"Codex internal model plus approved project translation memory where available","entries":[]}
    for key,(jp,ko) in STRINGS.items(): mapping["entries"].append({"id":key,"source_ja_or_en":jp,"translation_ko":ko})
    for code,(jp,ko) in LOCATIONS.items(): mapping["entries"].append({"id":f"location_{code}","source_ja_or_en":jp,"translation_ko":ko})
    (BASE/"korean_string_map.json").write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    exclusions={
        "interface/tex_casino_intro_race_wtm.cxd":"No Japanese text detected; race scene art only.",
        "interface/tex_casino_intro_slot_wtm.cxd":"No Japanese text detected; slot symbols and English BET COIN label retained as art/UI convention.",
        "Sys/criware.wtm":"CRIWARE middleware logo; no Japanese text and not a game-localization surface.",
        "Hbm/homeBtnIcon.wtm":"Wii Home Button icon; symbolic art with no Japanese text.",
        "Title/title.vol::title_flear.tpl":"Title flare/effect texture; no identified display text.",
        "Title/title.vol::title.brres":"Title scene model/layout resources; baked labels are stored in the separately edited WTMD members.",
        "Title/title.vol::light.brres":"Lighting effect resource; no display text.",
        "Title/title.vol::rain.brres":"Rain effect resource; no display text."
    }
    (BASE/"reports"/"image_exclusions.json").write_text(json.dumps(exclusions,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"edited_png_count":len(list(EDIT.glob('*.png'))),"string_count":len(mapping['entries']),"excluded_count":len(exclusions)},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
