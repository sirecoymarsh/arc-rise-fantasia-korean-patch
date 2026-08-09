import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DRAFTS=ROOT/'work/translation/drafts'; REVIEWED=ROOT/'work/translation/reviewed'; REPORTS=ROOT/'work/translation/reviews'
REVIEWER='/root/review_batch_0058_0060'; DRAFT_AUTHOR='/root/audit_boundary_integration'
EDITS={
76:{
0:("제가 당신의 엿듣기를 눈치채지\n못했다고 생각했나요?","semantic_accuracy","엿듣기를 한 주체와 이를 눈치챈 화자를 명확히 구분했다."),
1:("『소금』이 빠진다고……?\n여기에 소금길이 생기는 거야?","wordplay","潮를 소금으로 오해하는 원문의 말장난을 복원했다."),
4:("그렇다면 넌 이제\n이매지널의 섭리를 도출할\n이사의 아이가 아니군","terminology","導く를 설정 문맥의 '도출하다'로 통일했다."),
11:("그렇슴다.\n가학성을 습격한 건 오르키나교고\n완전히 누명임다!","register","니콜의 말버릇을 대사 전체에 일관되게 적용했다."),
23:("마하트 폐하께서 서거하셨다는 소문은\n상당히 신빙성이 높은 것 같아.\n아니면 이렇게까지 퍼지지 않아","register","왕의 죽음을 나타내는 존칭 표현을 자연스럽게 다듬었다."),
31:("특별한 재능이 없어도\n조금씩 그 사람을\n성장시키는 재능이 있습니다――<$0C>그건 계속하는 재능입니다.\n다행히 저는 이 재능을 타고났습니다.\n근면한 조상에게 받은 선물입니다","semantic_accuracy","かろうじて를 부자연스러운 '간신히'가 아닌 꾸준한 성장의 의미로 옮겼다."),
52:("새 지도자 라르크.\n우리 저항군 전원은\n앞으로 당신을 따르겠습니다<$0C>무슨 일이든 명령해 주십시오","terminology","レジスタンス와 직책을 확정 용어로 통일했다."),
56:("용박탑 로케타이\n탑 내부에 침입　　\n심마프 등장　　　\n심마프와 계약　　\nＶＳ 디노스전２\n도시로 돌아가자　\n돌아간다　　　　","formatting","메뉴 항목의 간격과 돌아가기 표기를 정리했다."),
62:("파도 소리를 들으면\n지난날의 항구가 떠오릅니다.\n그때는 제 곁에 또 １명이 있었고……","naturalness","潮騒를 통용되는 파도 소리로 자연스럽게 옮겼다."),
76:("잠깐, 지금 말 걸지 마.\n지금 확실히 속이 안 좋으니까……\n너무 다정하게 굴지 마……","semantic_accuracy","気分悪い가 불쾌감이 아닌 몸 상태를 가리키도록 바로잡았다."),
82:("기하 회랑 알비스・종언의 기억  제２층","formatting","프로젝트의 고유명사 구분점 표기를 통일했다."),
86:("천충탑 자이펠트・라운드 플로어０８","terminology","ザイフェルト의 확정 표기와 구분점을 적용했다."),
98:("경장 차림의 경비병들이\n정말 부러워……","naturalness","軽装를 부자연스러운 '장비를 입다' 대신 경장 차림으로 옮겼다."),
108:("신에게 기도하러 온 것처럼\n도저히 보이지 않는 자도\n몇 명 섞인 모양이지만――<$0C>신앙은 고귀한 것이지……\n나나 너 같은 인간에게도","semantic_accuracy","기도하러 온 사람의 외양을 논하는 원문 의미를 명확히 했다."),
112:("둘 다 중요하지.\n１명이서 무리라면\n친구나 동료를 모으면 돼","naturalness","인원수 １을 유지하면서 조사를 자연스럽게 고쳤다."),
116:("사랑을…… 해 본 적 있나요?\n전 있습니다……<$0C>하지만――\n이렇게 가슴이 괴롭다면\n사랑 따윈 하지 않는 편이 낫습니다","naturalness","목적격 조사와 말줄임표 결합을 자연스럽게 다듬었다."),
143:("내 이름은 오브제 군.\n빙벽을 전환하는 재능이 있는 남자야","punctuation","원문에 없는 종결 마침표를 제거했다."),
148:("제국의 선전포고 때문에\n머리 위로 비광정이 지나갈 때마다\n가슴을 졸이는 나날이야<$0C>뭐, 그게 제국 녀석들의\n노림수겠지만\n우리는 괜한 피해를 보는 셈이지","semantic_accuracy","いい迷惑를 상대 때문에 괜한 피해를 본다는 의미로 옮겼다."),
165:("지금 저――\n상당히 다운된 기분임다.\n맑은 날에도 마음엔 눈물비가 내림다<$0C>마하트 폐하는 힐링계라\n제 마음의 오아시스였슴다……","register","니콜의 말버릇을 대사 전체에 통일했다."),
177:("길드란\n나 같은 용병이\n일을 받는 곳이야<$0C>길드의 일은\n『퀘스트』라고 불러<$0C>그 의뢰 내용을 달성하면\n보수를 받는 구조지<$0C>아무튼\n한번 길드에 들러 보자","naturalness","마지막 행동 제안을 자연스러운 구어체로 다듬었다."),
},
77:{
18:("저항군 사람들이\n안절부절못하고 있어……<$0C>……무슨 일이 있는 걸까?","terminology","レジスタンス의 확정 표기 '저항군'을 적용했다."),
21:("이벤트(EV09_17_2700B)를 재생","formatting","메뉴 문구의 괄호를 한국어 표기로 통일했다."),
27:("귀족도 병사도\n뭘 그렇게 서두르는지……<$0C>감정을 드러내거나\n거드름을 피우며 뛰는 건\n마음에 여유가 없다는 증거입니다","naturalness","肩で風を切る의 거만한 태도를 자연스럽게 옮겼다."),
29:("여기가 그 이름도 유명한\n『홍하의 자무엘』 님이\n운영하는 무예관인가<$0C>전설의 로드나이트가 세운 무예관……\n아들이 크면\n꼭 여기에 다니게 하고 싶군","naturalness","중복 소유격을 제거해 자연스럽게 다듬었다."),
42:("티그리스강 D2로\n","formatting","지명과 맵 식별자의 띄어쓰기를 통일했다."),
49:("저기 있는 병사분들이 나누는\n두 황자님 이야기는\n전 잘 모르겠어요……<$0C>두 분 다 훌륭하시니까요","semantic_accuracy","병사들이 두 황자에 관해 나누는 이야기라는 수식 관계를 명확히 했다."),
58:("오늘은 아가씨를 돌보느라\n여기까지 왔습니다만\n저로서는 감당이 안 됩니다……<$0C>아이는 씩씩한 게 제일이지만\n무엇이든 지나치면 문제라서……\n계속 가슴을 졸이고 있습니다","semantic_accuracy","肝を冷やしている의 지속적인 불안 상태를 정확히 반영했다."),
74:("나의 영역을 침범하러 왔느냐\n이사의 아이여!<$0C>멸망당하는 것을\n두려워하지도 않고!","naturalness","수동 의미와 조사를 바로잡았다."),
102:("마음에 응어리가 있으면\n검도 무뎌지는 법이지.\n……너 나름대로 결판을 짓고 와","semantic_accuracy","剣の方를 검술 전반을 가리키는 표현으로 바로잡았다."),
107:("귀족들의 모반 소문과\n저항군의 테러 위험도 있다.\n……경비에 힘을 쏟아야겠군","terminology","レジスタンス의 확정 표기를 적용했다."),
109:("자, 어떻게 할 건데?\n이대로 목적도 없이\n어슬렁거릴 셈이야?","naturalness","도입부와 질문형 구어를 자연스럽게 다듬었다."),
112:("(기이한 수집가에게도\n　역시 이건 팔리지 않았던\n　모양이네……)","formatting","한국어 문장에 맞는 괄호 표기로 통일했다."),
130:("저 계단에\n수상한 남자가 있지?<$0C>악인처럼 보이지는 않지만\n그런 습격이 있은 직후다.\n경계해서 나쁠 건 없어","naturalness","경계 권고의 문장을 자연스럽게 다듬었다."),
140:("어라, 전에 어디서 만났지?\n그래, 제도에서 본 적 있는 얼굴이야!\n분명 너, 공인 용병이었지?","terminology","認可傭兵을 프로젝트 통용 표기 '공인 용병'으로 통일했다."),
162:("라르크 님――\n화평에 관한 논의는\n추후 집무실에서 진행됩니다","register","後日를 '추후'로 옮기고 공적인 안내 어조를 다듬었다."),
166:("그래. 섭리 없는 미래를 위하여","terminology","定理의 확정 설정 용어 '섭리'를 적용했다."),
172:("……나도 서툴렀어.\n하지만 요즘 너무 많은 일을 겪어서\n점점 익숙해졌어","semantic_accuracy","苦手를 능숙하지 못했다는 의미로 명확히 했다."),
179:("군에 들어가 오래 살아남아서\n이 도시가 사랑스럽게 느껴질 만큼\n버텨 보려고 해……","naturalness","목적 관계와 한국어 어순을 자연스럽게 정리했다."),
},
78:{
6:("옛날엔 어부의 작은 배에 태워 달라고 했지.\n아니, 그 집 아들이 소꿉친구라서――\n이른 아침부터 바다에 나가서는<$0C>선물을 잔뜩\n집으로 가져왔지. 이야,\n그때 멀미는 정말 심했어……","semantic_accuracy","화자가 어부의 배에 태워 달라고 했다는 능동 관계를 바로잡았다."),
11:("<$19>00, 계속 나아가지 않겠나","semantic_accuracy","先に進む를 먼저 간다는 뜻이 아닌 앞으로 진행한다는 의미로 옮겼다."),
26:("그린힐 의장은\n적극적으로 원로원 의원들의\n내부 개혁을 추진하는 모양이야<$0C>꽤나 미련을 털어 낸 모습인데\n이게 성황 호제아의 고발과\n무슨 관련이 있는 걸까?","naturalness","精力的의 번역에서 불필요한 성적 뉘앙스를 제거했다."),
34:("알콘대만 있으면\n공화국군의 승리는 약속된 것이나 다름없습니다.\n아무것도 두려워할 필요 없습니다","register","한 대사 안의 존댓말 종결을 통일했다."),
53:("큰일이네, 이 녀석……\n끝도 없이 짜증 나는데……\n있지, 이 녀석 좀 어떻게 해 줘","register","ヤバイ를 상황에 맞는 부정적 감탄으로 옮겼다."),
66:("기하 회랑 알비스・혼탁한 기억  제４층","naturalness","混濁する를 명사구 제목에 맞게 간결하게 다듬었다."),
68:("후후…… 좀처럼 포기할 줄 모르네.\n그럼 누나가 진짜\n비밀의 의미를 가르쳐 줄까?","semantic_accuracy","懲りない를 실패해도 포기하지 않는다는 의미로 바로잡았다."),
88:("『붉은 달』이 뭐 어쨌다는 거야!\n그딴 건 별것도 아니야\n이쪽엔 가족이 있다고<$0C>가족을 위해서라면\n오르키나든 지옥이든\n기꺼이 가 주겠어!","naturalness","メじゃねえ를 구어체 관용 표현으로 자연스럽게 옮겼다."),
95:("좋은 상품은 비싼 값에 팔리고\n조악한 물건은 헐값에 매입된다――\n이게 바로 자유 경쟁이지<$0C>이렇게 번성한 항구라면\n상인들의 생존 경쟁도 치열하겠어.\n끝까지 살아남으면 좋겠지만","semantic_accuracy","買い叩かれる를 싸게 팔린다가 아닌 헐값에 매입된다는 의미로 바로잡았다."),
106:("라르크. 나는 언제나 단 하나의\n해답을 찾아 헤매고 있습니다","naturalness","대화 문맥의 解를 자연스러운 '해답'으로 옮겼다."),
118:("bug040:비틀\nbug041:메탈 사슴벌레\nbug042:레이디버드\nbug043:나나호시\n그만두기","terminology","곤충 이름과 합성어 표기를 자연스럽게 다듬었다."),
120:("기하 회랑 알비스・혼탁한 기억  제２층","naturalness","混濁する를 명사구 제목에 맞게 간결하게 다듬었다."),
134:("그야 납득되잖아?\n움직이는 상자 안에 든 게\n코핀이었다니","naturalness","상자와 내용물의 관계를 자연스럽게 다듬었다."),
137:("머리가 멍하거든……\n생활에 활기가 부족한 거야, 분명.\n군인은 만남 같은 게 없으니까……","semantic_accuracy","出会い를 단순 접촉 기회가 아닌 연애 상대와의 만남으로 자연스럽게 옮겼다."),
153:("――솔직히 불안합니다<$0C>정권이 바뀐다는 건\n모든 게 바뀐다는 뜻이죠?\n……괜찮은 걸까요?","register","한 대사 안의 존댓말 종결을 통일했다."),
189:("라르크, 너무\n알스 전하께 폐를\n끼치면 안 돼<$0C>아무리 사이가 좋아도\n알스 전하께는 지켜야 할\n입장이 있으시니까","naturalness","수식 관계와 줄 호흡을 자연스럽게 정리했다."),
}
}

def load(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def write(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='\n') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
for n,edits in EDITS.items():
    bid=f'batch_{n:04d}'; dp=DRAFTS/f'{bid}.jsonl'; op=REVIEWED/f'{bid}.jsonl'; rp=REPORTS/f'{bid}_review.json'; rows=load(dp); mods=[]
    for i,(after,cat,why) in sorted(edits.items()):
        before=rows[i]['translation_ko']; rows[i]['translation_ko']=after
        if before!=after:mods.append({'row_index':i,'tm_id':rows[i]['tm_id'],'source_text':rows[i]['source_text'],'before':before,'after':after,'category':cat,'reason':why})
    write(op,rows)
    report={'schema':'arf-translation-independent-review-v1','batch_id':bid,'reviewer':REVIEWER,'draft_translator':DRAFT_AUTHOR,'draft_author':DRAFT_AUTHOR,'independent_review':True,'translation_engine_policy':'Codex internal models only','external_translation_services_used':[],'external_translation_models_or_apis_used':[],'sources':{'draft':f'work/translation/drafts/{bid}.jsonl','source':f'work/translation/tm_v2/batches/source/{bid}.jsonl','rules':'work/translation/tm_v2/TRANSLATION_RULES.md','style_guide':'work/translation/glossary_agent/style_guide.md','glossary':'work/translation/glossary_agent/glossary.csv'},'output':f'work/translation/reviewed/{bid}.jsonl','row_count':len(rows),'reviewed_row_count':len(rows),'modified_row_count':len(mods),'unchanged_row_count':len(rows)-len(mods),'modifications':mods,'verification_execution':{'status':'deferred_by_user_instruction','executed_tools':[],'not_executed':['validator','fit','encoding','boundary_audit'],'reason':'사용자 지시에 따라 기술 검증은 전체 번역 완료 후 마지막에 한 번만 수행한다.'}}
    rp.parent.mkdir(parents=True,exist_ok=True); rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{bid} rows={len(rows)} modified={len(mods)}')
