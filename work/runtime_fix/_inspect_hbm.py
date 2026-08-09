from pathlib import Path
import hashlib
root=Path(r'work/disc_extracted/DATA/files/Hbm')
for name in ['home.csv','home_nosave.csv']:
 p=root/name;b=p.read_bytes()
 print(name,len(b),hashlib.sha256(b).hexdigest().upper(),b[:16].hex())
 print(b.decode('utf-16be')[:1500].replace('\r','\\r').replace('\n','\\n\n'))
 print('---')
