from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

xml_path = Path("work/final_runtime_staging/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml")
backup_path = Path("work/runtime_validation/arc_rise_fantasia_ko_full.before_main_dol.xml")
if not backup_path.exists():
    shutil.copy2(xml_path, backup_path)

text = xml_path.read_text(encoding="utf-8")
needle = '  <patch id="arf-ko-full" root="/arc_rise_fantasia_ko_full/files">'
insert = needle + '\n    <file disc="/sys/main.dol" external="sys/main.dol" resize="false" />'
if 'disc="/sys/main.dol"' not in text:
    if needle not in text:
        raise ValueError("patch node not found")
    text = text.replace(needle, insert, 1)
    xml_path.write_text(text, encoding="utf-8", newline="\n")
ET.parse(xml_path)
print(next(line for line in text.splitlines() if "main.dol" in line))
