from pathlib import Path
from datetime import date
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import tkinter as tk
from tkinter import ttk
import unittest

import gui
from perpustakaan import Anggota, BukuCetak, EBook, Perpustakaan, PenyimpananJSON
from perpustakaan.kesalahan import PenyimpananError


class UjiGUI(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.path = Path(self.folder.name) / "perpustakaan.json"
        self.perpus = Perpustakaan(PenyimpananJSON(self.path))
        self.perpus.muat()
        self.root = tk.Tk()
        self.root.withdraw()
        self.error_patch = patch.object(gui.messagebox, "showerror")
        self.pesan = self.error_patch.start()
        self.app = gui.AplikasiPerpustakaan(self.root, self.perpus)
        self.root.update_idletasks()

    def tearDown(self):
        self.error_patch.stop()
        self.root.destroy()
        self.folder.cleanup()

    def tombol(self, teks):
        def cari(widget):
            if isinstance(widget, ttk.Button) and widget.cget("text") == teks:
                return widget
            for anak in widget.winfo_children():
                hasil = cari(anak)
                if hasil:
                    return hasil
        hasil = cari(self.root)
        self.assertIsNotNone(hasil, teks)
        return hasil

    def daftar(self):
        self.app.kode.set("B001")
        self.app.judul.set("Dasar OOP")
        self.tombol("Daftarkan buku").invoke()
        self.app.id_anggota.set("M001")
        self.app.nama.set("Ani")
        self.tombol("Daftarkan anggota").invoke()

    def pinjam(self):
        self.daftar()
        self.app.anggota_dipilih.set("M001")
        self.app.buku_dipilih.set("B001")
        self.app.tanggal.set("2026-10-27")
        self.tombol("Pinjam").invoke()

    def test_widget_awal(self):
        self.assertEqual(len(self.app.tab.tabs()), 3)
        self.assertEqual(self.app.tabel_pinjam.get_children(), ())
        self.assertEqual(str(self.app.pilihan_buku.cget("state")), "readonly")
        self.assertFalse(self.app.berubah)
        self.assertTrue(self.root.bind("<Control-s>"))
        self.assertTrue(self.root.protocol("WM_DELETE_WINDOW"))

    def test_pendaftaran_dan_duplikat(self):
        self.daftar()
        self.assertEqual(self.app.kode.get(), "")
        self.assertEqual(self.app.tabel_anggota.item("M001", "values"), ("M001", "Ani"))
        self.app.simpan()
        self.app.kode.set("B001")
        self.app.judul.set("Duplikat")
        self.tombol("Daftarkan buku").invoke()
        self.pesan.assert_called_once()
        self.assertEqual(self.app.judul.get(), "Duplikat")
        self.assertFalse(self.app.berubah)
        self.assertEqual(self.perpus.daftar_buku()[0].judul, "Dasar OOP")

    def test_pinjam_dan_sinkronisasi_tabel(self):
        self.pinjam()
        self.assertEqual(self.app.tabel_pinjam.item("P001", "values"),
                         ("P001", "M001", "B001", "2026-10-27", "2026-11-10", "-", "aktif"))
        self.assertEqual(self.app.tabel_buku.item("B001", "values")[-1], "dipinjam")
        self.assertEqual(self.app.buku_dipilih.get(), "")
        self.assertNotIn("B001", self.app.pilihan_buku.cget("values"))
        self.assertTrue(self.app.berubah)

    def test_tanggal_salah_tidak_memutasi(self):
        self.daftar()
        self.app.simpan()
        self.app.anggota_dipilih.set("M001")
        self.app.buku_dipilih.set("B001")
        for tanggal in ("2026-02-30", "20261027", "", "2026-1-2"):
            self.app.tanggal.set(tanggal)
            self.app.pinjam()
            self.assertEqual(self.perpus.daftar_peminjaman(), [])
            self.assertFalse(self.app.berubah)
        self.assertEqual(self.pesan.call_count, 4)

    def test_kembali_tanpa_pilihan(self):
        self.app.kembalikan()
        self.pesan.assert_called_once()
        self.assertFalse(self.app.berubah)

    def test_kembali_ditolak_dan_berhasil(self):
        self.pinjam()
        self.app.simpan()
        self.app.tabel_pinjam.selection_set("P001")
        self.app.tanggal.set("2026-10-26")
        self.app.kembalikan()
        self.assertFalse(self.app.berubah)
        self.assertTrue(self.perpus.daftar_peminjaman()[0].aktif)
        self.app.tanggal.set("2026-11-02")
        self.tombol("Kembalikan pilihan").invoke()
        self.assertEqual(self.app.tabel_pinjam.item("P001", "values")[-2:],
                         ("2026-11-02", "selesai"))
        self.assertIn("B001", self.app.pilihan_buku.cget("values"))
        self.app.simpan()
        self.app.kembalikan()
        self.assertFalse(self.app.berubah)
        self.assertEqual(len(self.perpus.daftar_peminjaman()), 1)
        self.assertEqual(self.pesan.call_count, 2)

    def test_pilihan_buku_menggunakan_event(self):
        self.daftar()
        self.app.simpan()
        self.app.tabel_buku.selection_set("B001")
        self.app.tabel_buku.event_generate("<<TreeviewSelect>>")
        self.root.update()
        self.assertEqual(self.app.buku_dipilih.get(), "B001")
        self.assertFalse(self.app.berubah)

    def test_simpan_dan_muat_ulang(self):
        self.pinjam()
        self.tombol("Simpan").invoke()
        self.assertFalse(self.app.berubah)
        baru = Perpustakaan(PenyimpananJSON(self.path))
        baru.muat()
        self.assertEqual(baru.daftar_peminjaman()[0].id_pinjam, "P001")
        self.assertFalse(baru.tersedia("B001"))
        self.assertEqual(self.app.status.get(), "Data tersimpan.")

    def test_gagal_simpan_mempertahankan_penanda(self):
        self.daftar()
        with patch.object(self.perpus, "simpan", side_effect=PenyimpananError("Disk gagal")):
            self.assertFalse(self.app.simpan())
        self.assertTrue(self.app.berubah)
        self.pesan.assert_called_once()

    def test_batal_tutup_tidak_mengubah_keadaan(self):
        self.daftar()
        with patch.object(gui.messagebox, "askyesnocancel", return_value=None), \
                patch.object(self.root, "destroy") as hancurkan:
            self.app.tutup()
            hancurkan.assert_not_called()
        self.assertTrue(self.app.berubah)

    def test_tutup_tanpa_menyimpan(self):
        self.daftar()
        with patch.object(gui.messagebox, "askyesnocancel", return_value=False), \
                patch.object(self.root, "destroy") as hancurkan:
            self.app.tutup()
            hancurkan.assert_called_once()
        self.assertFalse(self.path.exists())

    def test_ya_gagal_simpan_tidak_menutup(self):
        self.daftar()
        with patch.object(gui.messagebox, "askyesnocancel", return_value=True), \
                patch.object(self.perpus, "simpan", side_effect=PenyimpananError("Disk gagal")), \
                patch.object(self.root, "destroy") as hancurkan:
            self.app.tutup()
            hancurkan.assert_not_called()
        self.assertTrue(self.app.berubah)

    def test_ya_berhasil_simpan_dan_tutup(self):
        self.daftar()
        with patch.object(gui.messagebox, "askyesnocancel", return_value=True), \
                patch.object(self.root, "destroy") as hancurkan:
            self.app.tutup()
            hancurkan.assert_called_once()
        self.assertFalse(self.app.berubah)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["buku"][0]["kode"], "B001")

    def test_tutup_bersih_tanpa_dialog(self):
        with patch.object(gui.messagebox, "askyesnocancel") as tanya, \
                patch.object(self.root, "destroy") as hancurkan:
            self.app.tutup()
            tanya.assert_not_called()
            hancurkan.assert_called_once()

    def test_ebook_memakai_layanan_yang_sama(self):
        self.daftar()
        self.app.kode.set("E001")
        self.app.judul.set("Dasar Python")
        self.app.jenis.set("ebook")
        self.app.tambah_buku()
        self.app.anggota_dipilih.set("M001")
        self.app.buku_dipilih.set("E001")
        self.app.tanggal.set("2026-11-03")
        self.app.pinjam()
        self.assertEqual(self.app.tabel_pinjam.item("P001", "values")[4], "2026-11-10")

    def test_main_menolak_file_rusak_tanpa_menimpa(self):
        data = Path(self.folder.name) / "data/perpustakaan.json"
        data.parent.mkdir()
        data.write_text("{rusak", encoding="utf-8")
        with patch.object(gui, "__file__", str(Path(self.folder.name) / "gui.py")), \
                patch.object(gui.tk, "Tk", return_value=self.root), \
                patch.object(self.root, "destroy") as hancurkan, \
                patch.object(gui, "AplikasiPerpustakaan") as aplikasi:
            self.assertEqual(gui.main(), 1)
            hancurkan.assert_called_once()
            aplikasi.assert_not_called()
        self.assertEqual(data.read_text(encoding="utf-8"), "{rusak")

    def test_alur_buku_cetak_dan_ebook_lengkap(self):
        self.pinjam()
        self.app.tabel_pinjam.selection_set("P001")
        self.app.tanggal.set("2026-11-02")
        self.app.kembalikan()
        self.app.kode.set("E001")
        self.app.judul.set("Dasar Python")
        self.app.jenis.set("ebook")
        self.app.tambah_buku()
        self.app.anggota_dipilih.set("M001")
        self.app.buku_dipilih.set("E001")
        self.app.tanggal.set("2026-11-03")
        self.app.pinjam()
        self.app.simpan()
        baru = Perpustakaan(PenyimpananJSON(self.path))
        baru.muat()
        riwayat = baru.daftar_peminjaman()
        self.assertEqual([(p.id_pinjam, p.aktif) for p in riwayat],
                         [("P001", False), ("P002", True)])
        self.assertEqual(riwayat[1].tanggal_jatuh_tempo, date(2026, 11, 10))
        self.assertIs(riwayat[1].anggota, baru.daftar_anggota()[0])
        self.assertTrue(baru.tersedia("B001"))
        self.assertFalse(baru.tersedia("E001"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
