from pathlib import Path
import struct

p = Path("work/disc_extracted/DATA/sys/main.dol")
d = p.read_bytes()
be32 = lambda off: struct.unpack_from(">I", d, off)[0]

sections = []
for i in range(7):
    sections.append((f"text{i}", be32(0x00 + 4*i), be32(0x48 + 4*i), be32(0x90 + 4*i)))
for i in range(11):
    sections.append((f"data{i}", be32(0x1c + 4*i), be32(0x64 + 4*i), be32(0xac + 4*i)))

for name, foff, addr, size in sections:
    print(f"{name:6} file=0x{foff:08X}-0x{foff+size:08X} mem=0x{addr:08X}-0x{addr+size:08X} size=0x{size:X}")

for foff in (0x3C64F7, 0x3D10FA, 0x3F1DD9):
    matches = [(n, a + foff - o) for n,o,a,s in sections if s and o <= foff < o+s]
    print(f"offset 0x{foff:X} ->", [(n, f"0x{a:08X}") for n,a in matches])
