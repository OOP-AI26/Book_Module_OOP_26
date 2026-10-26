from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from perpustakaan import Anggota, BukuCetak, Perpustakaan, PenyimpananJSON
from perpustakaan.kesalahan import DataTidakValidError


with TemporaryDirectory() as folder:
    simpanan = PenyimpananJSON(Path(folder) / "data.json")
    perpus = Perpustakaan(simpanan)
    perpus.tambah_buku(BukuCetak("B001", "Dasar OOP"))
    perpus.tambah_anggota(Anggota("M001", "Ani"))
    pinjam = perpus.pinjamkan("M001", "B001", date(2026, 10, 27))

    try:
        perpus.kembalikan("P001", date(2026, 10, 26))
    except DataTidakValidError:
        pass
    else:
        raise AssertionError("Tanggal kembali seharusnya ditolak.")
    assert pinjam.aktif and pinjam.tanggal_kembali is None
    assert len(perpus.daftar_peminjaman()) == 1

    perpus.simpan()
    dimuat = Perpustakaan(simpanan)
    dimuat.muat()
    riwayat = dimuat.daftar_peminjaman()
    assert riwayat[0].buku is dimuat.daftar_buku()[0]
    assert riwayat[0].anggota is dimuat.daftar_anggota()[0]
    assert not dimuat.tersedia("B001")

    dimuat.kembalikan("P001", date(2026, 11, 2))
    berikut = dimuat.pinjamkan("M001", "B001", date(2026, 11, 3))
    assert berikut.id_pinjam == "P002"

print("Kontrak pengembalian, relasi, dan nomor transaksi terpenuhi.")
