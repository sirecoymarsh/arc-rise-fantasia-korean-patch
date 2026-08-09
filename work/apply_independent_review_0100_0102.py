import json
from pathlib import Path

BASE = Path('work/translation')
REVIEWER = '/root/review_batch_0058_0060'
DRAFT_AUTHOR = '/root/translate_batch_0009'

edits = {
    '0100': {
        15: ('서두르자!', 'meaning', '의지형 대사를 자연스러운 청유형으로 바로잡음.'),
        30: ('수많은 불경한 자가\n디아만트성 안에\n투옥되어 있다<$0C>그렇게 되고 싶지 않다면\n어서 집으로 돌아가\n갓난아이처럼 떨며 잠들어라', 'terminology', '금지 변형인 띄어 쓴 지명을 고정 표기인 디아만트성으로 교정함.'),
        48: ('■■■사전 준비 2■■■\n', 'meaning', '仕込み를 문맥에 맞는 사전 준비로 교정함.'),
        108: ('제국의 마하트 폐하께서 총애하던 자가\n이 도시에서 크게 날뛰었다고?\n……나도 그 자리에 있고 싶었어!<$0C>반항기의 알스 황자는\n어떤 마술을 써서 거대한 용을\n불러냈다잖아!!<$0C>……정말 보고 싶었는데', 'naturalness', '秘蔵っ子의 의미와 황제 호칭에 맞게 표현을 다듬음.'),
        129: ('다시 방문해 주시기를\n기다릴 것 같은 예감……', 'naturalness', '원문의 장난스러운 추측형 어감을 자연스럽게 복원함.'),
    },
    '0101': {
        9: ('디아만트성으로 가실 거라면\n이쪽 구동 기관을 이용하십시오', 'terminology', '고정 지명 디아만트성의 표기를 통일함.'),
        26: ('용박탑은 제국 사람들의 생활을\n떠받치는 중요 시설이라\n경비에 힘을 쏟고 있지 말입니다', 'speaker_voice', 'であります의 서투른 군인 말투를 자연스러운 한국어 군대식 말투로 살림.'),
        56: ('우리 오르키나 백성은\n제국의 죄를 용서하고\n알스 황제를 받아들입시다<$0C>그리고 우리의 큰 소원을\n붉은 디바 아델 님께\n바치는 겁니다……', 'naturalness', '大願을 문맥상 오해 없는 자연스러운 표현으로 교정함.'),
        71: ('저기 있는 친구에게\n수상한 물건을 강매당해\n어쩔 줄 모르고 있습니다<$0C>저는 사용법을\n모르니 당신에게\n드리겠습니다……', 'meaning', '売りつけられて의 강매당했다는 의미를 복원함.'),
        172: ('디아만트성 D02(오른쪽)로\n', 'terminology', '고정 지명 디아만트성의 표기를 통일함.'),
    },
    '0102': {
        15: ('누, 누가 도움을 불러 줘!\n이 사람 크게 다쳤어!!', 'meaning', '구조 요청이라는 원문의 의미를 명확하게 복원함.'),
        46: ('이건 받을 수 없어<$0C>나는 아직 저항군에\n가입한 게 아니니까', 'terminology', 'レジスタンス를 용어집 고정 표기인 저항군으로 교정함.'),
        55: ('amp030:플라이 피시\namp031:데저트 피시\namp032:캣피시\namp033:레모라\n그만둔다', 'ui', '동일 계열 메뉴의 종결 표현을 그만둔다로 통일함.'),
        130: ('기, 기기기기\n의장님!?', 'speaker_voice', '원문의 당황한 말더듬을 임의 감탄으로 바꾸지 않고 복원함.'),
        131: ('이거…… 형한테 줄게.\n내게는 이제 필요 없으니까……', 'speaker_voice', '남자아이 화자의 お兄ちゃん을 성별에 맞는 형으로 교정함.'),
        164: ('지하 폐허 D04(저항군 거점)로\n', 'terminology', 'レジスタンス를 용어집 고정 표기인 저항군으로 교정함.'),
        178: ('엘레나 님은 내게 맡겨.\n하지만 저 사람에게 최고의 약은\n라르크, 바로 너야', 'naturalness', '１番の薬을 부자연스러운 수량 표현 대신 최고의 약으로 교정함.'),
    },
}

for b, batch_edits in edits.items():
    draft_path = BASE / 'drafts' / f'batch_{b}.jsonl'
    source_path = BASE / 'tm_v2' / 'batches' / 'source' / f'batch_{b}.jsonl'
    out_path = BASE / 'reviewed' / f'batch_{b}.jsonl'
    report_path = BASE / 'reviews' / f'batch_{b}_review.json'
    rows = [json.loads(x) for x in draft_path.read_text(encoding='utf-8').splitlines()]
    source_rows = [json.loads(x) for x in source_path.read_text(encoding='utf-8').splitlines()]
    modifications = []
    for idx, (after, category, reason) in batch_edits.items():
        before = rows[idx]['translation_ko']
        rows[idx]['translation_ko'] = after
        modifications.append({
            'row_index': idx,
            'tm_id': rows[idx]['tm_id'],
            'source_text': source_rows[idx]['source_text'],
            'before': before,
            'after': after,
            'category': category,
            'reason': reason,
        })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(''.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) + '\n' for x in rows), encoding='utf-8')
    report = {
        'schema': 'arf-translation-independent-review-v1',
        'batch_id': f'batch_{b}',
        'reviewer': REVIEWER,
        'draft_translator': DRAFT_AUTHOR,
        'draft_author': DRAFT_AUTHOR,
        'independent_review': True,
        'translation_engine_policy': 'Codex internal models only',
        'external_translation_services_used': [],
        'external_translation_models_or_apis_used': [],
        'sources': {
            'draft': str(draft_path).replace('\\', '/'),
            'source': str(source_path).replace('\\', '/'),
            'rules': 'work/translation/tm_v2/TRANSLATION_RULES.md',
            'style_guide': 'work/translation/glossary_agent/style_guide.md',
            'glossary': 'work/translation/glossary_agent/glossary.csv',
        },
        'output': str(out_path).replace('\\', '/'),
        'row_count': len(rows),
        'reviewed_row_count': len(rows),
        'modified_row_count': len(modifications),
        'unchanged_row_count': len(rows) - len(modifications),
        'modifications': modifications,
        'technical_validation': 'not run; deferred to final project stage per user instruction',
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'batch_{b} rows={len(rows)} edits={len(modifications)}')
