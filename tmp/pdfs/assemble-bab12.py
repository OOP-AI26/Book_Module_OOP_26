from pathlib import Path
import re

folder = Path(__file__).resolve().parent
template = (folder / "bab12-template.tex").read_text(encoding="utf-8")

def masukkan(match):
    nama = match.group(1)
    return (folder / "bab12-code" / nama).read_text(encoding="utf-8").rstrip()

hasil = re.sub(r"%<file:([^>]+)>", masukkan, template)
tujuan = folder.parent.parent / "bab" / "12-implementasi-aplikasi.tex"
tujuan.write_text(hasil, encoding="utf-8", newline="\n")
print(f"Ditulis: {tujuan.name} ({len(hasil.splitlines())} baris)")
