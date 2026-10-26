from pathlib import Path
import re
import hashlib
import json
import sys

workspace = Path(__file__).resolve().parent.parent.parent
tex = (workspace / "bab/13-implementasi-gui.tex").read_text(encoding="utf-8")
kode = re.search(r"\\begin\{kode\}\[gui.py\]\n(.*?)\\end\{kode\}", tex, re.S).group(1)
compile(kode, "gui.py", "exec")
assert kode.rstrip() == (Path(__file__).parent / "bab13-code/gui.py").read_text(encoding="utf-8").rstrip()
print("Kode gui.py yang diuji sama persis dengan listing pada Bab 13.")
for nama in ["13-implementasi-gui.tex", "14-penutup.tex"]:
    isi = (workspace / "bab" / nama).read_text(encoding="utf-8")
    assert "% TODO" not in isi and "%<file:" not in isi
    assert isi.count(r"\begingroup") == isi.count(r"\endgroup")
    print(nama, "terisi;", len(isi.splitlines()), "baris")

sebelum = json.loads((Path(sys.executable).parent.parent / "workspace-before.json").read_text(encoding="utf-8-sig"))
berubah = [nama for nama, nilai in sebelum.items()
           if hashlib.sha256((workspace / nama).read_bytes()).hexdigest() != nilai]
assert set(berubah) == {"bab\\11-analisis-perancangan.tex", "bab\\12-implementasi-aplikasi.tex",
                        "bab\\13-implementasi-gui.tex", "bab\\14-penutup.tex", "pustaka.bib"}, berubah
print("Berkas sumber di luar cakupan revisi Bab 11--14 tetap sama.")
