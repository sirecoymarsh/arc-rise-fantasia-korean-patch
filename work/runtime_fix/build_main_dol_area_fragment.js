const fs=require('fs');
const probe=JSON.parse(fs.readFileSync('work/catalog/text_probe_10.json','utf8'));
const dol=fs.readFileSync('work/disc_extracted/DATA/sys/main.dol');
const T=new Map(Object.entries({
 'トパジオン':'토파지온','ジャダ':'자다','帝都ディアマント':'제도디아만트','教都アントラクス':'교도안트락스','コピンの隠れ里':'코핀숨은마을','コピンの里':'코핀마을','首都カルブンクルス':'수도카르분쿨루스','聖都ベネトナーシュ':'성도베네트나슈','バトラキテス':'바트라키테스','エブル':'에블','オパルス':'오팔스','フェリス':'펠리스','レテアの森':'레테아숲','マンデルロー海岸':'만델로해안','ナブラ密林':'나블라밀림','ガウス地下道':'가우스지하도','エブル遺跡':'에블유적','グラ慈恵教会跡地':'그라자혜교회터','ガロア大裂溝':'갈루아대열곡','天衝塔ザイフェルト':'천충탑자이페르트','廃都ヒルベルト':'폐도힐베르트','エルゴード火山':'엘고드화산','ソリトン鍾乳洞':'솔리톤종유동','レゾルベント大氷壁':'레졸벤트대빙벽','空中回廊ラスカーダ':'공중회랑라스카다','空中回廊ベルクト':'공중회랑베르쿠트','聖地ノワーレ':'성지노와레','幾何回廊アルヴィス':'기하회랑알비스','眉月の宿':'초승달관','朔月の宿':'삭월관','古月の宿':'고월관','満月の宿':'만월관','半月の宿':'반월관','弧月の宿':'호월관','繊月の宿':'섬월관','教会':'교회','竜縛塔':'용박탑','オルキナ教大神殿':'오르키나교대신전','オルキナ教大神殿地下':'오르키나교대신전지하','海鳴りの道':'해명길','旗艦パーセヴァル':'기함파르세발','ディアマント城':'디아만트성','元老院':'원로원','クレイデル':'크레이델','ハーモニー':'하모니',
 'トパジオン宿屋ロビー':'토파지온여관로비','ジャダ帝国軍の詰め所':'자다제국군초소','ザムエル武芸塾：１Ｆ':'자무엘무예관:1F','ザムエル武芸塾：２Ｆ':'자무엘무예관:2F','ザムエル武芸塾：離れ':'자무엘무예관:별관','ベネトナーシュ夜':'베네트나슈밤','元老院会議場':'원로원회의장','元老院研究室':'원로원연구실','処刑場':'처형장','リフィア(リンダ)の家':'리피아(린다)의집','神殿':'신전','バトラキテス：会議室':'바트라키테스:회의실','オパルス：指令長官室':'오팔스:사령관실','盗賊船：船室':'도적선:선실','白月：会議室':'백월:회의실','白月：通信室':'백월:통신실','ノワーレの小屋内部':'노와레오두막안','コクピット':'조종석'
}));
const internal=/(イベント|用|回想|バトルフィールド|バトルフィール|予備枠|テストマップ|居住区00)/;
function est(s){let n=0;for(const c of s)n+=c.codePointAt(0)<=0x7f?1:2;return n;}
const out=[],excluded=[],errors=[];
for(const r of probe.records.filter(r=>r.offset>=0x3e7ee0&&r.offset<=0x3e9b60)){
 if(internal.test(r.text)){excluded.push({offset_hex:'0x'+r.offset.toString(16).toUpperCase(),source_text:r.text,reason:'explicit_event_test_or_internal_map_label'});continue;}
 const ko=T.get(r.text);if(!ko){errors.push({offset_hex:'0x'+r.offset.toString(16),source:r.text,error:'translation_missing'});continue;}
 const n=est(ko);if(n>r.capacity_to_nul){errors.push({offset_hex:'0x'+r.offset.toString(16),source:r.text,target:ko,capacity:r.capacity_to_nul,estimated:n,error:'over_capacity'});continue;}
 const raw=dol.subarray(r.offset,r.offset+r.byte_length).toString('hex').toUpperCase();if(raw!==r.raw_hex.toUpperCase()){errors.push({offset_hex:'0x'+r.offset.toString(16),error:'raw_mismatch'});continue;}
 out.push({schema:'arf-main-dol-translation-v1',file:'DATA/sys/main.dol',file_sha256:probe.source_sha256.toUpperCase(),offset:r.offset,offset_hex:'0x'+r.offset.toString(16).toUpperCase().padStart(8,'0'),byte_length:r.byte_length,capacity_to_nul:r.capacity_to_nul,source_encoding:'EUC-JP',source_text:r.text,source_raw_hex:r.raw_hex.toUpperCase(),translation_ko:ko,estimated_target_bytes:n,context:'세이브/지역 상태에 사용 가능한 상위 지역명',lane:'area_name',visibility:'runtime_user_visible',provenance:'Codex internal model',external_translation_used:false});
}
fs.writeFileSync('work/runtime_fix/main_dol_area_fragment.jsonl',out.map(x=>JSON.stringify(x)).join('\n')+'\n','utf8');
fs.writeFileSync('work/runtime_fix/main_dol_area_fragment_report.json',JSON.stringify({candidate_count:97,selected:out.length,excluded,errors},null,2)+'\n','utf8');
console.log(JSON.stringify({selected:out.length,excluded:excluded.length,error_count:errors.length,errors},null,2));
