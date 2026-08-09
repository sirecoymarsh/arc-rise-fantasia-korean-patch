import json
import re
import struct
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DOL = ROOT / "work/disc_extracted/DATA/sys/main.dol"
REPORT = ROOT / "work/runtime_validation/initial_dol_test_report.json"
XML = ROOT / "work/final_runtime_staging/riivolution_sd/riivolution/arc_rise_fantasia_ko_full.xml"
STAGED_DOL = ROOT / "work/final_runtime_staging/riivolution_sd/arc_rise_fantasia_ko_full/files/sys/main.dol"


def sections(data: bytes):
    u32 = lambda o: struct.unpack_from(">I", data, o)[0]
    out = []
    for i in range(7):
        out.append((u32(4*i), u32(0x48+4*i), u32(0x90+4*i)))
    for i in range(11):
        out.append((u32(0x1c+4*i), u32(0x64+4*i), u32(0xac+4*i)))
    return out


def file_to_memory(offset: int, sec):
    matches = [addr + offset - file_off for file_off, addr, size in sec if size and file_off <= offset < file_off + size]
    if len(matches) != 1:
        raise ValueError(f"DOL offset 0x{offset:X} has {len(matches)} memory mappings")
    return matches[0]


data = DOL.read_bytes()
sec = sections(data)
report = json.loads(REPORT.read_text(encoding="utf-8"))
lines = []
for row in report["patches"]:
    address = file_to_memory(row["offset"], sec)
    value = row["replacement_hex"] + "00" * (row["capacity"] - row["encoded_length"])
    lines.append(f'    <memory offset="0x{address:08X}" value="{value}" />')

text = XML.read_text(encoding="utf-8")
text = re.sub(r'^\s*<file disc="/sys/main\.dol"[^\n]*\n?', "", text, flags=re.MULTILINE)
text = re.sub(r'^\s*<memory offset="0x803[CD][0-9A-F]{5}"[^\n]*\n?', "", text, flags=re.MULTILINE)
needle = '  <patch id="arf-ko-full" root="/arc_rise_fantasia_ko_full/files">'
if needle not in text:
    raise ValueError("patch node not found")
text = text.replace(needle, needle + "\n" + "\n".join(lines), 1)
XML.write_text(text, encoding="utf-8", newline="\n")
ET.parse(XML)
STAGED_DOL.unlink(missing_ok=True)
print(json.dumps({"memory_patch_count": len(lines), "first": lines[0], "last": lines[-1]}, ensure_ascii=False))
