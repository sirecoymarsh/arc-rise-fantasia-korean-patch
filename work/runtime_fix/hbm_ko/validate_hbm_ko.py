from pathlib import Path
import hashlib, json, csv, io, xml.etree.ElementTree as ET
root=Path('.')
manifest=json.loads((root/'work/runtime_fix/hbm_ko/hbm_korean_payload_manifest.json').read_text(encoding='utf-8'))
assert manifest['static_validation']['valid']
for x in manifest['csv_files']:
 b=(root/x['output_path']).read_bytes(); assert b[:2]==b'\xfe\xff'; text=b[2:].decode('utf-16-be'); rows=list(csv.reader(io.StringIO(text,newline=''),delimiter='\t',quotechar='"')); assert len(rows)==4 and all(len(r)==7 for r in rows)
 assert hashlib.sha256(b).hexdigest().upper()==x['output_sha256']
a=manifest['home_button_archive']; b=(root/a['output_path']).read_bytes(); assert hashlib.sha256(b).hexdigest().upper()==a['output_sha256']; assert len(b)==a['output_size']==a['source_size']; assert b[:4]==b'\x55\xaa8-'
frag=(root/'work/runtime_fix/hbm_ko/riivolution_hbm_rules.xml.fragment').read_text(encoding='utf-8'); ET.fromstring('<patch>'+frag+'</patch>')
# Confirm immutable source hashes remain the audited baselines.
for p,h in [('work/disc_extracted/DATA/files/Hbm/home.csv','8A0BC17E6DD252A623B9BA5D89AB32E56C795D6F49FEA29E2DA65F2FD6B0AF9C'),('work/disc_extracted/DATA/files/Hbm/home_nosave.csv','560EE7A36E8EDFD75CC9397C75397C74D34FF02FEE8197D3D2697AC0E74D585B'),('work/disc_extracted/DATA/files/Hbm/homeBtn.arc','B0AF517B04C369A278B42C0147878E6C2ACB7EA6ACA4986D6243F93D760980BE')]: assert hashlib.sha256((root/p).read_bytes()).hexdigest().upper()==h
print(json.dumps({'valid':True,'payloads':3,'csv_rows_each':4,'u8_size':len(b),'xml_fragment_valid':True,'source_baselines_unchanged':True,'visual_evidence_count':len(manifest['visual_evidence'])},ensure_ascii=False,indent=2))
