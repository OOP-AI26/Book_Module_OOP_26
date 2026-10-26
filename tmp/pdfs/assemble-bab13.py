from pathlib import Path
import re

folder = Path(__file__).resolve().parent
template = (folder / "bab13-template.tex").read_text(encoding="utf-8")
hasil = re.sub(r"%<file:([^>]+)>",
               lambda m: (folder / "bab13-code" / m.group(1)).read_text(encoding="utf-8").rstrip(),
               template)
tujuan = folder.parent.parent / "bab/13-implementasi-gui.tex"
tujuan.write_text(hasil, encoding="utf-8", newline="\n")
print(f"Ditulis: {tujuan.name}, {len(hasil.splitlines())} baris")
