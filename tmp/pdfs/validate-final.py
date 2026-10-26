from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import re
import shutil
import subprocess
import sys

folder = Path(__file__).resolve().parent
workspace = folder.parent.parent
tex = (workspace / "bab/12-implementasi-aplikasi.tex").read_text(encoding="utf-8")

with TemporaryDirectory() as nama_folder:
    proyek = Path(nama_folder)
    listing = re.findall(r"\\begin\{kode\}\[([^\]]+)\]\n(.*?)\\end\{kode\}", tex, re.S)
    for judul, isi in listing:
        nama = judul.replace(r"\_", "_")
        if not nama.endswith(".py"):
            raise AssertionError(f"Judul listing tidak dipetakan: {nama}")
        tujuan = proyek / nama
        tujuan.parent.mkdir(parents=True, exist_ok=True)
        tujuan.write_text(isi, encoding="utf-8")
        compile(isi, nama, "exec")
        assert isi.rstrip() == (folder / "bab12-code" / nama).read_text(encoding="utf-8").rstrip()
    print(f"{len(listing)} listing Python diambil langsung dari TeX; seluruhnya valid.")

    def jalankan(file, masukan=None):
        perintah = [sys.executable, "-c",
                    "import sys,runpy; sys.path.insert(0,sys.argv[1]); "
                    "runpy.run_path(sys.argv[2],run_name='__main__')",
                    str(proyek), str(proyek / file)]
        return subprocess.run(perintah, input=masukan, text=True,
                              capture_output=True, cwd=proyek)

    for nama in ["demo_encapsulation.py", "demo_relasi.py",
                 "demo_polymorphism.py", "demo_integrasi.py", "cek_kontrak.py"]:
        hasil = jalankan(nama)
        assert hasil.returncode == 0, hasil.stderr
        assert hasil.stdout.strip() in tex, (nama, hasil.stdout)
    print("5 keluaran pemeriksaan sama persis dengan yang dituliskan di TeX.")

    alur = "\n".join(["2", "B001", "Dasar OOP", "cetak", "3", "M001", "Ani",
                       "4", "M001", "B001", "2026-10-27", "1", "0", ""])
    hasil = jalankan("main.py", alur)
    assert hasil.returncode == 0, hasil.stderr
    for teks in ["Buku terdaftar.", "Anggota terdaftar.",
                 "Berhasil: P001 jatuh tempo 2026-11-10",
                 "[B001] Dasar OOP - dipinjam", "Data tersimpan."]:
        assert teks in hasil.stdout, hasil.stdout
    simpanan = proyek / "data/perpustakaan.json"
    data = json.loads(simpanan.read_text(encoding="utf-8"))
    assert data["nomor_pinjam_berikutnya"] == 2

    hasil = jalankan("main.py", "1\n6\n5\nP001\n2026-11-02\n0\n")
    assert hasil.returncode == 0, hasil.stderr
    assert "[B001] Dasar OOP - dipinjam" in hasil.stdout
    assert "P001 Ani B001 aktif" in hasil.stdout
    assert "Pengembalian tercatat." in hasil.stdout
    assert json.loads(simpanan.read_text(encoding="utf-8"))["peminjaman"][0]["tanggal_kembali"] == "2026-11-02"

    hasil = jalankan("main.py", "4\nM001\nB001\ntidak-valid\n0\n")
    assert hasil.returncode == 0 and "Ditolak:" in hasil.stdout

    simpanan.write_text("{rusak", encoding="utf-8")
    hasil = jalankan("main.py", "0\n")
    assert hasil.returncode == 1 and "Data tidak dimuat:" in hasil.stdout
    assert simpanan.read_text(encoding="utf-8") == "{rusak"
    print("Menu: daftar, pinjam, muat ulang, kembali, input salah, dan file rusak sesuai kontrak.")

    shutil.copyfile(folder / "bab12-code/test_integrasi.py", proyek / "test_integrasi.py")
    perintah = [sys.executable, "-c", "import sys,unittest; sys.path.insert(0,sys.argv[1]); "
                "suite=unittest.defaultTestLoader.discover(sys.argv[1],pattern='test_integrasi.py'); "
                "result=unittest.TextTestRunner(verbosity=1).run(suite); "
                "sys.exit(not result.wasSuccessful())", str(proyek)]
    hasil = subprocess.run(perintah, text=True, capture_output=True)
    assert hasil.returncode == 0, hasil.stderr
    print(hasil.stderr.strip())

for nama in ["11-analisis-perancangan.tex", "12-implementasi-aplikasi.tex"]:
    isi = (workspace / "bab" / nama).read_text(encoding="utf-8")
    assert "% TODO" not in isi and "%<file:" not in isi
    assert isi.count(r"\begingroup") == isi.count(r"\endgroup")
    cites = re.findall(r"\\cite\{([^}]+)\}", isi)
    bib = (workspace / "pustaka.bib").read_text(encoding="utf-8")
    for keys in cites:
        for key in keys.split(","):
            assert re.search(r"@\w+\{" + re.escape(key) + ",", bib)

sebelum = json.loads((Path(sys.executable).parent.parent / "workspace-before.json").read_text(encoding="utf-8-sig"))
berubah = []
for nama, hash_lama in sebelum.items():
    file = workspace / nama
    if hashlib.sha256(file.read_bytes()).hexdigest() != hash_lama:
        berubah.append(nama)
assert set(berubah) == {"bab\\11-analisis-perancangan.tex", "bab\\12-implementasi-aplikasi.tex", "pustaka.bib"}, berubah
print("Sumber yang berubah:", ", ".join(berubah))
