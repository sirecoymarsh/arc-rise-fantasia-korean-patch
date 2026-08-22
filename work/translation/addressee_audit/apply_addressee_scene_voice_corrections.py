#!/usr/bin/env python3
"""Apply Codex-authored addressee and per-scene voice corrections.

Every replacement below was written after reviewing the whole BSCR scene in
the occurrence-bound audit corpus.  The script performs no translation.  It
only applies the pinned Korean decisions to reviewed batches and rebuilds the
final TM from those authoritative reviewed batches.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUDIT_DIR = ROOT / "work/translation/addressee_audit"
QUEUE_PATH = AUDIT_DIR / "review_queue.json"
CORPUS_PATH = AUDIT_DIR / "multiparty_scene_corpus.json"
FINAL_DIR = ROOT / "work/translation/final"
FINAL_TM = FINAL_DIR / "translation_memory_draft.json"
REVIEWED_DIR = ROOT / "work/translation/reviewed"
REVIEWS_DIR = ROOT / "work/translation/reviews"
DRAFTS_DIR = ROOT / "work/translation/drafts"
MERGER = ROOT / "work/research/merge_translation_batches.py"
BOUNDARY = ROOT / "work/translation/boundary_audit/canonical_system_boundary_audit.json"
REPORT_PATH = AUDIT_DIR / "addressee_scene_voice_corrections.json"

PINNED_QUEUE_SHA256 = "D41E2EBEE78AC2BC4131D2704B5C5D1790B58588BE9E4D056362B414BB619D9E"
PINNED_TM_SHA256 = "CF46C82FBD9A201938B5001985015FBE4D3147E718BE1101253BF9D0DC3775B1"
REVIEWER = "/root"
MARKER = (
    "[addressee-scene-voice-review] Whole-scene Codex review re-evaluated "
    "speaker, actual addressee, directed relationship, and story-phase voice."
)


# Unique TM IDs from all 128 `당신` occurrences in the multi-party queue.
# E193... occurs on both Event and Map surfaces and is intentionally listed once.
CORRECTIONS = {
    "ARF-TM-E193789FF93524BEC0AB": "니콜은\n정말 신경 쓰인단 말이지……",
    "ARF-TM-726ABB16FD33BDC3C442": "알고 있는 걸\n말해 주시겠습니까",
    "ARF-TM-0171A43DC0F99579CCB9": "넌…… 이제 슬슬\n알아 두는 게 좋을 텐데",
    "ARF-TM-8656AA5B1F26EFEB9C1F": "오이겐이 젊었을 때면\n아주 먼 옛날 이야기겠슴다?",
    "ARF-TM-E7B5C9AC50D1C3EAE5DC": "이봐, 오이겐까지\n그런 말을 하면",
    "ARF-TM-7F3FD401ED2795592FE2": "어이쿠.\n오이겐까지 갈아입겠다고\n하진 마",
    "ARF-TM-8337D606A8698F14FD44": "정신을 못 차리네, 너희들.\n그러니까 여자 때문에 고생할 팔자가\n훤히 보이는 거 아니야?",
    "ARF-TM-07E291651793E0269629": "앞으로도 계속\n정신 못 차릴 것 같네,\n너희 둘은……",
    "ARF-TM-D77208D5CCB4E0D0C998": "거기서 잔뜩 움츠리고 있는 사람은\n어떻게 느껴?",
    "ARF-TM-3F3A0D232C0336905010": "저기, 오이겐이라면 알겠지?",
    "ARF-TM-03F0624F5D8416497192": "오이겐\n안 갈아입어도 돼?",
    "ARF-TM-075424E58D42273490F0": "심각한 척해도 과거는 변하지 않아.\n나한테도 너한테도 말이야",
    "ARF-TM-A6B2881D049AA3A65678": "<$19>00, 넌 가고 싶어?",
    "ARF-TM-D3EAEBF95D8C6934102A": "<$1C>0099.\n왜 여기에 온 거야",
    "ARF-TM-4A3B33E399D6ECF652A0": "――실례합니다, 부인<$0C>너무 깊이 고민하시면\n아름다운 용모가\n상하고 맙니다",
    "ARF-TM-69357D828013EECBE471": "……아, 그래……\n그렇군.\n그런데 성함이……",
    "ARF-TM-4281A2CE50C41063F7BF": "……넌\n그들을 믿고 있구나",
    "ARF-TM-3BAF9400B1C6D63087C7": "……네 목을 내놔!",
    "ARF-TM-E18F54B4B612F061E6B0": "……넌 나와 달라!\n난 모르는 채로 있으면\n불안하다고!!",
    "ARF-TM-48F8A3374742F897A258": "……사쥬는 조용히 해.\n이야기가 안 나가잖아",
    "ARF-TM-82FEE5A1501230635D46": "……여기서 널 죽이면\n이번에는 내가 네 가족의\n원수가 돼",
    "ARF-TM-5E0AE8FEFC7EE751ECB4": "……자, 사쥬도 들어와.\n아니면 남을 거야?",
    "ARF-TM-28600D01C20AF16F417D": "……하지만 난 여러분에게\n감사하고 있어",
    "ARF-TM-BF1550AC1D7B908C85EC": "……그렇다면\n제가 바이스 님의 뜻을 잇겠습니다",
    "ARF-TM-59934DC799AF2C20B7D2": "……어머!\n월터였구나?",
    "ARF-TM-285E792CAFBB2719FFDE": "……오이겐.\n난 역시 널 용서할 수 없어.\n평생 그럴지도 몰라",
    "ARF-TM-016D113A4CA9A341055B": "……난…… 아직 널\n용서할 수 없어",
    "ARF-TM-2D3763C10DDC404D69AA": "……난 널\n용서한 건 아니야",
    "ARF-TM-F93659B273CF37F3B9A1": "아…… 칼라일 박사님?",
    "ARF-TM-9F0E0062F9DE486D313E": "아, 아아…… 그쪽은?",
    "ARF-TM-ADD29CC9CDFBC0ED5309": "아, 레온……!",
    "ARF-TM-31E16CCA893C9E80AE61": "그래.\n아를루…… 네 뜻은\n확실히 받았어",
    "ARF-TM-AFD8158B7DD14DCE10D6": "그래. 그란츠 씨 덕분이야.\n고마워",
    "ARF-TM-9209A73F130CA7640F90": "그쪽은\n내가 좋아하는 사람과 닮았어",
    "ARF-TM-F72D91495E534B42E0EA": "라르크, 정말 이매지널의 섭리가\n정의라고 생각했어?\n그렇다면 근거는 뭐야?",
    "ARF-TM-A23CDA3E0D737FAA7C3E": "그쪽은 누구야?",
    "ARF-TM-B25F6296E16E54C5D570": "어떻게 살아가든 알스가\n리얼의 섭리를 아뢰면 세계는\n결정화되는 것 아닙니까?",
    "ARF-TM-33B897F62040F4E54D89": "칼라일 박사님\n맞으신가요?",
    "ARF-TM-2035166F89083A104AC2": "네가 바네투야?",
    "ARF-TM-5F2A2D248BB313A9FDBE": "월터가 무사해서 다행이야",
    "ARF-TM-61615DA86CA0B61C12AA": "너와는 상관없는\n세계 얘기야. 신경 쓰지 마",
    "ARF-TM-EC69B7E7C42BD9D270C6": "네가 가학성을 습격하고\n어머니를 죽인 거구나!",
    "ARF-TM-8033DE03582933B68F69": "네가 말한 『확증』이\n되지는 않을지도 모르지만\n한 가지 확실한 게 있어",
    "ARF-TM-6D9899EBD559582859E8": "넌……",
    "ARF-TM-C449C2CDEA24E36E40FD": "바이스 님은 늘 그러시네요.\n일부러 남에게 오해받으려 하시죠",
    "ARF-TM-2BACDD1FBE0C2A898085": "넌 언제나 곁에 있을 권리를\n아무 조건 없이 얻었으니까!",
    "ARF-TM-AF2A2291CCCBA057BD36": "소아라 씨는 아버님의……\n심마프의 기억 속에 나타난 여성과\n쏙 빼닮았습니다. 대체 누구시죠……",
    "ARF-TM-7710EE55137603039759": "이곳을\n알고 계시는군요",
    "ARF-TM-A5F53750DBF808C3AFD1": "넌 내가 원하던 걸\n계속 독차지하고 있어!",
    "ARF-TM-0AF2B22C6C019D686F71": "그분은 마지막까지\n널 계속 사랑했구나……",
    "ARF-TM-A00E7A1FCCC3D88AED38": "어머, 너희까지?\n기쁘네. 언니는\n가슴이 두근거렸어",
    "ARF-TM-FC1DDE1FFBD203301C9C": "어머, 소동을 일으킨 게\n역시 너희였구나?",
    "ARF-TM-3D531480CEEA2DA051DA": "어머, 누가 누구 편이냐는 말은\n오히려 네가 할 소리 아닌가?",
    "ARF-TM-99B7A285C89DB6550DAB": "저기, 아까 그건……",
    "ARF-TM-EB8E9D1FD0F9D6C975C2": "레온, 사쥬와\n아는 사이야?",
    "ARF-TM-540A1B2BC80AF5D66159": "원로원 의원이야?\n왜 굳이 이 도시까지 왔지?",
    "ARF-TM-2F5CAC5BADD11878063A": "의뢰주가 맞지?",
    "ARF-TM-218F408C32018E3054FC": "너희 덕분에 살았어.\n고마워",
    "ARF-TM-9697B7683F51BA4ACDB2": "너희도\n표적이 됐을지 몰라",
    "ARF-TM-9A8AD02F3DC511504522": "너라면 알고 있잖아",
    "ARF-TM-D5BFA9A343947404874A": "짐을 전해 달라는\n부탁을 받았어<$0C>꼭 직접 받아야 한다고\n그러더군",
    "ARF-TM-6060638BCC1DB94DB668": "짐을 전해 달라는\n부탁을 받았어<$0C>상당히 초조해 보이면서\n짐을 건네주더군……",
    "ARF-TM-EB612D51F609A80F555A": "아를루는……",
    "ARF-TM-250A7DCB787380E82161": "만월의 여관에 있던……",
    "ARF-TM-BD4A29544937A5989723": "레슬리 씨는 이런 데서\n뭐 하는 검까? 분명 황자\n감시를 하고 있던 거 아니었……",
    "ARF-TM-946B2A8EAA214003FFD6": "정체가 뭐야?",
    "ARF-TM-45005637AC1A2C09264D": "그쪽은 분명\n자다에서 만난……",
    "ARF-TM-394DDFA37A62994DBE8B": "너!\n그라 자혜교회를 잊었어!?\n괴물 같은 소리 하지 마!",
    "ARF-TM-7817D119B35E599DFD4E": "아! 촌장이 부탁한\n의사 맞지?",
    "ARF-TM-1199556870904FE86FF8": "아! 그쪽은 분명……\n노와레교 전도사 일행……",
    "ARF-TM-8C9283263EF68351EB9D": "아닙니다, 꼬마 아가씨.\n아가씨 같은 미녀를 앞에 두고\n다른 여자 이야기를 하다니……",
    "ARF-TM-04F4F924C3D472AEA28E": "뭐……?\n아, 아아. 그럴 생각인데\n오이겐답지 않게 적극적이군",
    "ARF-TM-0BDB21F4C059EF436104": "응. 네 마음이 이끄는 대로",
    "ARF-TM-7F48F205C72D8CFAB5AD": "저, 저기……\n아니, 레온 님이십니까?",
    "ARF-TM-C13CE29974DBB829D865": "어이, 그쪽……",
    "ARF-TM-F8F330BA39A16635F2DF": "부탁입니다. 지나가게 해 주세요.\n저희는 장군님과 싸우려고\n여기에 온 게 아닙니다",
    "ARF-TM-A76A8B89DF5D0337D6D6": "여기서는 용사님의 감을\n믿을게요",
    "ARF-TM-C346B8282E20A60B2991": "이 아이가 말하고 싶은 건\n네 용병 경험으로\n뭔가 알아낼 수 없냐는 거야<$0C>그런 뜻이지?",
    "ARF-TM-21DAADB877A870E652FE": "이 아름다운 세상을\n너와 함께 지킬 수 있다면\n좋겠다고……",
    "ARF-TM-B12EC3B6E0D63B5A9EFA": "할아버지를 알아?\n그렇다면 역시 레온이……",
    "ARF-TM-3FA9C979F214C94C07AD": "그래? 잘 모르겠지만\n오이겐도 이견이 없다면\n베네트나슈로 가자",
    "ARF-TM-6DA009909515F48C40DB": "그래. 난 로그레스와――\n너와 계약을\n맺어야 하나 봐",
    "ARF-TM-291559EC9E190D9F5637": "그러네. 결국 라르크는\n이매지널의 섭리를――너를\n선택한 이사의 아이고",
    "ARF-TM-ABA0CF87A2A9A36A9A00": "그리고 너를――\n라르크를 만났어",
    "ARF-TM-F9BB1124892D7288FE4B": "그게…… 그쪽 사람들이\n하는 방식이군요",
    "ARF-TM-EAECDE9863BC70C38F72": "게다가 도움받은 건\n우리도 마찬가지야<$0C>마리아 씨가 그라의 이상을\n알려 준 덕분에\n무사히 계약할 수 있었으니까",
    "ARF-TM-A115678338C50A26F4E2": "게다가 의장에게도 너희에게서\n눈을 떼지 말라는 말을 들었고♪",
    "ARF-TM-9B477FF9BE0067F6E760": "그렇다면…… 난 널\n계속 살려 둘 거야",
    "ARF-TM-6120A10D84D96279FFA2": "그도 그럴 게…… 이사의 아이가\n정말로 존재했으니까",
    "ARF-TM-E30B94691818C8C08493": "그럼 아까 말씀하신\n이그나츠라는 이름은요?",
    "ARF-TM-EBA4CCDA53EE87C10068": "하지만 내가 널\n묘한 기분이 들게 한다는 건\n알고 있어……",
    "ARF-TM-EBDFE2DE283BED7096B7": "하지만 네가 도망치는 걸\n도와줬잖아",
    "ARF-TM-A1B4D59507779707DD8C": "하지만 이번 진군에\n넌 아무 관련도……",
    "ARF-TM-48A2ED2F780C1E66A22F": "하나 묻고 싶어. 아를루는 우리에게\n여러 가지를 가르쳐 줬잖아.\n그런데 왜 이제 와서 이런 짓을",
    "ARF-TM-581484F70E0C3B20927D": "오〜. 그럼 너도\n로드 나이트의 일원이었던 거야?",
    "ARF-TM-21CE6501DDDD655CCA1E": "뭐, 믿든 말든\n너희 마음이야.\n그럼 이만",
    "ARF-TM-DE861B4AC182DC566CB7": "설마…… 저게 소아라야?\n하지만 소아라는 신종이 아니야.\n용옥석을 달고 있지 않아",
    "ARF-TM-DC9AF4A7C34678196037": "나머지 １개 조를 이끌 사람은……\n오이겐, 네가 적임자라고 생각해",
    "ARF-TM-2CC529B67E969F06043F": "역시 레온이\n맞으셨군요!?",
    "ARF-TM-99457F7845D76B3EE63A": "아이온대? 그쪽이?",
    "ARF-TM-5F0C0E4C2A9569FCBF41": "아델 말이 맞아.\n넌 이제야 만난\n이사의 아이야. 무리하지 마……",
    "ARF-TM-E940818AA09AC590EB46": "엔주 씨의\n처형을 막기 위해서예요.\n레슬리 씨는 무죄니까요",
    "ARF-TM-9DF266200BD57F914CF3": "오이겐. 더글러스 경 암살 사건에 관해\n뭔가 알고 있지 않나요?",
    "ARF-TM-946BC49D6109A4D49512": "쿠도안느. 왜 스스로를\n바보라고 하는 거야?<$0C>설령 노래하는 돌을 신으로 정한 게\n너라고 해도\n강요한 건 아니잖아",
    "ARF-TM-7480AB85DA00F02B2D7D": "소아라 씨!\n대체 누구세요!",
    "ARF-TM-F41DA5841A34A89CA465": "호제아. 너는 이매지널의 섭리로\n세계를 구하려 했지",
    "ARF-TM-9DBADE7540B4D0EF5801": "라르크……\n네 목을 내놔!",
    "ARF-TM-0FEDC84000FD47DEBAEF": "라르크, 너무 무리하지 마<$0C>넌 이제야 만난\n이사의 아이니까……",
    "ARF-TM-A747F61CF1524F4B87FA": "라르크가 간다면\n나도 따라갈게. 네가\n날 선택해 줬으니까",
    "ARF-TM-B5A0598C8369A4930052": "류즈……\n넌 대체 누구지.\n소아라도 마찬가지야",
    "ARF-TM-DC4934B5D5CF41B69221": "릴리아…… 아니, 셰리.\n넌 공화국에\n소중한 존재야",
    "ARF-TM-134CFAE0CABB837034F8": "바이스 전하가\n널 붙잡으라고\n명령했다든가……",
    "ARF-TM-261D54AFBE292D687742": "전에 네가\n라르크 일행을 속이려고\n행세했던 도적단 말인데<$0C>메리디아 어딘가에\n아지트를 두고 있었지?",
    "ARF-TM-46D36CCB97F23D054204": "아무 말도 하지 마.\n난 네게 우리의 미래를 보여 주겠다.\n그뿐이야",
    "ARF-TM-A07DEE528B7FE5D15AD3": "우리가 카르분클루스에 오기\n조금 전이야. 네게……\n아니, 레온에게",
    "ARF-TM-AB26A8A303F1CB5BB75D": "모든 걸 가졌던 건\n너잖아!",
    "ARF-TM-50634264E52E372F210F": "딱히 상관없잖아?\n네가 직감대로 움직이는 녀석 곁에서\n그 녀석을 받쳐 주면 되지",
    "ARF-TM-43007CB61C10D7A293C7": "전에 클라이드 장군이 내게\n알스를 막아 달라고 했어",
    "ARF-TM-DAFBDE02B436B293119B": "지난번도 그랬지만\n이건 원래 맡은 일 아닌가……",
    "ARF-TM-6951E60D70FDE41B2402": "애초에 네가\n두리번거리다가\n이 사람과 부딪친 거잖아",
    "ARF-TM-B9F0081A8DB1374707BE": "장군.\n니콜은 우리 정보를\n네게 흘렸던 거지?",
    "ARF-TM-EF955A2790725EF7D636": "얼른 너 자신을\n믿을 수 있게 해 달라고",
    "ARF-TM-7424C82ED366B7F8606E": "내 후회가 너야?",
    "ARF-TM-55593BCE29AB95A44991": "난 너와 가고 싶어.\n이 앞에 로그레스 그라가 있다면\n도움이 될 것 같으니까",
    "ARF-TM-6516E6A2986F09BB51B2": "나도 너와 싸우고 싶어",
    "ARF-TM-0C4620E06D7DD6308577": "방어 스크린이 펼쳐지면\n너희도 도시에 못 들어오니까\n돌아오지 않아도 돼",
    "ARF-TM-97B651A4A2CA85B731A2": "놀랐어, 클라이드.\n클라이드라면 지금 알스의 방식에\n반발할 줄 알았는데",
}


# Additional exact voice-template bleed and one unrelated-unit semantic copy.
EXTRA = {
    "ARF-TM-4B92A89B55A40F8B0A55": {
        "expected_old": "누가 형님임까!",
        "new": "누가 형님이야!",
        "category": "speaker_voice_template_bleed",
        "reason": "Larc slot 00 incorrectly inherited Nicol's ~임까 ending.",
    },
    "ARF-TM-55CF78B6373927C90CEB": {
        "expected_old": "여, 형님! 무사해서 다행임다",
        "new": "여, 형님! 무사해서 다행이야",
        "category": "speaker_voice_template_bleed",
        "reason": "Sarju slot 02 incorrectly inherited Nicol's ~임다 ending.",
    },
    "ARF-TM-AEB1C0B29F1AFE7D4601": {
        "expected_old": "이 몸이 비광정을 떠나면서\n아무 조치도 안 해 둘 리 없잖슴까",
        "new": "이 몸이 비광정을 떠나면서\n아무 조치도 안 해 뒀을 리 없잖아",
        "category": "speaker_voice_template_bleed",
        "reason": "Sarju slot 02 incorrectly inherited Nicol's ~잖슴까 ending.",
    },
    "ARF-TM-FCBFFACAB4EC9B824197": {
        "expected_old": "틀림없어……\n아군끼리 싸운 거야……",
        "new": "……시끄러워!\n싫은 기억 떠올리게 하지 마!",
        "category": "unrelated_unit_semantic_copy",
        "reason": "The reviewed Korean was copied from an unrelated neighboring unit.",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    if sha256(QUEUE_PATH) != PINNED_QUEUE_SHA256:
        raise ValueError("review queue hash is not the pinned audited input")
    if sha256(FINAL_TM) != PINNED_TM_SHA256:
        raise ValueError("final TM hash is not the pinned audited input")

    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    queue_ids = {str(row["tm_id"]) for row in queue["all_dangsin_lines"]}
    if queue["counts"]["unique_dangsin_lines"] != 128:
        raise ValueError("unexpected candidate occurrence count")
    if queue_ids != set(CORRECTIONS):
        missing = sorted(queue_ids - set(CORRECTIONS))
        extra = sorted(set(CORRECTIONS) - queue_ids)
        raise ValueError(f"correction closure mismatch: missing={missing}, extra={extra}")
    evidence_by_id: dict[str, list[dict]] = defaultdict(list)
    for row in queue["all_dangsin_lines"]:
        evidence_by_id[str(row["tm_id"])].extend(row.get("evidence", []))

    final_doc = json.loads(FINAL_TM.read_text(encoding="utf-8"))
    final_by_id = {str(row["tm_id"]): row for row in final_doc["units"]}
    all_new = dict(CORRECTIONS)
    for tm_id, detail in EXTRA.items():
        all_new[tm_id] = str(detail["new"])
    if len(all_new) != len(CORRECTIONS) + len(EXTRA):
        raise ValueError("duplicate TM ID between contextual and extra corrections")

    locations: dict[str, tuple[Path, int]] = {}
    batch_rows: dict[Path, list[dict]] = {}
    for path in sorted(REVIEWED_DIR.glob("batch_*.jsonl")):
        rows = read_jsonl(path)
        batch_rows[path] = rows
        for index, row in enumerate(rows):
            tm_id = str(row["tm_id"])
            if tm_id in all_new:
                if tm_id in locations:
                    raise ValueError(f"duplicate reviewed owner for {tm_id}")
                locations[tm_id] = (path, index)
    missing_reviewed = sorted(set(all_new) - set(locations))
    if missing_reviewed:
        raise ValueError(f"missing reviewed owners: {missing_reviewed}")

    results: list[dict] = []
    touched_batches: dict[Path, list[str]] = defaultdict(list)
    for tm_id, new in all_new.items():
        unit = final_by_id.get(tm_id)
        if unit is None:
            raise ValueError(f"missing final TM unit: {tm_id}")
        old = str(unit.get("translation_ko") or "")
        if tm_id in CORRECTIONS:
            queue_rows = [row for row in queue["all_dangsin_lines"] if str(row["tm_id"]) == tm_id]
            queue_old = {str(row["translation_ko"]) for row in queue_rows}
            if queue_old != {old}:
                raise ValueError(f"queue/final old translation mismatch for {tm_id}")
            category = "scene_addressee_and_story_phase_voice"
            reason = (
                "Whole-scene review replaced context-free Korean 당신 with a "
                "scene-specific name, title, casual pronoun, group form, or safe omission."
            )
        else:
            detail = EXTRA[tm_id]
            if old != detail["expected_old"]:
                raise ValueError(f"unexpected old translation for {tm_id}")
            category = str(detail["category"])
            reason = str(detail["reason"])
        if old == new:
            raise ValueError(f"no-op correction: {tm_id}")
        path, index = locations[tm_id]
        reviewed = batch_rows[path][index]
        if str(reviewed.get("translation_ko") or "") != old:
            raise ValueError(f"reviewed/final old translation mismatch for {tm_id}")
        reviewed["translation_ko"] = new
        reviewed["reviewer"] = REVIEWER
        notes = str(reviewed.get("notes") or "")
        if MARKER not in notes:
            reviewed["notes"] = (notes + (" " if notes else "") + MARKER).strip()
        touched_batches[path].append(tm_id)
        results.append(
            {
                "tm_id": tm_id,
                "batch": path.stem,
                "source_text": str(unit["source_text"]),
                "before": old,
                "after": new,
                "category": category,
                "reason": reason,
                "multiparty_evidence": evidence_by_id.get(tm_id, []),
            }
        )

    batch_hashes = []
    for path, tm_ids in sorted(touched_batches.items(), key=lambda item: item[0].name):
        before_hash = sha256(path)
        write_jsonl(path, batch_rows[path])
        after_hash = sha256(path)
        batch = path.stem
        review_path = REVIEWS_DIR / f"{batch}_review.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        modifications = review.setdefault("modifications", [])
        by_mod_id = {str(row.get("tm_id")): row for row in modifications}
        for tm_id in tm_ids:
            result = next(row for row in results if row["tm_id"] == tm_id)
            modification = by_mod_id.get(tm_id)
            if modification is None:
                modification = {"tm_id": tm_id}
                modifications.append(modification)
            elif modification.get("after") != result["before"]:
                modification["superseded_after"] = modification.get("after")
            modification.update(
                {
                    "source_text": result["source_text"],
                    "before": result["before"],
                    "after": result["after"],
                    "category": result["category"],
                    "reason": result["reason"],
                }
            )
        draft_path = DRAFTS_DIR / f"{batch}.jsonl"
        drafts = {str(row["tm_id"]): row for row in read_jsonl(draft_path)}
        reviewed_rows = batch_rows[path]
        modified_units = sum(
            str(row.get("translation_ko") or "")
            != str(drafts[str(row["tm_id"])].get("translation_ko") or "")
            for row in reviewed_rows
        )
        review["modified_units"] = modified_units
        review["unchanged_units"] = len(reviewed_rows) - modified_units
        review["addressee_scene_voice_review"] = {
            "schema": "arf-addressee-scene-voice-batch-review-v1",
            "reviewer": REVIEWER,
            "independent_review": True,
            "translation_engine_policy": "Codex internal models only",
            "external_translation_services_used": [],
            "tm_ids": sorted(tm_ids),
            "reviewed_sha256": after_hash,
        }
        review.setdefault("hashes", {})["reviewed_sha256"] = after_hash
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        batch_hashes.append(
            {
                "batch": batch,
                "reviewed_sha256_before": before_hash,
                "reviewed_sha256_after": after_hash,
                "review_report_sha256_after": sha256(review_path),
                "tm_ids": sorted(tm_ids),
            }
        )

    subprocess.run(
        [
            sys.executable,
            str(MERGER),
            str(FINAL_TM),
            str(FINAL_DIR),
            str(REVIEWED_DIR),
            "--reviewed",
            "--reviewer",
            REVIEWER,
            "--boundary-audit",
            str(BOUNDARY),
        ],
        check=True,
    )

    merged = json.loads(FINAL_TM.read_text(encoding="utf-8"))
    merged_by_id = {str(row["tm_id"]): row for row in merged["units"]}
    for tm_id, expected in all_new.items():
        if str(merged_by_id[tm_id].get("translation_ko") or "") != expected:
            raise ValueError(f"merged correction mismatch for {tm_id}")
    merged["addressee_scene_voice_review"] = {
        "schema": "arf-addressee-scene-voice-review-v1",
        "reviewer": REVIEWER,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "source_review_queue": str(QUEUE_PATH),
        "source_review_queue_sha256": PINNED_QUEUE_SHA256,
        "source_scene_corpus": str(CORPUS_PATH),
        "candidate_occurrences_reviewed": 128,
        "unique_addressee_tm_ids_corrected": len(CORRECTIONS),
        "speaker_voice_template_bleed_corrected": 3,
        "unrelated_unit_semantic_copy_corrected": 1,
        "total_unique_tm_ids_corrected": len(all_new),
        "correction_report": str(REPORT_PATH),
    }
    FINAL_TM.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "schema": "arf-addressee-scene-voice-corrections-v1",
        "game_id": "RPJJ99",
        "reviewer": REVIEWER,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_models_or_apis_used": False,
        "decision_unit": "Japanese source + whole scene + speaker + actual addressee + relationship + story phase",
        "inputs": {
            "review_queue": str(QUEUE_PATH),
            "review_queue_sha256": PINNED_QUEUE_SHA256,
            "multiparty_scene_corpus": str(CORPUS_PATH),
            "final_tm_sha256_before": PINNED_TM_SHA256,
        },
        "counts": {
            "candidate_occurrences_reviewed": 128,
            "unique_addressee_tm_ids_corrected": len(CORRECTIONS),
            "speaker_voice_template_bleed_corrected": 3,
            "unrelated_unit_semantic_copy_corrected": 1,
            "total_unique_tm_ids_corrected": len(all_new),
            "touched_reviewed_batches": len(touched_batches),
        },
        "batch_hashes": batch_hashes,
        "corrections": sorted(results, key=lambda row: row["tm_id"]),
        "outputs": {
            "final_translation_memory": str(FINAL_TM),
            "final_translation_memory_sha256": sha256(FINAL_TM),
            "final_translation_csv": str(FINAL_DIR / "translation_memory_draft.csv"),
            "final_translation_csv_sha256": sha256(FINAL_DIR / "translation_memory_draft.csv"),
            "coverage": str(FINAL_DIR / "coverage.json"),
            "coverage_sha256": sha256(FINAL_DIR / "coverage.json"),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "corrected_tm_ids": len(all_new),
                "touched_batches": len(touched_batches),
                "final_tm_sha256": sha256(FINAL_TM),
                "report": str(REPORT_PATH),
                "report_sha256": sha256(REPORT_PATH),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
