from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
backup = ROOT / "work/runtime_validation/arc_rise_fantasia_ko_full.before_main_dol.xml"
xml_path = ROOT / "work/final_runtime_staging/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
text = backup.read_text(encoding="utf-8")
needle = '  <patch id="arf-ko-full" root="/arc_rise_fantasia_ko_full/files">'
line = '    <memory offset="0x803D4FFA" value="BFDDB7A800000000" />'
text = text.replace(needle, needle + "\n" + line, 1)
xml_path.write_text(text, encoding="utf-8", newline="\n")
ET.parse(xml_path)
print(line)
