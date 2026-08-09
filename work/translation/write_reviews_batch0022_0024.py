import json
from pathlib import Path


ROOT = Path("work/translation")
SOURCE_ROOT = ROOT / "tm_v2" / "batches" / "source"
DRAFT_ROOT = ROOT / "drafts"
REVIEWED_ROOT = ROOT / "reviewed"
REVIEWS_ROOT = ROOT / "reviews"


CORRECTIONS = {
    "batch_0022": {
        "ARF-TM-F9481ACD2389CC34C3FA": {
            "after": "전체에게 무속성 피해\n추가 효과: 상태 이상",
            "category": "terminology",
            "reason": "범위 효과 문장의 승인 표기인 ‘전체에게’를 적용했다.",
        },
        "ARF-TM-F9E2E357A791D6AB4B6E": {
            "after": "음의 시대의 거석에서 탄생한 지팡이.\n소지자의 몸을 견고한 대지의 가호가 감싼다",
            "category": "particle",
            "reason": "‘음의 시대의 거석’으로 관형 관계를 분명히 했다.",
        },
        "ARF-TM-FD9E697C70F6CA82059C": {
            "after": "옛 가르침의 <$13>14<$1F>00011D<$1F>01<$13>00와\n결별하며 생겨난\n새로운 가르침 중 하나.\n창조와 번영을 상징하는\n<$13>14<$1F>0000FF<$1F>01<$13>00를 신봉하며\n오르키나교가 믿는\n<$13>14<$1F>000102<$1F>01<$13>00를\n소멸과 쇠퇴를 상징하는\n사악한 신으로 여긴다",
            "category": "proper_noun",
            "reason": "승인 고유명사 ‘오르키나교’로 통일했다.",
        },
    },
    "batch_0023": {
        "ARF-TM-58D5992D89B11699B98C": {
            "after": "용사도에 후퇴란 없어!",
            "category": "terminology",
            "reason": "작중에서 하나의 수행 체계로 쓰이는 ‘勇者道’를 ‘용사도’로 통일했다.",
        },
        "ARF-TM-7331DA7DF8FE479A1058": {
            "after": "너희의 힘과 유대가 굳건하다면\n새로운 공격이 탄생할 것이다",
            "category": "naturalness",
            "reason": "유대의 확고함을 나타내도록 자연스러운 한국어로 다듬었다.",
        },
        "ARF-TM-82EEE7EDFC57BCAF3137": {
            "after": "몬스터들이 서로\n광소술을 조합해 쓴 거야",
            "category": "meaning",
            "reason": "몬스터들이 동료끼리 광소술을 조합하여 사용했다는 의미를 명확히 했다.",
        },
        "ARF-TM-84D4209D067710878470": {
            "after": "이런, 요즘 몬스터는\n하는 짓도 참 치밀하네",
            "category": "naturalness",
            "reason": "‘芸が細かい’의 문맥상 의미를 자연스럽게 옮겼다.",
        },
        "ARF-TM-85182D838A95053A2314": {
            "after": "대체 <$15>D4를 얼마나\n갖고 있슴까",
            "category": "speaker_voice",
            "reason": "오타처럼 보이던 어미를 니콜의 승인 말투인 ‘~슴까’로 정리했다.",
        },
        "ARF-TM-8F5DD0069D4673A25838": {
            "after": "아직 본래의 힘이 잠들어 있다고\n말하는 거다",
            "category": "meaning",
            "reason": "본래의 힘을 의도적으로 재운다는 뜻이 아니라 아직 잠재되어 있다는 뜻으로 바로잡았다.",
        },
        "ARF-TM-9DD6598610D71B6D0300": {
            "after": "혼자서 여러 행동을 조합하면\n더 강력한 행동을\n만들어 낼 수 있어",
            "category": "meaning",
            "reason": "한 사람이 자신의 복수 행동을 조합하는 기능임을 분명히 했다.",
        },
        "ARF-TM-C536A6E6963E7897ADA3": {
            "after": "엑셀 액트는 강력하다.\n그렇기에\n언제나 쓸 수 있는 것은 아니다",
            "category": "naturalness",
            "reason": "‘강대하다’를 기술의 위력을 나타내는 자연스러운 ‘강력하다’로 고쳤다.",
        },
        "ARF-TM-CC5E82871F4F5DC93589": {
            "after": "그러니까 자기 <$15>D4만\n생각해서는 싸워 나갈 수 없어",
            "category": "meaning",
            "reason": "협력 전투를 운용할 수 없다는 ‘やっていけない’의 의미를 명확히 했다.",
        },
        "ARF-TM-2E5E8C574B32C7CFC6AD": {
            "after": "제가 산성에 약했군요",
            "category": "meaning",
            "reason": "‘酸’을 산(山)으로 오해할 수 없도록 산성으로 명확히 옮겼다.",
        },
        "ARF-TM-58C08369EAF82D0D9C35": {
            "after": "미리 말씀드리지만\n저는 맛없거든요?",
            "category": "function",
            "reason": "질문이 아니라 자신은 맛없다는 경고성 어조가 드러나도록 고쳤다.",
        },
        "ARF-TM-A54392BDA00D729EA32D": {
            "after": "말과 맞먹는다는 소리를 들은 적이 있습니다",
            "category": "meaning",
            "reason": "‘ウマナミ(馬並み)’의 말과 견줄 만하다는 말장난을 의미가 전달되게 옮겼다.",
        },
        "ARF-TM-64CAEF1E46F67D23478D": {
            "after": "오팔루스 일이 먼저잖아?",
            "category": "proper_noun",
            "reason": "승인 지명 ‘오팔루스’로 통일했다.",
        },
        "ARF-TM-202605BD2E9F35864D82": {
            "after": "얼핏 보면 조작반 무늬 같은 게\n전혀 다르긴 한데요. 그래도 익숙해지면\n제국군 비광정과 똑같슴다",
            "category": "naturalness",
            "reason": "조작반의 외형은 다르지만 익숙해지면 제국군 비광정과 같다는 대조 관계를 자연스럽게 정리했다.",
        },
    },
    "batch_0024": {
        "ARF-TM-35A4C4FCC1F66FD14C52": {
            "after": "지체 없이 뛰어들어\n뒤로 손을 뻗어 문을 닫고 히죽〜",
            "category": "meaning",
            "reason": "‘後ろ手に’를 등 뒤에서 손을 뻗어 문을 닫는 동작으로 정확히 옮겼다.",
        },
        "ARF-TM-432EB2C1B6C97FEFB6A3": {
            "after": "하지만 그것도\n이 아이가 힘을 더\n되찾을 때까지만 해당되는 얘기니까!",
            "category": "naturalness",
            "reason": "기능상의 제약이 힘을 되찾기 전까지만이라는 뜻이 자연스럽게 이어지도록 다듬었다.",
        },
        "ARF-TM-48BA29FE0CFB275F2A3E": {
            "after": "난 공인 용병이 됐을 때\n기본 훈련은 받았지만\n세실은 군인이 아니잖아",
            "category": "terminology",
            "reason": "기존 설정 용어 ‘공인 용병’으로 통일했다.",
        },
        "ARF-TM-5655AA06821E69A13857": {
            "after": "길드에 보고하러 가는 거네",
            "category": "function",
            "reason": "다음 목적지가 길드 보고임을 확인하는 대사 기능에 맞게 고쳤다.",
        },
        "ARF-TM-58373A38AD26975618EF": {
            "after": "와, 좋겠다.\n아이에게 비광정을 쓰게 해 주다니\n우리 때는 상상도 못 했어",
            "category": "particle",
            "reason": "비광정 사용을 허락받는 대상이 아이라는 관계를 명확히 했다.",
        },
        "ARF-TM-684BE9EC8C0BEC5DC981": {
            "after": "그건 아니지만\n탈 기회는 많이 있었어.\n그 뒤로는 혼자 익혔달까",
            "category": "meaning",
            "reason": "‘勝手に覚えた’를 저절로가 아니라 스스로 익혔다는 뜻으로 바로잡았다.",
        },
        "ARF-TM-954FEB1A6F1047C729F3": {
            "after": "설명을 부탁해도 될까\n우리 에이스 파일럿님",
            "category": "speaker_voice",
            "reason": "호칭 ‘さん’의 장난스러운 존칭을 살리고 한국어 소유 표현을 자연스럽게 했다.",
        },
        "ARF-TM-000483682AF8265976BE": {
            "after": "그리고 며칠 뒤\n놀람인지 기쁨인지 모를 라르크 씨의\n목소리가 들려왔습니다",
            "category": "naturalness",
            "reason": "놀람과 기쁨 중 어느 쪽인지 알 수 없는 목소리라는 서술을 자연스럽게 정리했다.",
        },
        "ARF-TM-00863EFA533B2E2D1A3E": {
            "after": "하지만…… 종복은\n소중히 대해야 해",
            "category": "terminology",
            "reason": "관련 작중 표기와 맞춰 ‘しもべ’를 ‘종복’으로 통일했다.",
        },
        "ARF-TM-00D9154F957B927F3FF6": {
            "after": "또 추락하는 건\n이 오빠가 사양할게",
            "category": "meaning",
            "reason": "비광정이 다시 추락하는 상황이라는 의미를 분명히 했다.",
        },
        "ARF-TM-015A85F31663AA24ED1D": {
            "after": "심각한 얼굴을 하고 있었지",
            "category": "naturalness",
            "reason": "회상 대사가 한국어 완성 문장으로 이어지도록 다듬었다.",
        },
        "ARF-TM-01EDDC040A6A08536F21": {
            "after": "그렇게 말해도\n길드의 의뢰도 뭣도 아니잖아",
            "category": "naturalness",
            "reason": "‘依頼でも何でもない’의 관용적 부정을 자연스럽게 옮겼다.",
        },
        "ARF-TM-01F6B101598EAF7E519E": {
            "after": "어떤 여자가 취향이야?",
            "category": "meaning",
            "reason": "특정 여성이 아니라 선호하는 여성상을 묻는 질문임을 명확히 했다.",
        },
        "ARF-TM-02092909CE7571121DB4": {
            "after": "그래.\n오이겐은 의외로\n대담하네",
            "category": "meaning",
            "reason": "‘意外に’의 뜻과 화제 표지를 빠짐없이 살렸다.",
        },
        "ARF-TM-021FA8668FF95D9A6BBB": {
            "after": "사람이 사람을 솎아 내는 건가",
            "category": "naturalness",
            "reason": "어색한 종결 표현을 독백형 의문문으로 바로잡았다.",
        },
        "ARF-TM-025680E81BC6963262A1": {
            "after": "라르크는\n우리가 이해해 주면 된다.\n그것이 라르크를 지탱해 줄 거라 생각한다",
            "category": "naturalness",
            "reason": "라르크를 이해하는 일이 그를 지지한다는 인과를 자연스럽게 연결했다.",
        },
        "ARF-TM-0272CBEB885F780A7397": {
            "after": "너희의 마음에\n이래라저래라하고 싶은 건 아니야.\n하지만――",
            "category": "meaning",
            "reason": "상대의 감정에 간섭하려는 것이 아니라는 의미를 명확히 했다.",
        },
        "ARF-TM-0357C7ABBC08ED5E0D74": {
            "after": "그렇군……\n의뢰라면 받아 줄 수도 있는데?",
            "category": "function",
            "reason": "문제를 의뢰로 받아 줄 의향을 제시하는 대사 기능을 분명히 했다.",
        },
        "ARF-TM-0392925E8222D39B9754": {
            "after": "너희가 품은 레온이라는\n이상적인 모습은 무너뜨리지 않으려 했다.\n하지만 결국――",
            "category": "meaning",
            "reason": "‘理想像’을 단순한 이상이 아니라 레온에 대한 이상적인 이미지로 구체화했다.",
        },
        "ARF-TM-05A40123C7D6C7F6B252": {
            "after": "네가 침략자가 됐을지도 모른다는 건가",
            "category": "context",
            "reason": "앞뒤 대화상 니콜의 두려움을 되짚는 말이므로 1인칭을 2인칭으로 바로잡았다.",
        },
        "ARF-TM-06DF932D8320E1B30E2C": {
            "after": "더 커졌어.\n코핀 마을에서 본 것보다\n훨씬 더 흉악해 보여",
            "category": "meaning",
            "reason": "괴물의 ‘質が悪い’를 품질이 아니라 더 고약하고 위험하다는 뜻으로 옮겼다.",
        },
        "ARF-TM-06FCF6B9DCBBB1648D26": {
            "after": "이번에는 반드시\n맛있게 먹혀 드리겠습니다!\n자, 사양하지 마세요!",
            "category": "naturalness",
            "reason": "‘먹혀 보이겠습니다’의 잘못된 보조 용언 결합을 바로잡고 코믹한 자청 어조를 살렸다.",
        },
        "ARF-TM-07E291651793E0269629": {
            "after": "앞으로도 계속\n정신 못 차릴 거지\n당신들은……",
            "category": "naturalness",
            "reason": "앞으로도 교훈을 얻지 못할 것이라는 ‘こりない’의 의미를 자연스럽게 옮겼다.",
        },
        "ARF-TM-08B2246EE68AEE4A0308": {
            "after": "그 나이에 그 기특함……\n이 언니, 반할 것 같아",
            "category": "meaning",
            "reason": "‘若さ’와 ‘いじらしさ’를 나이와 기특한 마음가짐이라는 문맥에 맞게 옮겼다.",
        },
        "ARF-TM-0A5540AC2269A0ECBC03": {
            "after": "노스 노와레교의 성도\n베네트나슈",
            "category": "proper_noun",
            "reason": "승인 지명 ‘베네트나슈’로 통일했다.",
        },
    },
}


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_batch(batch_id: str, corrections: dict):
    source_path = SOURCE_ROOT / f"{batch_id}.jsonl"
    draft_path = DRAFT_ROOT / f"{batch_id}.jsonl"
    reviewed_path = REVIEWED_ROOT / f"{batch_id}.jsonl"
    review_path = REVIEWS_ROOT / f"{batch_id}_review.json"

    source_rows = read_jsonl(source_path)
    draft_rows = read_jsonl(draft_path)
    draft_by_id = {row["tm_id"]: row for row in draft_rows}
    modifications = []

    for row in source_rows:
        tm_id = row["tm_id"]
        before = draft_by_id[tm_id]["translation_ko"]
        correction = corrections.get(tm_id)
        after = correction["after"] if correction else before
        row["translation_ko"] = after
        if correction:
            modifications.append(
                {
                    "tm_id": tm_id,
                    "source_text": row["source_text"],
                    "before": before,
                    "after": after,
                    "category": correction["category"],
                    "reason": correction["reason"],
                }
            )

    REVIEWED_ROOT.mkdir(parents=True, exist_ok=True)
    REVIEWS_ROOT.mkdir(parents=True, exist_ok=True)
    reviewed_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in source_rows) + "\n",
        encoding="utf-8",
    )

    report = {
        "schema": "arf-translation-independent-review-v1",
        "batch_id": batch_id,
        "reviewer": "/root/translate_batch_0009",
        "draft_translator": "/root/translate_batch_0008",
        "draft_author": "/root/translate_batch_0008",
        "independent_review": True,
        "translation_engine_policy": "Codex internal models only",
        "external_translation_services_used": [],
        "external_translation_models_or_apis_used": [],
        "source": source_path.as_posix(),
        "draft": draft_path.as_posix(),
        "reviewed_output": reviewed_path.as_posix(),
        "reviewed_units": len(source_rows),
        "modified_units": len(modifications),
        "unchanged_units": len(source_rows) - len(modifications),
        "review_dimensions": [
            "meaning",
            "function",
            "numeric fidelity",
            "proper nouns",
            "natural Korean",
            "particles",
            "control tokens",
            "line breaks",
        ],
        "modifications": modifications,
        "verification_execution": {
            "status": "deferred_by_user_instruction",
            "executed_tools": [],
            "not_executed": ["validator", "fit", "encoding", "boundary_audit"],
            "note": "사용자 지시에 따라 별도 validator, fit, encoding, boundary audit를 실행하지 않았다.",
        },
    }
    review_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(modifications)


for batch, changes in CORRECTIONS.items():
    count = write_batch(batch, changes)
    print(f"{batch}: {count}")
