from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from perpustakaan import Anggota, BukuCetak, EBook, Perpustakaan, PenyimpananJSON
from perpustakaan.kesalahan import BukuSedangDipinjamError


with TemporaryDirectory() as folder:
    simpanan = PenyimpananJSON(Path(folder) / "perpustakaan.json")
    perpus = Perpustakaan(simpanan)
    perpus.muat()
    perpus.tambah_buku(BukuCetak("B001", "Dasar OOP"))
    perpus.tambah_buku(EBook("E001", "Dasar Python"))
    perpus.tambah_anggota(Anggota("M001", "Ani"))

    pinjam = perpus.pinjamkan("M001", "B001", date(2026, 10, 27))
    print("Pinjam:", pinjam.id_pinjam, "jatuh tempo", pinjam.tanggal_jatuh_tempo)
    print("B001 tersedia:", perpus.tersedia("B001"))
    try:
        perpus.pinjamkan("M001", "B001", date(2026, 10, 28))
    except BukuSedangDipinjamError as exc:
        print("Ditolak:", exc)
    print("Jumlah riwayat:", len(perpus.daftar_peminjaman()))

    perpus.kembalikan("P001", date(2026, 11, 2))
    print("Sesudah kembali:", perpus.tersedia("B001"))
    digital = perpus.pinjamkan("M001", "E001", date(2026, 10, 27))
    print("E-book jatuh tempo:", digital.tanggal_jatuh_tempo)
    perpus.simpan()

    dimuat = Perpustakaan(simpanan)
    dimuat.muat()
    print("Dimuat:", len(dimuat.daftar_buku()), "buku,",
          len(dimuat.daftar_peminjaman()), "riwayat")
    print("Status:", [(p.id_pinjam, p.aktif) for p in dimuat.daftar_peminjaman()])
