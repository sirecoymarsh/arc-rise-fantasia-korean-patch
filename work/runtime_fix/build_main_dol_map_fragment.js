const fs=require('fs');
const probe=JSON.parse(fs.readFileSync('work/catalog/text_probe_10.json','utf8'));
const dol=fs.readFileSync('work/disc_extracted/DATA/sys/main.dol');
const byOffset=new Map(probe.records.map(r=>[r.offset,r]));

// Runtime map/location captions. A one-byte leading value in several rows is
// a renderer control/index byte represented as ASCII by the probe; it is
// preserved verbatim below and is not translated.
const T=new Map(Object.entries({
  'コピンの大樹':'코핀대수','コピンの石舞台':'코핀돌무대','大橋':'대교','噴水広場':'분수광장','工場地区':'공장지구','港湾地区':'항만지구','上層地区':'상층지구','ディアマント城':'디아만트성','森の奥':'숲속','うねる小道':'굽이샛길','飛び石のせせらぎ':'징검여울','崖の上　北側':'절벽 위 북쪽','大階段':'대계단','大裂溝谷底':'대열곡바닥','崖の上　南側':'절벽 위 남쪽','のどかな通り':'한적한거리','環状庭園':'환상정원','芸術街':'예술가','港湾区':'항만구','娯楽街':'오락가','歌劇場通り':'극장거리','工場区':'공장구','共和国元老院':'공화국원로원','熱砂の集落':'열사촌락','崖下の小道':'절벽밑길','滝の入り江':'폭포물굽이','ならず者の住処':'무법자소굴','秘密の港':'비밀항구','黄金回廊':'황금회랑','黄金回廊　右翼':'황금회랑 우익','黄金回廊　左翼':'황금회랑 좌익','黄金回廊　右翼奥':'황금회랑 우익안','黄金回廊　左翼奥':'황금회랑 좌익안','契約の間':'계약의방','封印門前':'봉인문앞','塔１階':'탑1층','塔地下１階':'탑지하1층','束縛の間':'속박의방','塔最上層':'탑최상층','分かれ道':'갈림길','蜜花の小道':'밀화샛길','極彩色の迷宮':'극채색미궁','腐臭の間':'부취의방','干満の道':'간만의길','黒竜の祭壇':'흑룡제단','外周階段':'외곽계단','輝火書院':'휘화서원','地下１階　通路':'지하1층 통로','地下２階　通路':'지하2층 통로','地下２階　倉庫':'지하2층 창고','地下３階　通路':'지하3층 통로','地下３階　機械室':'지하3층 기계실','地下４階　制御室':'지하4층 제어실','しずくの暗路':'물방울암로','崩れかけた道':'무너진길','海底の泉':'해저샘','こだまの暗路':'메아리암로','声無き遊び場':'침묵놀이터','野菊の礼拝堂':'들국화예배당','地下の貯蔵庫':'지하저장고','地下施設３階':'지하시설3층','地下施設２階':'지하시설2층','地下施設１階':'지하시설1층','害なす道':'해악의길','迫る道':'압박길','牙の檻':'이빨굴','開く道':'열린길','エントランスホール':'입구홀','エレベータホール':'승강기홀','コンソールフロア':'콘솔플로어','ラウンドフロア０１':'라운드플로어01','ラウンドフロア０２':'라운드플로어02','ラウンドフロア０３':'라운드플로어03','ラウンドフロア０４':'라운드플로어04','ラウンドフロア０５':'라운드플로어05','ラウンドフロア０６':'라운드플로어06','ラウンドフロア０７':'라운드플로어07','ラウンドフロア０８':'라운드플로어08','ラウンドフロア０９':'라운드플로어09','ラウンドフロア１０':'라운드플로어10','ヘブンズラダー':'헤븐즈래더','コントロールルーム':'제어실','灰の山道':'잿빛산길','溶岩のほとり':'용암가','血脈通路':'혈맥통로','赤熱の谷':'적열곡','灼熱の橋':'작열교','奇石の森':'기암숲','岩の高架':'바위고가','蛍石の道':'형석길','三叉路':'삼거리','青い滝':'청폭포','空洞入口':'공동입구','中央通':'중앙로','貴人街':'귀인가','大空洞':'대공동','砂岩の道':'사암길','甲板':'갑판','船首側通路':'선수통로','船尾側通路':'선미통로','艦橋':'함교','鏡の間':'거울방','執権の間　通路':'집정실 통로','兵士控え室':'병사대기실','地下牢':'지하옥','謁見の間　踊り場':'알현실 층계참','謁見の間':'알현실','執権の間　執務室':'집정실 사무실','議場前':'의장앞','議場玄関':'의장입구','一般房':'일반방','懲罰房':'징벌방','特別房':'특별방','処刑場前':'처형장앞','エアポート':'에어포트','連絡通路':'연결통로','警戒区域':'경계구역','中央制御室':'중앙제어실','通信室前':'통신실앞','コンコース':'콩코스','定理の間':'정리의방','花緑青の路':'화록청길','珊瑚の回廊':'산호회랑','柅緒の回廊':'단서회랑','混沌の回廊':'혼돈회랑','破綻の空間':'파탄공간','困惑の回廊':'곤혹회랑','友愛の空間':'우애공간','疑念の回廊':'의심회랑','信義の空間':'신의공간','未必の回廊':'미필회랑','系譜の空間':'계보공간','回帰と永遠の三叉路':'회귀와영원의삼거리','選択の間':'선택의방','現世の中枢':'현세중추','石柱の参道':'석주참도','氷鏡の間':'빙경의방','遺跡中腹':'유적중턱','永久結氷':'영구결빙','銀氷の間':'은빙의방','雪姫の祭壇':'설희제단','有相無相の迷い路':'유상무상의미로','商業区画':'상업구역','拠点区画':'거점구역','聖堂前広場':'성당앞광장','船着場':'선착장','住宅街':'주택가','軍部施設':'군부시설','襲撃された町':'습격당한마을','墓苑':'묘원','大聖堂前通り':'대성당앞길','庭園通り':'정원길','軍事基地跡':'군사기지터','井戸端':'우물가','工場':'공장','石畳と雪だるまの路':'돌길과눈사람길','学び舎':'학교','目覚めた人々の間':'깨어난자들의방','眠る人々の間':'잠든자들의방','ハーモニー':'하모니',
  'トパジオン宿屋ロビー':'토파지온여관로비','ジャダ帝国軍の詰め所':'자다제국군초소','ザムエル武芸塾：１Ｆ':'자무엘무예관:1F','ザムエル武芸塾：２Ｆ':'자무엘무예관:2F','ザムエル武芸塾：離れ':'자무엘무예관:별관','ベネトナーシュ夜':'베네트나슈 밤','竜縛塔イベント飛空挺':'용박탑이벤트비광정','ルフンガ用イベント':'루푼가용이벤트','元老院会議場':'원로원회의장','元老院研究室':'원로원연구실','処刑場':'처형장','リフィア(リンダ)の家':'리피아(린다)의집','神殿':'신전','バトラキテス：会議室':'바트라키테스:회의실','遺跡Ｂイベント用':'유적B이벤트용','オパルス：指令長官室':'오팔스:사령관실','ＰＣ用飛空艇ブリッジ':'PC용비광정함교','盗賊船：船室':'도적선:선실','白月：会議室':'백월:회의실','白月：通信室':'백월:통신실','白月：シムマフ回想用':'백월:심마프회상용','ノワーレの小屋内部':'노와레오두막안','ジャダバトルフィール':'자다배틀필드','神竜バトルフィールド':'신룡배틀필드','白月の居住区00 セピア':'백월거주구00 세피아','バトラ広場Ｂイベント':'바트라광장B이벤트','オーリエンスイベント':'오리엔스이벤트','コクピット':'조종석','イベントムービー用29B':'이벤트영상용29B','イベントムービー用30B':'이벤트영상용30B',
  '開かれた地':'열린땅','忘れられた地':'잊힌땅','熱せられた地':'달아오른땅','包まれた地':'감싸인땅','吹かれた地':'바람부는땅','閉ざされた地':'닫힌땅','？？？':'???','幾何回廊アルヴィス':'기하회랑알비스'
}));

function splitPrefix(s){let i=0;while(i<s.length&&s.charCodeAt(i)<=0x7f)i++;return [s.slice(0,i),s.slice(i)];}
function est(s){let n=0;for(const c of s)n+=c.codePointAt(0)<=0x7f?1:2;return n;}
const out=[],errors=[],excluded=[];
for(const r of probe.records.filter(r=>r.offset>=0x3f072a&&r.offset<=0x3f1dd9)){
  const [prefix,base]=splitPrefix(r.text);
  if(base==='予備枠'){excluded.push({offset_hex:'0x'+r.offset.toString(16).toUpperCase(),source_text:r.text,reason:'reserved_internal_slot'});continue;}
  const ko=T.get(base);
  if(!ko){errors.push({offset_hex:'0x'+r.offset.toString(16),source:r.text,base,error:'translation_missing'});continue;}
  const target=prefix+ko,n=est(target);
  if(n>r.capacity_to_nul){errors.push({offset_hex:'0x'+r.offset.toString(16),source:r.text,target,capacity:r.capacity_to_nul,estimated:n,error:'over_capacity'});continue;}
  const raw=dol.subarray(r.offset,r.offset+r.byte_length).toString('hex').toUpperCase();if(raw!==r.raw_hex.toUpperCase()){errors.push({offset_hex:'0x'+r.offset.toString(16),error:'raw_mismatch'});continue;}
  out.push({schema:'arf-main-dol-translation-v1',file:'DATA/sys/main.dol',file_sha256:probe.source_sha256.toUpperCase(),offset:r.offset,offset_hex:'0x'+r.offset.toString(16).toUpperCase().padStart(8,'0'),byte_length:r.byte_length,capacity_to_nul:r.capacity_to_nul,source_encoding:'EUC-JP',source_text:r.text,source_raw_hex:r.raw_hex.toUpperCase(),translation_ko:target,estimated_target_bytes:n,context:'런타임 지역/맵 표시명',lane:'map_name',visibility:'runtime_user_visible',provenance:'Codex internal model',external_translation_used:false});
}
fs.writeFileSync('work/runtime_fix/main_dol_map_fragment.jsonl',out.map(x=>JSON.stringify(x)).join('\n')+'\n','utf8');
fs.writeFileSync('work/runtime_fix/main_dol_map_fragment_report.json',JSON.stringify({candidate_count:226,selected:out.length,excluded,errors},null,2)+'\n','utf8');
console.log(JSON.stringify({selected:out.length,excluded:excluded.length,error_count:errors.length,errors},null,2));
