#!/usr/bin/env python3
"""Translate the remaining fld000.bin default-name placeholder."""
from __future__ import annotations
import hashlib, json, os, struct
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]; W=ROOT/'work'
STAGED=W/'final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/Btl/btl_usual.vol'
REFERENCE=W/'ray_stone_field_application/btl_usual.vol'
MANIFEST=W/'final_runtime_staging/staging_manifest.json'
CODEBOOK=W/'font/final_v3/codebook.json'
APP=W/'battle_field_residue_application'; OUTPUT=APP/'btl_usual.vol'; REPORT=APP/'application_report.json'
SOURCE_CONTAINER_SHA256='DF2574E528543BC1D7B13CDEF26705CA655F6D24834AAE400A0A6FA22678D3D2'
ENTRY_INDEX=25; ENTRY_NAME='fld000.bin'; ENTRY_SIZE=392704
SOURCE_MEMBER_SHA256='E7BA14CF2357EEFFBB3FEE23C67BF4C1086438876FED594AF44DFFBFAA621ACE'
FIELD_OFFSET=0x8BC; FIELD_CAPACITY=35
PRECEDING_OFFSET=0x8B8; PRECEDING_EXPECTED=bytes.fromhex('0000003C')
FOLLOWING_OFFSET=FIELD_OFFSET+FIELD_CAPACITY; FOLLOWING_EXPECTED=0x86
SOURCE_TEXT='名称未設定'; TARGET_TEXT='이름 미설정'
SOURCE_HEX='CCBEBECECCA4C0DFC4EA'; TARGET_HEX='B0ABB7C220B9A6BBF0B0AC'

def need(ok:bool,msg:str)->None:
 if not ok: raise RuntimeError(msg)
def h(data:bytes)->str:return hashlib.sha256(data).hexdigest().upper()
def readj(p:Path)->dict[str,Any]:
 o=json.loads(p.read_text(encoding='utf-8-sig'));need(isinstance(o,dict),f'bad JSON: {p}');return o
def writej(p:Path,o:Any)->None:
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+'.partial');q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(q,p)
def parse(data:bytes):
 need(data[:4]==b'RTDP','not RTDP');e,c=struct.unpack_from('>II',data,4);need(0x20+c*40<=e<=len(data),'bad header');rows=[]
 for i in range(c):
  p=0x20+i*40;n=data[p:p+32].split(b'\0',1)[0].decode('ascii');s,r=struct.unpack_from('>II',data,p+32);start=e+r;end=start+s;need(end<=len(data),'member out of range');rows.append({'index':i,'name':n,'size':s,'relative':r,'start':start,'end':end})
 return rows
def dec(data:bytes,row):return bytes(x^0x55 for x in data[row['start']:row['end']])
def encode()->bytes:
 cb=readj(CODEBOOK)['characters'];parts=[]
 for c in TARGET_TEXT:
  if c in cb:parts.append(bytes.fromhex(cb[c]['bytes_hex']))
  else:need(ord(c)<128,f'missing codebook char {c!r}');parts.append(c.encode('ascii'))
 out=b''.join(parts);need(out.hex().upper()==TARGET_HEX,'target encoding changed');return out

def main()->int:
 for p in (STAGED,REFERENCE,MANIFEST,CODEBOOK):need(p.is_file(),f'missing {p}')
 source=REFERENCE.read_bytes();need(h(source)==SOURCE_CONTAINER_SHA256,'v1.1.1 source container changed')
 rows=parse(source);need(len(rows)==26,'member count changed');row=rows[ENTRY_INDEX];need(row['name']==ENTRY_NAME and row['size']==ENTRY_SIZE,'member identity changed')
 before=dec(source,row);need(h(before)==SOURCE_MEMBER_SHA256,'v1.1.1 fld member changed')
 raw=before[FIELD_OFFSET:FIELD_OFFSET+FIELD_CAPACITY].split(b'\0',1)[0];need(raw.hex().upper()==SOURCE_HEX and raw.decode('euc_jp')==SOURCE_TEXT,'source placeholder changed')
 need(before[PRECEDING_OFFSET:PRECEDING_OFFSET+4]==PRECEDING_EXPECTED,'preceding structure changed');need(before[FOLLOWING_OFFSET]==FOLLOWING_EXPECTED,'following structure changed')
 target=encode();need(len(target)<FIELD_CAPACITY,'target does not fit')
 after=bytearray(before);after[FIELD_OFFSET:FIELD_OFFSET+FIELD_CAPACITY]=bytes(FIELD_CAPACITY);after[FIELD_OFFSET:FIELD_OFFSET+len(target)]=target
 need(after[PRECEDING_OFFSET:PRECEDING_OFFSET+4]==PRECEDING_EXPECTED and after[FOLLOWING_OFFSET]==FOLLOWING_EXPECTED,'adjacent structure changed')
 changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b];need(all(FIELD_OFFSET<=i<FIELD_OFFSET+FIELD_CAPACITY for i in changed),'change outside field')
 output=bytearray(source);output[row['start']:row['end']]=bytes(x^0x55 for x in after);out=bytes(output);need(len(out)==len(source),'container size changed')
 outrows=parse(out);need([(x['name'],x['size'],x['relative']) for x in rows]==[(x['name'],x['size'],x['relative']) for x in outrows],'RTDP layout changed')
 for a,b in zip(rows,outrows):
  if a['index']!=ENTRY_INDEX:need(dec(source,a)==dec(out,b),f'unrelated member changed: {a["name"]}')
 verified=dec(out,outrows[ENTRY_INDEX]);need(verified[FIELD_OFFSET:FIELD_OFFSET+len(target)]==target,'target reread failed');need(verified[FIELD_OFFSET+len(target):FIELD_OFFSET+FIELD_CAPACITY]==bytes(FIELD_CAPACITY-len(target)),'padding changed')
 current=STAGED.read_bytes();already=current==out;need(current==source or already,f'staged source unexpected: {h(current)}')
 APP.mkdir(parents=True,exist_ok=True);OUTPUT.write_bytes(out);tmp=STAGED.with_suffix(STAGED.suffix+'.partial');tmp.write_bytes(out);os.replace(tmp,STAGED);need(STAGED.read_bytes()==out,'staging reread failed')
 m=readj(MANIFEST);rowsm=m['static_validation']['staged_files'];matches=[x for x in rowsm if x['physical_path']=='Btl/btl_usual.vol'];need(len(matches)==1,'manifest row missing');matches[0]['output_sha256']=h(out);matches[0]['output_size']=len(out)
 m['counts']['battle_field_object_name_residue_translations']=1;m['counts']['battle_field_object_placeholder_residue_translations']=1;m['counts']['battle_field_object_text_residue_translations']=2
 m['battle_field_text_residue_patch']={'schema':'arf-battle-field-text-residue-patch-v1','report':'work/battle_field_residue_application/application_report.json','physical_path':'Btl/btl_usual.vol','member':ENTRY_NAME,'field_offset_hex':f'0x{FIELD_OFFSET:X}','source_text':SOURCE_TEXT,'translation_ko':TARGET_TEXT,'output_sha256':h(out),'translator_model':'Codex internal'}
 writej(MANIFEST,m)
 report={'schema':'arf-battle-field-placeholder-application-v1','game_id':'RPJJ99','valid':True,'already_applied':already,'physical_path':'Btl/btl_usual.vol','source_container_sha256':h(source),'output_container_sha256':h(out),'container_size':len(out),'member_index':ENTRY_INDEX,'member_name':ENTRY_NAME,'member_size':ENTRY_SIZE,'source_member_sha256':h(before),'output_member_sha256':h(verified),'field_offset_hex':f'0x{FIELD_OFFSET:X}','field_capacity':FIELD_CAPACITY,'source_text':SOURCE_TEXT,'translation_ko':TARGET_TEXT,'source_hex':SOURCE_HEX,'target_hex':TARGET_HEX,'changed_member_bytes':len(changed),'changed_outside_allowlist':0,'rtdp_layout_preserved':True,'unrelated_members_unchanged':True,'adjacent_structure_preserved':True,'translator_model':'Codex internal','external_translation_models_or_apis_used':False,'staging_manifest_sha256':h(MANIFEST.read_bytes())}
 writej(REPORT,report);print(json.dumps(report,ensure_ascii=True,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
