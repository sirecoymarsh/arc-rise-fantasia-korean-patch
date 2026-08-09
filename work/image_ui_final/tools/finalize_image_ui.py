#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
BASE = ROOT / "work" / "image_ui_final"
DISC = ROOT / "work" / "disc_extracted" / "DATA" / "files"
sys.path.insert(0, str(HERE.parent))
from wtmd_pipeline import decompress_lz10, parse_wtmd


def sha(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def wtm_check(original: Path, patched: Path, render: Path):
    a=original.read_bytes();b=patched.read_bytes();ha=parse_wtmd(a);hb=parse_wtmd(b)
    with Image.open(render) as im:size=list(im.size);alpha=list(im.convert('RGBA').getchannel('A').getextrema())
    return {
        "original":str(original.relative_to(ROOT)).replace('\\','/'),"patched":str(patched.relative_to(ROOT)).replace('\\','/'),
        "original_sha256":sha(original),"patched_sha256":sha(patched),"original_bytes":len(a),"patched_bytes":len(b),
        "size_equal":len(a)==len(b),"header_and_palette_equal":a[:ha['image_pos']]==b[:hb['image_pos']],
        "dimensions_equal":(ha['width'],ha['height'])==(hb['width'],hb['height'])==tuple(size),
        "gx_format_equal":ha['gx']==hb['gx'],"palette_format_equal":ha['pal']==hb['pal'],"render_dimensions":size,"render_alpha_range":alpha,
        "changed":a!=b,"pass":len(a)==len(b) and a[:ha['image_pos']]==b[:hb['image_pos']] and ha['gx']==hb['gx'] and ha['pal']==hb['pal'] and (ha['width'],ha['height'])==tuple(size) and a!=b,
    }


def cxd_check(original: Path, patched: Path, leaf: Path, render: Path):
    oa=original.read_bytes();pa=patched.read_bytes();a=decompress_lz10(oa);b=decompress_lz10(pa);ha=parse_wtmd(a);hb=parse_wtmd(b)
    with Image.open(render) as im:size=list(im.size);alpha=list(im.convert('RGBA').getchannel('A').getextrema())
    leaf_bytes=leaf.read_bytes()
    return {
        "original":str(original.relative_to(ROOT)).replace('\\','/'),"patched":str(patched.relative_to(ROOT)).replace('\\','/'),"leaf":str(leaf.relative_to(ROOT)).replace('\\','/'),
        "original_sha256":sha(original),"patched_sha256":sha(patched),"original_compressed_bytes":len(oa),"patched_compressed_bytes":len(pa),
        "decompressed_bytes_equal":len(a)==len(b),"leaf_matches_decompressed_payload":leaf_bytes==b,
        "header_and_palette_equal":a[:ha['image_pos']]==b[:hb['image_pos']],"dimensions_equal":(ha['width'],ha['height'])==(hb['width'],hb['height'])==tuple(size),
        "gx_format_equal":ha['gx']==hb['gx'],"palette_format_equal":ha['pal']==hb['pal'],"render_dimensions":size,"render_alpha_range":alpha,
        "changed":a!=b,"pass":len(a)==len(b) and leaf_bytes==b and a[:ha['image_pos']]==b[:hb['image_pos']] and ha['gx']==hb['gx'] and ha['pal']==hb['pal'] and (ha['width'],ha['height'])==tuple(size) and a!=b,
    }


def main():
    checks=[];targets=[]
    for n in ['strapA_jp','strapB_jp']:
        o=DISC/'Sys'/f'{n}.wtm';p=BASE/'payloads'/'Sys'/f'{n}.wtm';r=BASE/'reports'/'reencoded_render'/f'{n}.png'
        checks.append(wtm_check(o,p,r));targets.append({"target":f"Sys/{n}.wtm","payload":str(p.relative_to(ROOT)).replace('\\','/'),"method":"replace physical file during disc rebuild","asset_count":1})
    o=ROOT/'work'/'pristine'/'Sys'/'system.vol'/'nowloading.wtm';p=BASE/'payloads'/'Sys'/'0053__nowloading.wtm';r=BASE/'reports'/'reencoded_render'/'nowloading.png'
    checks.append(wtm_check(o,p,r));targets.append({"target":"Sys/system.vol::entry 53 nowloading.wtm","payload":str(p.relative_to(ROOT)).replace('\\','/'),"method":"replace same-size RTDP member in cumulative system.vol build","asset_count":1})

    title_original=BASE/'extracted'/'title_vol'/'payloads';title_patched=BASE/'payloads'/'Title'/'title_vol_payloads'
    title_names=['0000__title_pressanybutton.wtm','0001__title_logo.wtm','0002__title_newgame01.wtm','0003__title_newgame02.wtm','0004__title_continue01.wtm','0005__title_continue02.wtm']
    for n in title_names:
        checks.append(wtm_check(title_original/n,title_patched/n,BASE/'reports'/'reencoded_render'/(Path(n).stem+'.png')))
    title_payload=BASE/'payloads'/'Title'/'title.vol';sys_title_payload=BASE/'payloads'/'Sys'/'title.vol'
    for t,p in [('Title/title.vol',title_payload),('Sys/title.vol',sys_title_payload)]:
        targets.append({"target":t,"payload":str(p.relative_to(ROOT)).replace('\\','/'),"method":"replace physical RTDP archive during disc rebuild","asset_count":6,"changed_entries":[0,1,2,3,4,5]})

    interface_dir=DISC/'interface';payload_dir=BASE/'payloads'/'interface';leaf_dir=BASE/'payloads'/'wtmd_leaves';render_dir=BASE/'reports'/'reencoded_render'
    cxd_names=[p.name for p in sorted(interface_dir.glob('tex_loc_title_*_wtm.cxd'))]+['tex_casino_intro_bj_wtm.cxd','tex_casino_intro_poker_wtm.cxd']
    for n in cxd_names:
        base=Path(n).stem
        checks.append(cxd_check(interface_dir/n,payload_dir/n,leaf_dir/f'{base}.wtm',render_dir/f'{base}.png'))
        targets.append({"target":f"interface/{n}","payload":str((payload_dir/n).relative_to(ROOT)).replace('\\','/'),"method":"replace LZ10 CXD physical file during disc rebuild","asset_count":1})

    original_title_hash=sha(DISC/'Title'/'title.vol');original_sys_title_hash=sha(DISC/'Sys'/'title.vol')
    original_manifest=json.loads((BASE/'extracted'/'title_vol'/'manifest.json').read_text(encoding='utf-8'))
    post_manifest=json.loads((BASE/'reports'/'title_vol_post'/'manifest.json').read_text(encoding='utf-8'))
    orig_payloads=sorted((BASE/'extracted'/'title_vol'/'payloads').iterdir())
    post_payloads=sorted((BASE/'reports'/'title_vol_post'/'payloads').iterdir())
    changed_entries=[];unchanged_entries=[]
    for a,b in zip(orig_payloads,post_payloads):
        idx=int(a.name.split('__',1)[0])
        (changed_entries if sha(a)!=sha(b) else unchanged_entries).append(idx)
    title_archive_check={"original_title_and_sys_title_identical":original_title_hash==original_sys_title_hash,
        "original_sha256":original_title_hash,"patched_sha256":sha(title_payload),"physical_size_equal":title_payload.stat().st_size==(DISC/'Title'/'title.vol').stat().st_size,
        "entry_count_equal":len(original_manifest['entries'])==len(post_manifest['entries'])==11,"changed_entries":changed_entries,"unchanged_entries":unchanged_entries,
        "expected_changed_entries":[0,1,2,3,4,5],"pass":original_title_hash==original_sys_title_hash and title_payload.stat().st_size==(DISC/'Title'/'title.vol').stat().st_size and changed_entries==[0,1,2,3,4,5] and len(original_manifest['entries'])==len(post_manifest['entries'])==11}

    failures=[c for c in checks if not c['pass']]
    validation={"schema":"arf-image-ui-structural-validation-v1","asset_checks":len(checks),"passed":len(checks)-len(failures),"failed":len(failures),
        "title_archive_check":title_archive_check,"contact_sheet_100pct":{"pages":["reports/contact_reencoded_100pct/contact_001.png","reports/contact_reencoded_100pct/contact_002.png"],"visual_verdict":"PASS","review_scope":"48 re-encoded renders; Korean legibility, clipping, alpha, retained state frames and Japanese residue on edited regions"},
        "runtime_tested":False,"failures":failures,"checks":checks}
    (BASE/'reports'/'structural_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    manifest={"schema":"arf-image-ui-reinsertion-manifest-v1","baseline":"work/disc_extracted/DATA/files (immutable extracted RVZ derivative)","original_rvz_modified":False,
        "modified_asset_count":len(checks),"replacement_target_count":len(targets),"targets":targets,
        "payload_tree_sha256":{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in sorted((BASE/'payloads').rglob('*')) if p.is_file() and 'title_vol_build' not in str(p)},
        "translation_map":"work/image_ui_final/korean_string_map.json","validation":"work/image_ui_final/reports/structural_validation.json",
        "integration_notes":["Apply Sys/system.vol::nowloading.wtm as a leaf into the cumulative system.vol build; do not overwrite another lane's cumulative system.vol.","Title/title.vol and Sys/title.vol share the same Japanese baseline and use the same patched archive bytes.","CXD sizes may change because deterministic LZ10 recompression is used; rebuild the disc filesystem rather than in-place sector overwrite."]}
    (BASE/'reinsertion_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    exclusions=json.loads((BASE/'reports'/'image_exclusions.json').read_text(encoding='utf-8'))
    report=f"""# Arc Rise Fantasia 이미지 UI 한국어화 최종 보고서

## 결과

- 실제 수정 이미지: **{len(checks)}개**
- 재삽입 대상: **{len(targets)}개** (동일 타이틀 아카이브의 두 배치 경로 포함)
- 구조 검사: **{len(checks)-len(failures)}/{len(checks)} PASS**
- 타이틀 RTDP 변경 엔트리: `{changed_entries}` / 예상 `[0, 1, 2, 3, 4, 5]`
- 100% 재렌더 시각 확인: **PASS**
- 원본 RVZ 수정: **없음**
- 외부 번역/API/생성 모델 사용: **없음**

## 처리 범위

- `Sys/strapA_jp.wtm`, `Sys/strapB_jp.wtm`: 일본어 안전 문구 전체를 한국어로 교체.
- `Title/title.vol`, `Sys/title.vol`: PRESS ANY BUTTON, New Game 2상태, Continue 2상태, 로고 하단 일본어 부제를 한국어로 교체.
- `Sys/system.vol::0053:nowloading.wtm`: 두 상태의 Now Loading을 `불러오는 중…`으로 교체.
- `interface/tex_loc_title_*_wtm.cxd` 37개: 일본어 장소명을 프로젝트 고정 표기의 한국어로 교체하고 기존 영어 부제는 장식 요소로 유지.
- 카지노 소개 2개: 블랙잭/포커의 안내문, 조작 라벨, 상태 라벨 및 포커 족보를 한국어로 교체.

## 보존 사항

- 모든 WTMD의 캔버스, GX 형식, 팔레트 형식, 헤더와 팔레트 바이트를 유지했다.
- 팔레트 텍스처는 기존 팔레트 안에서만 재양자화했고 RGBA32 텍스처는 원래 타일 배열로 재인코드했다.
- 타이틀 VOL은 원본 크기·11개 엔트리·순서·정렬을 유지하며 엔트리 0~5만 변경했다.
- 장소명/카지노 CXD는 동일 크기의 WTMD leaf를 deterministic LZ10으로 다시 감쌌다.

## 제외 자산

{chr(10).join(f'- `{k}`: {v}' for k,v in exclusions.items())}

## 산출물

- 원본 디코드: `work/image_ui_final/original/`
- 조판 PNG: `work/image_ui_final/edited/`
- 재인코드 payload: `work/image_ui_final/payloads/`
- 한국어 문자열 맵: `work/image_ui_final/korean_string_map.json`
- 재삽입 매니페스트: `work/image_ui_final/reinsertion_manifest.json`
- 구조 검사: `work/image_ui_final/reports/structural_validation.json`
- 100% 재렌더: `work/image_ui_final/reports/reencoded_render/`
- 콘택트시트: `work/image_ui_final/reports/contact_reencoded_100pct/`

## 남은 통합 단계

- `nowloading.wtm`은 다른 lane의 누적 `system.vol`에 엔트리 53으로 병합해야 한다.
- CXD는 압축 크기가 달라질 수 있으므로 최종 디스크 파일시스템 재구성 단계에서 교체한다.
- 실제 게임 런타임 확인은 이 lane에서 실행하지 않았다. 최종 통합 빌드에서 부팅 경고, 타이틀 상태 전환, 장소 입장, 카지노 안내, 로딩 화면을 확인해야 한다.
"""
    (BASE/'reports'/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
    print(json.dumps({"modified_assets":len(checks),"targets":len(targets),"passed":len(checks)-len(failures),"failed":len(failures),"title_archive_pass":title_archive_check['pass']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
