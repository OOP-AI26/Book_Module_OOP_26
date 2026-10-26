import copy
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from perpustakaan import Anggota, BukuCetak, EBook, Perpustakaan, PenyimpananJSON
from perpustakaan.kesalahan import (
    BukuSedangDipinjamError, DataTidakValidError, DataTidakDitemukanError,
    DataRusakError, PeminjamanSelesaiError, PenyimpananError,
)


class UjiPerpustakaan(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "data.json"
        self.penyimpanan = PenyimpananJSON(self.path)
        self.perpus = Perpustakaan(self.penyimpanan)
        self.perpus.muat()
        self.buku = BukuCetak("B001", "Dasar OOP")
        self.perpus.tambah_buku(self.buku)
        self.perpus.tambah_buku(EBook("E001", "Dasar Python"))
        self.perpus.tambah_anggota(Anggota("M001", "Ani"))
        self.perpus.tambah_anggota(Anggota("M002", "Budi"))
        self.tanggal = date(2026, 10, 27)

    def tearDown(self):
        self.folder.cleanup()

    def test_identitas_dan_validasi(self):
        with self.assertRaises(AttributeError):
            self.buku.kode = "B999"
        with self.assertRaises(DataTidakValidError):
            self.buku.judul = "  "
        self.assertEqual(self.buku.judul, "Dasar OOP")
        with self.assertRaises(DataTidakValidError):
            self.perpus.tambah_buku(BukuCetak("B001", "Duplikat"))
        self.assertEqual(len(self.perpus.daftar_buku()), 2)

    def test_polymorphism_dan_object(self):
        a = self.perpus.pinjamkan("M001", "B001", self.tanggal)
        b = self.perpus.pinjamkan("M001", "E001", self.tanggal)
        self.assertEqual(a.tanggal_jatuh_tempo, self.tanggal + timedelta(days=14))
        self.assertEqual(b.tanggal_jatuh_tempo, self.tanggal + timedelta(days=7))
        self.assertIs(a.buku, self.buku)
        self.assertFalse(self.perpus.tersedia("B001"))

    def test_pinjam_gagal_tidak_mengubah_riwayat_atau_nomor(self):
        a = self.perpus.pinjamkan("M001", "B001", self.tanggal)
        with self.assertRaises(BukuSedangDipinjamError):
            self.perpus.pinjamkan("M002", "B001", self.tanggal)
        self.assertEqual(len(self.perpus.daftar_peminjaman()), 1)
        self.perpus.kembalikan(a.id_pinjam, self.tanggal)
        b = self.perpus.pinjamkan("M002", "B001", self.tanggal)
        self.assertEqual(b.id_pinjam, "P002")
        self.assertEqual(len(self.perpus.daftar_peminjaman()), 2)

    def test_pengembalian_dan_riwayat(self):
        a = self.perpus.pinjamkan("M001", "B001", self.tanggal)
        with self.assertRaises(DataTidakValidError):
            self.perpus.kembalikan(a.id_pinjam, self.tanggal - timedelta(days=1))
        self.assertTrue(a.aktif)
        self.perpus.kembalikan(a.id_pinjam, self.tanggal)
        self.assertTrue(self.perpus.tersedia("B001"))
        self.assertEqual(len(self.perpus.daftar_peminjaman()), 1)
        with self.assertRaises(PeminjamanSelesaiError):
            self.perpus.kembalikan(a.id_pinjam, self.tanggal)

    def test_data_tidak_terdaftar_dan_tanggal_salah(self):
        for anggota, buku in [("X", "B001"), ("M001", "X")]:
            with self.assertRaises(DataTidakDitemukanError):
                self.perpus.pinjamkan(anggota, buku, self.tanggal)
        with self.assertRaises(DataTidakValidError):
            self.perpus.pinjamkan("M001", "B001", "2026-10-27")
        self.assertEqual(self.perpus.daftar_peminjaman(), [])

    def test_hasil_daftar_adalah_salinan_koleksi(self):
        daftar = self.perpus.daftar_buku()
        daftar.clear()
        self.assertEqual(len(self.perpus.daftar_buku()), 2)

    def test_tanggal_melebihi_jangkauan_tidak_mengubah_data(self):
        with self.assertRaises(DataTidakValidError):
            self.perpus.pinjamkan("M001", "B001", date.max)
        self.assertEqual(self.perpus.daftar_peminjaman(), [])
        sah = self.perpus.pinjamkan("M001", "B001", self.tanggal)
        self.assertEqual(sah.id_pinjam, "P001")

    def test_simpan_muat_mempertahankan_relasi_dan_nomor(self):
        a = self.perpus.pinjamkan("M001", "B001", self.tanggal)
        self.perpus.kembalikan(a.id_pinjam, self.tanggal)
        self.perpus.simpan()
        baru = Perpustakaan(self.penyimpanan)
        baru.muat()
        p = baru.daftar_peminjaman()[0]
        self.assertIs(p.buku, baru.daftar_buku()[0])
        self.assertIs(p.anggota, baru.daftar_anggota()[0])
        self.assertFalse(p.aktif)
        self.assertEqual(baru.pinjamkan("M002", "B001", self.tanggal).id_pinjam, "P002")

    def test_jatuh_tempo_historis_tidak_dihitung_ulang(self):
        a = self.perpus.pinjamkan("M001", "B001", self.tanggal)
        self.perpus.simpan()
        with patch.object(BukuCetak, "lama_pinjam", return_value=2):
            baru = Perpustakaan(self.penyimpanan)
            baru.muat()
            self.assertEqual(baru.daftar_peminjaman()[0].tanggal_jatuh_tempo,
                             a.tanggal_jatuh_tempo)

    def test_json_terpotong_tidak_menghapus_memory(self):
        self.path.write_text('{"buku":', encoding="utf-8")
        with self.assertRaises(DataRusakError):
            self.perpus.muat()
        self.assertEqual(len(self.perpus.daftar_buku()), 2)

    def test_data_tidak_sah_ditolak_secara_utuh(self):
        self.perpus.pinjamkan("M001", "B001", self.tanggal)
        self.perpus.simpan()
        asli = json.loads(self.path.read_text(encoding="utf-8"))
        variasi = []
        d = copy.deepcopy(asli); d["peminjaman"][0]["id_anggota"] = "X"; variasi.append(d)
        d = copy.deepcopy(asli); d["buku"].append(d["buku"][0]); variasi.append(d)
        d = copy.deepcopy(asli); p = dict(d["peminjaman"][0]); p["id_pinjam"] = "P002"
        d["peminjaman"].append(p); d["nomor_pinjam_berikutnya"] = 3; variasi.append(d)
        d = copy.deepcopy(asli); d["nomor_pinjam_berikutnya"] = 1; variasi.append(d)
        d = copy.deepcopy(asli); d["versi"] = True; variasi.append(d)
        d = copy.deepcopy(asli); d["peminjaman"][0]["tanggal_kembali"] = "2026-10-01"; variasi.append(d)
        variasi.extend([{}, [], None])
        for d in variasi:
            with self.subTest(data=d):
                self.path.write_text(json.dumps(d), encoding="utf-8")
                with self.assertRaises(DataRusakError):
                    self.perpus.muat()
                self.assertEqual(len(self.perpus.daftar_buku()), 2)
                self.assertEqual(len(self.perpus.daftar_peminjaman()), 1)

    def test_gagal_menulis_tidak_menimpa_file_lama(self):
        self.perpus.simpan()
        sebelum = self.path.read_bytes()
        with patch("perpustakaan.penyimpanan.json.dump", side_effect=OSError("disk")):
            with self.assertRaises(PenyimpananError):
                self.perpus.simpan()
        self.assertEqual(self.path.read_bytes(), sebelum)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
